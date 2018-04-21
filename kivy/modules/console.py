# coding=utf-8
"""
Console
=======

.. versionadded:: 1.9.1

Reboot of the old inspector, designed to be modular and keep concerns
separated. It also has an addons architecture that allow you to add a button,
panel, or more in the Console itself.

.. warning::

    This module works, but might fail in some cases. Please contribute!

Usage
-----

For normal module usage, please see the :mod:`~kivy.modules` documentation::

    python main.py -m console

Mouse navigation
----------------

When the "Select" button is activated, you can:

- tap once on a widget to select it without leaving inspect mode
- double tap on a widget to select and leave inspect mode (then you can
  manipulate the widget again)

Keyboard navigation
-------------------

- "Ctrl + e": toggle console
- "Escape": cancel widget lookup, then hide inspector view
- "Up": select the parent widget
- "Down": select the first child of the currently selected widget
- "Left": select the previous sibling
- "Right": select the next sibling

Additional information
----------------------

Some properties can be edited live. However, due to the delayed usage of
some properties, it might crash if you don't handle the required cases.

Addons
------

Addons must be added to `Console.addons` before the first Clock tick of the
application, or before :attr:`create_console` is called. You currently cannot
add addons on the fly. Addons are quite cheap until the Console is activated.
Panels are even cheaper as nothing is done until the user selects them.

We provide multiple addons activated by default:

- ConsoleAddonFps: display the FPS at the top-right
- ConsoleAddonSelect: activate the selection mode
- ConsoleAddonBreadcrumb: display the hierarchy of the current widget at the
  bottom
- ConsoleAddonWidgetTree: panel to display the widget tree of the application
- ConsoleAddonWidgetPanel: panel to display the properties of the selected
  widget

If you need to add custom widgets in the Console, please use either
:class:`ConsoleButton`, :class:`ConsoleToggleButton` or :class:`ConsoleLabel`.

An addon must inherit from the :class:`ConsoleAddon` class.

For example, here is a simple addon for displaying the FPS at the top/right
of the Console::

    from kivy.modules.console import Console, ConsoleAddon

    class ConsoleAddonFps(ConsoleAddon):
        def init(self):
            self.lbl = ConsoleLabel(text="0 Fps")
            self.console.add_toolbar_widget(self.lbl, right=True)

        def activate(self):
            self.event = Clock.schedule_interval(self.update_fps, 1 / 2.)

        def deactivated(self):
            self.event.cancel()

        def update_fps(self, *args):
            fps = Clock.get_fps()
            self.lbl.text = "{} Fps".format(int(fps))

    Console.register_addon(ConsoleAddonFps)


You can create addons that add panels. Panel activation/deactivation is not
tied to the addon activation/deactivation, but in some cases, you can use the
same callback for deactivating the addon and the panel. Here is a simple
"About" panel addon::

    from kivy.modules.console import Console, ConsoleAddon, ConsoleLabel

    class ConsoleAddonAbout(ConsoleAddon):
        def init(self):
            self.console.add_panel("About", self.panel_activate,
                                   self.panel_deactivate)

        def panel_activate(self):
            self.console.bind(widget=self.update_content)
            self.update_content()

        def panel_deactivate(self):
            self.console.unbind(widget=self.update_content)

        def deactivate(self):
            self.panel_deactivate()

        def update_content(self, *args):
            widget = self.console.widget
            if not widget:
                return
            text = "Selected widget is: {!r}".format(widget)
            lbl = ConsoleLabel(text=text)
            self.console.set_content(lbl)

    Console.register_addon(ConsoleAddonAbout)

"""

__all__ = ("start", "stop", "create_console", "Console", "ConsoleAddon",
           "ConsoleButton", "ConsoleToggleButton", "ConsoleLabel")

import kivy
kivy.require('1.9.0')

import weakref
from functools import partial
from itertools import chain
from kivy.logger import Logger
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.treeview import TreeViewNode, TreeView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix
from kivy.graphics.context_instructions import Transform
from kivy.graphics.transformation import Matrix
from kivy.properties import (ObjectProperty, BooleanProperty, ListProperty,
                             NumericProperty, StringProperty, OptionProperty,
                             ReferenceListProperty, AliasProperty,
                             VariableListProperty)
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.lang import Builder

Builder.load_string("""
<Console>:
    size_hint: (1, None) if self.mode == "docked" else (None, None)
    height: dp(250)

    canvas:
        Color:
            rgb: .185, .18, .18
        Rectangle:
            size: self.size
        Color:
            rgb: .3, .3, .3
        Rectangle:
            pos: 0, self.height - dp(48)
            size: self.width, dp(48)

    GridLayout:
        cols: 1
        id: layout

        GridLayout:
            id: toolbar
            rows: 1
            height: "48dp"
            size_hint_y: None
            padding: "4dp"
            spacing: "4dp"


        RelativeLayout:
            id: content


<ConsoleAddonSeparator>:
    size_hint_x: None
    width: "10dp"

<ConsoleButton,ConsoleToggleButton,ConsoleLabel>:
    size_hint_x: None
    width: self.texture_size[0] + dp(20)


<ConsoleAddonBreadcrumbView>:
    size_hint_y: None
    height: "48dp"
    canvas:
        Color:
            rgb: .3, .3, .3
        Rectangle:
            size: self.size
    ScrollView:
        id: sv
        do_scroll_y: False
        GridLayout:
            id: stack
            rows: 1
            size_hint_x: None
            width: self.minimum_width
            padding: "4dp"
            spacing: "4dp"

<TreeViewProperty>:
    height: max(dp(48), max(lkey.texture_size[1], ltext.texture_size[1]))
    Label:
        id: lkey
        text: root.key
        text_size: (self.width, None)
        width: 150
        size_hint_x: None
    Label:
        id: ltext
        text: [repr(getattr(root.widget, root.key, '')), root.refresh][0]\
                if root.widget else ''
        text_size: (self.width, None)

<ConsoleAddonWidgetTreeView>:
    ScrollView:
        scroll_type: ['bars', 'content']
        bar_width: '10dp'

        ConsoleAddonWidgetTreeImpl:
            id: widgettree
            hide_root: True
            size_hint: None, None
            height: self.minimum_height
            width: max(self.parent.width, self.minimum_width)
            selected_widget: root.widget
            on_select_widget: root.console.highlight_widget(args[1])

<-TreeViewWidget>:
    height: self.texture_size[1] + sp(4)
    size_hint_x: None
    width: self.texture_size[0] + sp(4)

    canvas.before:
        Color:
            rgba: self.color_selected if self.is_selected else (0, 0, 0, 0)
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 1, 1, 1, int(not self.is_leaf)
        Rectangle:
            source:
                ('atlas://data/images/defaulttheme/tree_%s' %
                ('opened' if self.is_open else 'closed'))
            size: 16, 16
            pos: self.x - 20, self.center_y - 8

    canvas:
        Color:
            rgba:
                (self.disabled_color if self.disabled else
                (self.color if not self.markup else (1, 1, 1, 1)))
        Rectangle:
            texture: self.texture
            size: self.texture_size
            pos:
                (int(self.center_x - self.texture_size[0] / 2.),
                int(self.center_y - self.texture_size[1] / 2.))

""")


def ignore_exception(f):
    def f2(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            pass

    return f2


class TreeViewProperty(BoxLayout, TreeViewNode):
    key = ObjectProperty(None, allownone=True)
    refresh = BooleanProperty(False)
    widget_ref = ObjectProperty(None, allownone=True)

    def _get_widget(self):
        wr = self.widget_ref
        if wr is None:
            return None
        wr = wr()
        if wr is None:
            self.widget_ref = None
            return None
        return wr

    widget = AliasProperty(_get_widget, None, bind=('widget_ref', ))


class ConsoleButton(Button):
    """Button specialized for the Console"""
    pass


class ConsoleToggleButton(ToggleButton):
    """ToggleButton specialized for the Console"""
    pass


class ConsoleLabel(Label):
    """LabelButton specialized for the Console"""
    pass


class ConsoleAddonSeparator(Widget):
    pass


class ConsoleAddon(object):
    """Base class for implementing addons"""

    #: Console instance
    console = None

    def __init__(self, console):
        super(ConsoleAddon, self).__init__()
        self.console = console
        self.init()

    def init(self):
        """Method called when the addon is instantiated by the Console
        """
        pass

    def activate(self):
        """Method called when the addon is activated by the console
        (when the console is displayed)"""
        pass

    def deactivate(self):
        """Method called when the addon is deactivated by the console
        (when the console is hidden)
        """
        pass


class ConsoleAddonMode(ConsoleAddon):
    def init(self):
        btn = ConsoleToggleButton(text=u"Docked")
        self.console.add_toolbar_widget(btn)


class ConsoleAddonSelect(ConsoleAddon):
    def init(self):
        self.btn = ConsoleToggleButton(text=u"Select")
        self.btn.bind(state=self.on_button_state)
        self.console.add_toolbar_widget(self.btn)
        self.console.bind(inspect_enabled=self.on_inspect_enabled)

    def on_inspect_enabled(self, instance, value):
        self.btn.state = "down" if value else "normal"

    def on_button_state(self, instance, value):
        self.console.inspect_enabled = (value == "down")


class ConsoleAddonFps(ConsoleAddon):

    _update_ev = None

    def init(self):
        self.lbl = ConsoleLabel(text="0 Fps")
        self.console.add_toolbar_widget(self.lbl, right=True)

    def activate(self):
        ev = self._update_ev
        if ev is None:
            self._update_ev = Clock.schedule_interval(self.update_fps, 1 / 2.)
        else:
            ev()

    def deactivated(self):
        if self._update_ev is not None:
            self._update_ev.cancel()

    def update_fps(self, *args):
        fps = Clock.get_fps()
        self.lbl.text = "{} Fps".format(int(fps))


class ConsoleAddonBreadcrumbView(RelativeLayout):
    widget = ObjectProperty(None, allownone=True)
    parents = []

    def on_widget(self, instance, value):
        stack = self.ids.stack

        # determine if we can just highlight the current one
        # or if we need to rebuild the breadcrumb
        prefs = [btn.widget_ref() for btn in self.parents]
        if value in prefs:
            # ok, so just toggle this one instead.
            index = prefs.index(value)
            for btn in self.parents:
                btn.state = "normal"
            self.parents[index].state = "down"
            return

        # we need to rebuild the breadcrumb.
        stack.clear_widgets()
        if not value:
            return
        widget = value
        parents = []
        while True:
            btn = ConsoleButton(text=widget.__class__.__name__)
            btn.widget_ref = weakref.ref(widget)
            btn.bind(on_release=self.highlight_widget)
            parents.append(btn)
            if widget == widget.parent:
                break
            widget = widget.parent
        for btn in reversed(parents):
            stack.add_widget(btn)
        self.ids.sv.scroll_x = 1
        self.parents = parents
        btn.state = "down"

    def highlight_widget(self, instance):
        self.console.widget = instance.widget_ref()


class ConsoleAddonBreadcrumb(ConsoleAddon):
    def init(self):
        self.view = ConsoleAddonBreadcrumbView()
        self.view.console = self.console
        self.console.ids.layout.add_widget(self.view)

    def activate(self):
        self.console.bind(widget=self.update_content)
        self.update_content()

    def deactivate(self):
        self.console.unbind(widget=self.update_content)

    def update_content(self, *args):
        self.view.widget = self.console.widget


class ConsoleAddonWidgetPanel(ConsoleAddon):
    def init(self):
        self.console.add_panel("Properties", self.panel_activate,
                               self.deactivate)

    def panel_activate(self):
        self.console.bind(widget=self.update_content)
        self.update_content()

    def deactivate(self):
        self.console.unbind(widget=self.update_content)

    def update_content(self, *args):
        widget = self.console.widget
        if not widget:
            return

        from kivy.uix.scrollview import ScrollView
        self.root = root = BoxLayout()
        self.sv = sv = ScrollView(scroll_type=["bars", "content"],
                                  bar_width='10dp')
        treeview = TreeView(hide_root=True, size_hint_y=None)
        treeview.bind(minimum_height=treeview.setter("height"))
        keys = list(widget.properties().keys())
        keys.sort()
        node = None
        wk_widget = weakref.ref(widget)
        for key in keys:
            node = TreeViewProperty(key=key, widget_ref=wk_widget)
            node.bind(is_selected=self.show_property)
            try:
                widget.bind(**{
                    key: partial(self.update_node_content, weakref.ref(node))
                })
            except:
                pass
            treeview.add_node(node)

        root.add_widget(sv)
        sv.add_widget(treeview)
        self.console.set_content(root)

    def show_property(self, instance, value, key=None, index=-1, *l):
        # normal call: (tree node, focus, )
        # nested call: (widget, prop value, prop key, index in dict/list)
        if value is False:
            return

        console = self.console
        content = None
        if key is None:
            # normal call
            nested = False
            widget = instance.widget
            key = instance.key
            prop = widget.property(key)
            value = getattr(widget, key)
        else:
            # nested call, we might edit subvalue
            nested = True
            widget = instance
            prop = None

        dtype = None

        if isinstance(prop, AliasProperty) or nested:
            # trying to resolve type dynamically
            if type(value) in (str, str):
                dtype = 'string'
            elif type(value) in (int, float):
                dtype = 'numeric'
            elif type(value) in (tuple, list):
                dtype = 'list'

        if isinstance(prop, NumericProperty) or dtype == 'numeric':
            content = TextInput(text=str(value) or '', multiline=False)
            content.bind(
                text=partial(self.save_property_numeric, widget, key, index))

        elif isinstance(prop, StringProperty) or dtype == 'string':
            content = TextInput(text=value or '', multiline=True)
            content.bind(
                text=partial(self.save_property_text, widget, key, index))

        elif (isinstance(prop, ListProperty) or
              isinstance(prop, ReferenceListProperty) or
              isinstance(prop, VariableListProperty) or dtype == 'list'):
            content = GridLayout(cols=1, size_hint_y=None)
            content.bind(minimum_height=content.setter('height'))
            for i, item in enumerate(value):
                button = Button(text=repr(item), size_hint_y=None, height=44)
                if isinstance(item, Widget):
                    button.bind(on_release=partial(console.highlight_widget,
                                                   item, False))
                else:
                    button.bind(on_release=partial(self.show_property, widget,
                                                   item, key, i))
                content.add_widget(button)

        elif isinstance(prop, OptionProperty):
            content = GridLayout(cols=1, size_hint_y=None)
            content.bind(minimum_height=content.setter('height'))
            for option in prop.options:
                button = ToggleButton(
                    text=option,
                    state='down' if option == value else 'normal',
                    group=repr(content.uid),
                    size_hint_y=None,
                    height=44)
                button.bind(
                    on_press=partial(self.save_property_option, widget, key))
                content.add_widget(button)

        elif isinstance(prop, ObjectProperty):
            if isinstance(value, Widget):
                content = Button(text=repr(value))
                content.bind(
                    on_release=partial(console.highlight_widget, value))
            elif isinstance(value, Texture):
                content = Image(texture=value)
            else:
                content = Label(text=repr(value))

        elif isinstance(prop, BooleanProperty):
            state = 'down' if value else 'normal'
            content = ToggleButton(text=key, state=state)
            content.bind(on_release=partial(self.save_property_boolean, widget,
                                            key, index))

        self.root.clear_widgets()
        self.root.add_widget(self.sv)
        if content:
            self.root.add_widget(content)

    @ignore_exception
    def save_property_numeric(self, widget, key, index, instance, value):
        if index >= 0:
            getattr(widget, key)[index] = float(instance.text)
        else:
            setattr(widget, key, float(instance.text))

    @ignore_exception
    def save_property_text(self, widget, key, index, instance, value):
        if index >= 0:
            getattr(widget, key)[index] = instance.text
        else:
            setattr(widget, key, instance.text)

    @ignore_exception
    def save_property_boolean(self, widget, key, index, instance, ):
        value = instance.state == 'down'
        if index >= 0:
            getattr(widget, key)[index] = value
        else:
            setattr(widget, key, value)

    @ignore_exception
    def save_property_option(self, widget, key, instance, *l):
        setattr(widget, key, instance.text)


class TreeViewWidget(Label, TreeViewNode):
    widget = ObjectProperty(None)


class ConsoleAddonWidgetTreeImpl(TreeView):
    selected_widget = ObjectProperty(None, allownone=True)

    __events__ = ('on_select_widget', )

    def __init__(self, **kwargs):
        super(ConsoleAddonWidgetTreeImpl, self).__init__(**kwargs)
        self.update_scroll = Clock.create_trigger(self._update_scroll)

    def find_node_by_widget(self, widget):
        for node in self.iterate_all_nodes():
            if not node.parent_node:
                continue
            try:
                if node.widget == widget:
                    return node
            except ReferenceError:
                pass
        return None

    def update_selected_widget(self, widget):
        if widget:
            node = self.find_node_by_widget(widget)
            if node:
                self.select_node(node, False)
                while node and isinstance(node, TreeViewWidget):
                    if not node.is_open:
                        self.toggle_node(node)
                    node = node.parent_node

    def on_selected_widget(self, inst, widget):
        if widget:
            self.update_selected_widget(widget)
            self.update_scroll()

    def select_node(self, node, select_widget=True):
        super(ConsoleAddonWidgetTreeImpl, self).select_node(node)
        if select_widget:
            try:
                self.dispatch("on_select_widget", node.widget.__self__)
            except ReferenceError:
                pass

    def on_select_widget(self, widget):
        pass

    def _update_scroll(self, *args):
        node = self._selected_node
        if not node:
            return

        self.parent.scroll_to(node)


class ConsoleAddonWidgetTreeView(RelativeLayout):
    widget = ObjectProperty(None, allownone=True)
    _window_node = None

    def _update_widget_tree_node(self, node, widget, is_open=False):
        tree = self.ids.widgettree
        update_nodes = []
        nodes = {}
        for cnode in node.nodes[:]:
            try:
                nodes[cnode.widget] = cnode
            except ReferenceError:
                # widget no longer exists, just remove it
                pass
            tree.remove_node(cnode)
        for child in widget.children:
            if isinstance(child, Console):
                continue
            if child in nodes:
                cnode = tree.add_node(nodes[child], node)
            else:
                cnode = tree.add_node(
                    TreeViewWidget(text=child.__class__.__name__,
                                   widget=child.proxy_ref,
                                   is_open=is_open), node)
            update_nodes.append((cnode, child))
        return update_nodes

    def update_widget_tree(self, *args):
        win = self.console.win
        if not self._window_node:
            self._window_node = self.ids.widgettree.add_node(
                TreeViewWidget(text="Window",
                               widget=win,
                               is_open=True))

        nodes = self._update_widget_tree_node(self._window_node, win,
                                              is_open=True)
        while nodes:
            ntmp = nodes[:]
            nodes = []
            for node in ntmp:
                nodes += self._update_widget_tree_node(*node)

        self.ids.widgettree.update_selected_widget(self.widget)


class ConsoleAddonWidgetTree(ConsoleAddon):
    def init(self):
        self.content = None
        self.console.add_panel("Tree", self.panel_activate, self.deactivate,
                               self.panel_refresh)

    def panel_activate(self):
        self.console.bind(widget=self.update_content)
        self.update_content()

    def deactivate(self):
        if self.content:
            self.content.widget = None
            self.content.console = None
        self.console.unbind(widget=self.update_content)

    def update_content(self, *args):
        widget = self.console.widget
        if not self.content:
            self.content = ConsoleAddonWidgetTreeView()
        self.content.console = self.console
        self.content.widget = widget
        self.content.update_widget_tree()
        self.console.set_content(self.content)

    def panel_refresh(self):
        if self.content:
            self.content.update_widget_tree()


class Console(RelativeLayout):
    """Console interface

    This widget is created by create_console(), when the module is loaded.
    During that time, you can add addons on the console to extend the
    functionalities, or add your own application stats / debugging module.
    """

    #: Array of addons that will be created at Console creation
    addons = [  # ConsoleAddonMode,
        ConsoleAddonSelect, ConsoleAddonFps, ConsoleAddonWidgetPanel,
        ConsoleAddonWidgetTree, ConsoleAddonBreadcrumb]

    #: Display mode of the Console, either docked at the bottom, or as a
    #: floating window.
    mode = OptionProperty("docked", options=["docked", "floated"])

    #: Current widget being selected
    widget = ObjectProperty(None, allownone=True)

    #: Indicate if the inspector inspection is enabled. If yes, the next
    #: touch down will select a the widget under the touch
    inspect_enabled = BooleanProperty(False)

    #: True if the Console is activated (showed)
    activated = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.win = kwargs.pop('win', None)
        super(Console, self).__init__(**kwargs)
        self.avoid_bring_to_top = False
        with self.canvas.before:
            self.gcolor = Color(1, 0, 0, .25)
            PushMatrix()
            self.gtransform = Transform(Matrix())
            self.grect = Rectangle(size=(0, 0))
            PopMatrix()
        Clock.schedule_interval(self.update_widget_graphics, 0)

        # instantiate all addons
        self._toolbar = {"left": [], "panels": [], "right": []}
        self._addons = []
        self._panel = None
        for addon in self.addons:
            instance = addon(self)
            self._addons.append(instance)
        self._init_toolbar()
        # select the first panel
        self._panel = self._toolbar["panels"][0]
        self._panel.state = "down"
        self._panel.cb_activate()

    def _init_toolbar(self):
        toolbar = self.ids.toolbar
        for key in ("left", "panels", "right"):
            if key == "right":
                toolbar.add_widget(Widget())
            for el in self._toolbar[key]:
                toolbar.add_widget(el)
            if key != "right":
                toolbar.add_widget(ConsoleAddonSeparator())

    @classmethod
    def register_addon(cls, addon):
        cls.addons.append(addon)

    def add_toolbar_widget(self, widget, right=False):
        """Add a widget in the top left toolbar of the Console.
        Use `right=True` if you wanna add the widget at the right instead.
        """
        key = "right" if right else "left"
        self._toolbar[key].append(widget)

    def remove_toolbar_widget(self, widget):
        """Remove a widget from the toolbar
        """
        self.ids.toolbar.remove_widget(widget)

    def add_panel(self, name, cb_activate, cb_deactivate, cb_refresh=None):
        """Add a new panel in the Console.

        - `cb_activate` is a callable that will be called when the panel is
          activated by the user.

        - `cb_deactivate` is a callable that will be called when the panel is
          deactivated or when the console will hide.

        - `cb_refresh` is an optional callable that is called if the user
          click again on the button for display the panel

        When activated, it's up to the panel to display a content in the
        Console by using :meth:`set_content`.
        """
        btn = ConsoleToggleButton(text=name)
        btn.cb_activate = cb_activate
        btn.cb_deactivate = cb_deactivate
        btn.cb_refresh = cb_refresh
        btn.bind(on_press=self._activate_panel)
        self._toolbar["panels"].append(btn)

    def _activate_panel(self, instance):
        if self._panel != instance:
            self._panel.cb_deactivate()
            self._panel.state = "normal"
            self.ids.content.clear_widgets()
            self._panel = instance
            self._panel.cb_activate()
            self._panel.state = "down"
        else:
            self._panel.state = "down"
            if self._panel.cb_refresh:
                self._panel.cb_refresh()

    def set_content(self, content):
        """Replace the Console content with a new one.
        """
        self.ids.content.clear_widgets()
        self.ids.content.add_widget(content)

    def on_touch_down(self, touch):
        ret = super(Console, self).on_touch_down(touch)
        if (('button' not in touch.profile or touch.button == 'left') and
                not ret and self.inspect_enabled):
            self.highlight_at(*touch.pos)
            if touch.is_double_tap:
                self.inspect_enabled = False
            ret = True
        else:
            ret = self.collide_point(*touch.pos)
        return ret

    def on_touch_move(self, touch):
        ret = super(Console, self).on_touch_move(touch)
        if not ret and self.inspect_enabled:
            self.highlight_at(*touch.pos)
            ret = True
        return ret

    def on_touch_up(self, touch):
        ret = super(Console, self).on_touch_up(touch)
        if not ret and self.inspect_enabled:
            ret = True
        return ret

    def on_window_children(self, win, children):
        if self.avoid_bring_to_top or not self.activated:
            return
        self.avoid_bring_to_top = True
        win.remove_widget(self)
        win.add_widget(self)
        self.avoid_bring_to_top = False

    def highlight_at(self, x, y):
        """Select a widget from a x/y window coordinate.
        This is mostly used internally when Select mode is activated
        """
        widget = None
        # reverse the loop - look at children on top first and
        # modalviews before others
        win_children = self.win.children
        children = chain((c for c in reversed(win_children)
                          if isinstance(c, ModalView)),
                         (c for c in reversed(win_children)
                          if not isinstance(c, ModalView)))
        for child in children:
            if child is self:
                continue
            widget = self.pick(child, x, y)
            if widget:
                break
        self.highlight_widget(widget)

    def highlight_widget(self, widget, *largs):
        # no widget to highlight, reduce rectangle to 0, 0
        self.widget = widget
        if not widget:
            self.grect.size = 0, 0

    def update_widget_graphics(self, *l):
        if not self.activated:
            return
        if self.widget is None:
            self.grect.size = 0, 0
            return
        self.grect.size = self.widget.size
        matrix = self.widget.get_window_matrix()
        if self.gtransform.matrix.get() != matrix.get():
            self.gtransform.matrix = matrix

    def pick(self, widget, x, y):
        """Pick a widget at x/y, given a root `widget`
        """
        ret = None
        # try to filter widgets that are not visible (invalid inspect target)
        if (hasattr(widget, 'visible') and not widget.visible):
            return ret
        if widget.collide_point(x, y):
            ret = widget
            x2, y2 = widget.to_local(x, y)
            # reverse the loop - look at children on top first
            for child in reversed(widget.children):
                ret = self.pick(child, x2, y2) or ret
        return ret

    def on_activated(self, instance, activated):
        if activated:
            self._activate_console()
        else:
            self._deactivate_console()

    def _activate_console(self):
        if self not in self.win.children:
            self.win.add_widget(self)
        self.y = 0
        for addon in self._addons:
            addon.activate()
        Logger.info('Console: console activated')

    def _deactivate_console(self):
        for addon in self._addons:
            addon.deactivate()
        self.grect.size = 0, 0
        self.y = -self.height
        self.widget = None
        self.inspect_enabled = False
        # self.win.remove_widget(self)
        self._window_node = None
        Logger.info('Console: console deactivated')

    def keyboard_shortcut(self, win, scancode, *largs):
        modifiers = largs[-1]
        if scancode == 101 and modifiers == ['ctrl']:
            self.activated = not self.activated
            if self.activated:
                self.inspect_enabled = True
            return True

        elif scancode == 27:
            if self.inspect_enabled:
                self.inspect_enabled = False
                return True
            if self.activated:
                self.activated = False
                return True

        if not self.activated or not self.widget:
            return

        if scancode == 273:  # top
            self.widget = self.widget.parent

        elif scancode == 274:  # down
            filtered_children = [c for c in self.widget.children
                                 if not isinstance(c, Console)]
            if filtered_children:
                self.widget = filtered_children[0]

        elif scancode == 276:  # left
            parent = self.widget.parent
            filtered_children = [c for c in parent.children
                                 if not isinstance(c, Console)]
            index = filtered_children.index(self.widget)
            index = max(0, index - 1)
            self.widget = filtered_children[index]

        elif scancode == 275:  # right
            parent = self.widget.parent
            filtered_children = [c for c in parent.children
                                 if not isinstance(c, Console)]
            index = filtered_children.index(self.widget)
            index = min(len(filtered_children) - 1, index + 1)
            self.widget = filtered_children[index]


def create_console(win, ctx, *l):
    ctx.console = Console(win=win)
    win.bind(children=ctx.console.on_window_children,
             on_keyboard=ctx.console.keyboard_shortcut)


def start(win, ctx):
    """Create an Console instance attached to the *ctx* and bound to the
    Window's :meth:`~kivy.core.window.WindowBase.on_keyboard` event for
    capturing the keyboard shortcut.

        :Parameters:
            `win`: A :class:`Window <kivy.core.window.WindowBase>`
                The application Window to bind to.
            `ctx`: A :class:`~kivy.uix.widget.Widget` or subclass
                The Widget to be inspected.

    """
    Clock.schedule_once(partial(create_console, win, ctx))


def stop(win, ctx):
    """Stop and unload any active Inspectors for the given *ctx*."""
    if hasattr(ctx, "console"):
        win.unbind(children=ctx.console.on_window_children,
                   on_keyboard=ctx.console.keyboard_shortcut)
        win.remove_widget(ctx.console)
        del ctx.console
