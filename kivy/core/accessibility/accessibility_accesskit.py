from collections import defaultdict

import kivy
from accesskit import Node, Tree, Role, TreeUpdate, Action, unix, Rect, Toggled
from kivy.uix.behaviors.accessibility import AccessibleBehavior
from sys import platform
from . import AccessibilityBase, Action as KivyAction, Role as KivyRole

class AccessKit(AccessibilityBase):
    def __init__(self, root_window):
        super().__init__()
        self.node_classes = []
        self.adapter = None
        self.root_window = root_window
        self.root_window_size = None
        root_window.bind(focus=lambda w, v: self._update_root_window_focus(v))
        root_window.bind(size=lambda w, v: self._update_root_window_size(v))
        self.action_request_callback = None
        self.initialized = False

    def _update_root_window_focus(self, is_focused):
        if self.adapter is None:
            return
        if platform == 'darwin':
            events = self.adapter.update_view_focus_state(is_focused)
            if events is not None:
                events.raise_events()
        elif 'linux' in platform or 'freebsd' in platform or 'openbsd' in platform:
            self.adapter.update_window_focus_state(is_focused)

    def _update_root_window_size(self, size):
        self.root_window_size = size

    def _build_tree_info(self):
        tree = Tree(self.root_window.uid)
        tree.toolkit_name = "Kivy"
        tree.toolkit_version = kivy.__version__
        return tree

    def _build_dummy_tree(self):
        # If there is no assistive technology running, then this might never be called.
        # We don't really know when the first accessibility tree will be requested: if it's early in the app initialization then we might not have everything ready.
        # It's OK to first push an empty tree update and replace it later.
        root = Node(Role.WINDOW)
        update = TreeUpdate(self.root_window.uid)
        update.nodes.append((self.root_window.uid, root))
        update.tree = self._build_tree_info()
        self.initialized = True
        return update

    def _on_action_request(self, request):
        # An assistive technology wants to perform an action on behalf of the user.
        if request.action == Action.FOCUS:
            action = KivyAction.FOCUS
        elif request.action == Action.DEFAULT:
            action = KivyAction.DEFAULT
        else:
            return
        if self.action_request_callback:
            # If we are properly initialized, forward the action to the accessibility manager.
            self.action_request_callback(request.target, action)

    @staticmethod
    def _handle_deactivation(*args, **kwargs): ...

    def install(self, window_info, width, height):
        self.root_window_size = (width, height)
        if platform == 'darwin':
            # The following function will need to be called. Since it's SDL2 specific, should it really belong here?
            # macos.add_focus_forwarder_to_window_class("SDLWindow")
            self.adapter = macos.SubclassingAdapter(window_info.window, self._build_dummy_tree, self._on_action_request)
        elif 'linux' in platform or 'freebsd' in platform or 'openbsd' in platform:
            self.adapter = unix.Adapter(self._build_dummy_tree, self._on_action_request, self._handle_deactivation)
        elif platform in ('win32', 'cygwin'):
            self.adapter = windows.SubclassingAdapter(window_info.window, self._build_dummy_tree, self._on_action_request)
        # Assume the window has the focus at this time, even though it's probably not true.
        self._update_root_window_focus(True)

    def _build_node(self, accessible):
        node = Node(to_accesskit_role(accessible.accessible_role))
        (x, y) = accessible.accessible_pos
        # On Windows, Y coordinates seem to be reversed, this will be annoying once the window is resized as we'll need to recompute every widget's bounds.
        # Is there a more direct way?
        (width, height) = accessible.accessible_size
        bounds = Rect(x, y, x + width, y + height)
        node.set_bounds(bounds)
        
        if accessible.accessible_checked_state is not None:
            node.set_toggled(Toggled.TRUE if accessible.accessible_checked_state else Toggled.FALSE)
        if accessible.accessible_children:
            node.set_children(accessible.accessible_children)
        if accessible.accessible_name:
            node.set_label(accessible.accessible_name)
        if accessible.is_focusable:
            node.set_custom_actions([Action.FOCUS])
        elif accessible.is_clickable:
            node.set_default_action_verb(Action.CLICK)
        return node

    def _build_tree_update(self, root_window_changed=True):
        # If no widget has the focus, then we must put it on the root window.
        focus = (
            widget.focused_widget.uid
            if widget.focused_widget
            else self.root_window.uid
        )
        update = TreeUpdate(focus)
        update.tree = self._build_tree_info()
        if root_window_changed:
            node = Node(Role.WINDOW)
            node.set_label(self.root_window.title)
            update.tree.root = self.root_window.uid
            update.nodes = [(self.root_window.uid, node)]
            childs = defaultdict(set)
            nodes = {self.root_window.uid: node}
            for (id_, accessible) in widget.updated_widgets.items():
                if accessible.parent == self.root_window:
                    childs[self.root_window.uid].add(id_)
                    node = self._build_node(accessible)
                    update.nodes.append((id_, node))
                    nodes[id_] = node
                else:
                    ancestry = [accessible]
                    here = accessible
                    while here.parent is not here:
                        here = here.parent
                        ancestry.append(here)
                    if self.root_window != ancestry.pop():
                        raise RuntimeError("Not in the right window")
                    prev = ancestry.pop()
                    if prev.uid in nodes:
                        prev_node = nodes[prev.uid]
                    else:
                        prev_node = self._build_node(prev)
                        nodes[prev.uid] = prev_node
                    childs[self.root_window.uid].add(prev.uid)
                    if prev.uid not in childs[self.root_window.uid]:
                        update.nodes.append((prev.uid, prev_node))
                    while ancestry:
                        accessible = ancestry.pop()
                        if accessible.uid in nodes:
                            accessible_node = nodes[accessible.uid]
                        else:
                            accessible_node = self._build_node(accessible)
                            nodes[accessible.uid] = accessible_node
                        if accessible.uid not in childs[prev.uid]:
                            update.nodes.append((accessible.uid, accessible_node))
                            childs[prev.uid].add(accessible.uid)
                        (prev, prev_node) = (accessible, accessible_node)
            if self.node_classes:
                node.class_name = self.node_classes[0]
            for id_, node in nodes.items():
                if id_ in childs:
                    node.set_children(list(childs[id_]))
        else:
            for (id, accessible) in widget.updated_widgets.items():
                update.nodes.append((id, self._build_node(accessible)))
        return update

    def update(self, root_window_changed=False):
        if not self.adapter:
            return False
        if not self.initialized:
            self._build_dummy_tree()
        events = self.adapter.update_if_active(lambda: self._build_tree_update(root_window_changed))
        if events:
            events.raise_events()
        return True

def to_accesskit_role(role):
    if role == KivyRole.STATIC_TEXT:
        return Role.PARAGRAPH
    elif role == KivyRole.GENERIC_CONTAINER:
        return Role.GENERIC_CONTAINER
    elif role == KivyRole.CHECK_BOX:
        return Role.CHECK_BOX
    elif role == KivyRole.BUTTON:
        return Role.BUTTON
    return Role.UNKNOWN
