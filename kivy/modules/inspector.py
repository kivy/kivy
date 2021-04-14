'''
Inspector
=========

.. versionadded:: 1.0.9

.. warning::

    This module is highly experimental, use it with care.

The Inspector is a tool for finding a widget in the widget tree by clicking or
tapping on it.
Some keyboard shortcuts are activated:

    * "Ctrl + e": activate / deactivate the inspector view
    * "Escape": cancel widget lookup first, then hide the inspector view

Available inspector interactions:

    * tap once on a widget to select it without leaving inspect mode
    * double tap on a widget to select and leave inspect mode (then you can
      manipulate the widget again)

Some properties can be edited live. However, due to the delayed usage of
some properties, it might crash if you don't handle all the cases.

Usage
-----

For normal module usage, please see the :mod:`~kivy.modules` documentation.

The Inspector, however, can also be imported and used just like a normal
python module. This has the added advantage of being able to activate and
deactivate the module programmatically::

    from kivy.core.window import Window
    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.modules import inspector

    class Demo(App):
        def build(self):
            button = Button(text="Test")
            inspector.create_inspector(Window, button)
            return button

    Demo().run()

To remove the Inspector, you can do the following::

    inspector.stop(Window, button)

'''

__all__ = ('start', 'stop', 'create_inspector')

import weakref
from functools import partial
from itertools import chain

from kivy.animation import Animation
from kivy.logger import Logger
from kivy.graphics.transformation import Matrix
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.weakproxy import WeakProxy
from kivy.properties import (
    ObjectProperty, BooleanProperty, ListProperty,
    NumericProperty, StringProperty, OptionProperty,
    ReferenceListProperty, AliasProperty, VariableListProperty
)

Builder.load_string('''
<Inspector>:
    layout: layout
    widgettree: widgettree
    treeview: treeview
    content: content
    BoxLayout:
        orientation: 'vertical'
        id: layout
        size_hint_y: None
        height: 250
        padding: 5
        spacing: 5
        top: 0

        canvas:
            Color:
                rgb: .4, .4, .4
            Rectangle:
                pos: self.x, self.top
                size: self.width, 1
            Color:
                rgba: .185, .18, .18, .95
            Rectangle:
                pos: self.pos
                size: self.size

        # Top Bar
        BoxLayout:
            size_hint_y: None
            height: 50
            spacing: 5
            Button:
                text: 'Move to Top'
                on_release: root.toggle_position(args[0])
                size_hint_x: None
                width: 120

            ToggleButton:
                text: 'Inspect'
                on_state: root.inspect_enabled = args[1] == 'down'
                size_hint_x: None
                state: 'down' if root.inspect_enabled else 'normal'
                width: 80

            Button:
                text: 'Parent'
                on_release:
                    root.highlight_widget(root.widget.parent) if root.widget \
                            else None
                size_hint_x: None
                width: 80

            Button:
                text: '%r' % root.widget
                on_release: root.show_widget_info()

            Button:
                text: 'X'
                size_hint_x: None
                width: 50
                on_release: root.activated = False

        # Bottom Bar
        BoxLayout:
            ScrollView:
                scroll_type: ['bars', 'content']
                bar_width: 10
                size_hint_x: 0.0001

                WidgetTree:
                    id: widgettree
                    hide_root: True
                    size_hint: None, None
                    height: self.minimum_height
                    width: max(self.parent.width, self.minimum_width)
                    selected_widget: root.widget
                    on_select_widget: root.highlight_widget(args[1])

            Splitter:
                sizeable_from: 'left'
                min_size: self.parent.width / 2
                max_size: self.parent.width

                BoxLayout:
                    ScrollView:
                        scroll_type: ['bars', 'content']
                        bar_width: 10
                        TreeView:
                            id: treeview
                            size_hint_y: None
                            hide_root: True
                            height: self.minimum_height

                    Splitter:
                        sizeable_from: 'left'
                        keep_within_parent: True
                        rescale_with_parent: True
                        max_size: self.parent.width / 2
                        min_size: 0

                        ScrollView:
                            id: content

<TreeViewProperty>:
    height: max(lkey.texture_size[1], ltext.texture_size[1])
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
''')


class TreeViewProperty(Factory.BoxLayout, Factory.TreeViewNode):

    widget_ref = ObjectProperty(None, allownone=True)

    def _get_widget(self):
        wr = self.widget_ref
        if wr is None:
            return
        wr = wr()
        if wr is None:
            self.widget_ref = None
            return
        return wr
    widget = AliasProperty(_get_widget, None, bind=('widget_ref', ))

    key = ObjectProperty(None, allownone=True)

    inspector = ObjectProperty(None)

    refresh = BooleanProperty(False)


class TreeViewWidget(Factory.Label, Factory.TreeViewNode):
    widget = ObjectProperty(None)


class WidgetTree(Factory.TreeView):
    selected_widget = ObjectProperty(None, allownone=True)

    __events__ = ('on_select_widget',)

    def __init__(self, **kwargs):
        super(WidgetTree, self).__init__(**kwargs)
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
        return

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
        super(WidgetTree, self).select_node(node)
        if select_widget:
            try:
                self.dispatch('on_select_widget', node.widget.__self__)
            except ReferenceError:
                pass

    def on_select_widget(self, widget):
        pass

    def _update_scroll(self, *args):
        node = self._selected_node
        if not node:
            return

        self.parent.scroll_to(node)


class Inspector(Factory.FloatLayout):

    widget = ObjectProperty(None, allownone=True)

    layout = ObjectProperty(None)

    widgettree = ObjectProperty(None)

    treeview = ObjectProperty(None)

    inspect_enabled = BooleanProperty(False)

    activated = BooleanProperty(False)

    widget_info = BooleanProperty(False)

    content = ObjectProperty(None)

    at_bottom = BooleanProperty(True)

    _update_widget_tree_ev = None

    def __init__(self, **kwargs):
        self.win = kwargs.pop('win', None)
        super(Inspector, self).__init__(**kwargs)
        self.avoid_bring_to_top = False
        with self.canvas.before:
            self.gcolor = Factory.Color(1, 0, 0, .25)
            Factory.PushMatrix()
            self.gtransform = Factory.Transform(Matrix())
            self.grect = Factory.Rectangle(size=(0, 0))
            Factory.PopMatrix()
        Clock.schedule_interval(self.update_widget_graphics, 0)

    def on_touch_down(self, touch):
        ret = super(Inspector, self).on_touch_down(touch)
        if (('button' not in touch.profile or touch.button == 'left') and
                not ret and self.inspect_enabled):
            self.highlight_at(*touch.pos)
            if touch.is_double_tap:
                self.inspect_enabled = False
                self.show_widget_info()
            ret = True
        return ret

    def on_touch_move(self, touch):
        ret = super(Inspector, self).on_touch_move(touch)
        if not ret and self.inspect_enabled:
            self.highlight_at(*touch.pos)
            ret = True
        return ret

    def on_touch_up(self, touch):
        ret = super(Inspector, self).on_touch_up(touch)
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
        widget = None
        # reverse the loop - look at children on top first and
        # modalviews before others
        win_children = self.win.children
        children = chain(
            (c for c in win_children if isinstance(c, Factory.ModalView)),
            (
                c for c in reversed(win_children)
                if not isinstance(c, Factory.ModalView)
            )
        )
        for child in children:
            if child is self:
                continue
            widget = self.pick(child, x, y)
            if widget:
                break
        self.highlight_widget(widget)

    def highlight_widget(self, widget, info=True, *largs):
        # no widget to highlight, reduce rectangle to 0, 0
        self.widget = widget
        if not widget:
            self.grect.size = 0, 0
        if self.widget_info and info:
            self.show_widget_info()

    def update_widget_graphics(self, *largs):
        if not self.activated:
            return
        if self.widget is None:
            self.grect.size = 0, 0
            return
        self.grect.size = self.widget.size
        matrix = self.widget.get_window_matrix()
        if self.gtransform.matrix.get() != matrix.get():
            self.gtransform.matrix = matrix

    def toggle_position(self, button):
        to_bottom = button.text == 'Move to Bottom'

        if to_bottom:
            button.text = 'Move to Top'
            if self.widget_info:
                Animation(top=250, t='out_quad', d=.3).start(self.layout)
            else:
                Animation(top=60, t='out_quad', d=.3).start(self.layout)

            bottom_bar = self.layout.children[1]
            self.layout.remove_widget(bottom_bar)
            self.layout.add_widget(bottom_bar)
        else:
            button.text = 'Move to Bottom'
            if self.widget_info:
                Animation(top=self.height, t='out_quad', d=.3).start(
                    self.layout)
            else:
                Animation(y=self.height - 60, t='out_quad', d=.3).start(
                    self.layout)

            bottom_bar = self.layout.children[1]
            self.layout.remove_widget(bottom_bar)
            self.layout.add_widget(bottom_bar)
        self.at_bottom = to_bottom

    def pick(self, widget, x, y):
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
        if not activated:
            self.grect.size = 0, 0
            if self.at_bottom:
                anim = Animation(top=0, t='out_quad', d=.3)
            else:
                anim = Animation(y=self.height, t='out_quad', d=.3)
            anim.bind(on_complete=self.animation_close)
            anim.start(self.layout)
            self.widget = None
            self.widget_info = False
        else:
            self.win.add_widget(self)
            Logger.info('Inspector: inspector activated')
            if self.at_bottom:
                Animation(top=60, t='out_quad', d=.3).start(self.layout)
            else:
                Animation(y=self.height - 60, t='out_quad', d=.3).start(
                    self.layout)
            ev = self._update_widget_tree_ev
            if ev is None:
                ev = self._update_widget_tree_ev = Clock.schedule_interval(
                    self.update_widget_tree, 1)
            else:
                ev()
            self.update_widget_tree()

    def animation_close(self, instance, value):
        if not self.activated:
            self.inspect_enabled = False
            self.win.remove_widget(self)
            self.content.clear_widgets()
            treeview = self.treeview
            for node in list(treeview.iterate_all_nodes()):
                node.widget_ref = None
                treeview.remove_node(node)

            self._window_node = None
            if self._update_widget_tree_ev is not None:
                self._update_widget_tree_ev.cancel()

            widgettree = self.widgettree
            for node in list(widgettree.iterate_all_nodes()):
                widgettree.remove_node(node)
            Logger.info('Inspector: inspector deactivated')

    def show_widget_info(self):
        self.content.clear_widgets()
        widget = self.widget
        treeview = self.treeview
        for node in list(treeview.iterate_all_nodes())[:]:
            node.widget_ref = None
            treeview.remove_node(node)
        if not widget:
            if self.at_bottom:
                Animation(top=60, t='out_quad', d=.3).start(self.layout)
            else:
                Animation(y=self.height - 60, t='out_quad', d=.3).start(
                    self.layout)
            self.widget_info = False
            return
        self.widget_info = True
        if self.at_bottom:
            Animation(top=250, t='out_quad', d=.3).start(self.layout)
        else:
            Animation(top=self.height, t='out_quad', d=.3).start(self.layout)
        for node in list(treeview.iterate_all_nodes())[:]:
            treeview.remove_node(node)

        keys = list(widget.properties().keys())
        keys.sort()
        node = None
        if type(widget) is WeakProxy:
            wk_widget = widget.__ref__
        else:
            wk_widget = weakref.ref(widget)
        for key in keys:
            node = TreeViewProperty(key=key, widget_ref=wk_widget)
            node.bind(is_selected=self.show_property)
            try:
                widget.bind(**{key: partial(
                    self.update_node_content, weakref.ref(node))})
            except:
                pass
            treeview.add_node(node)

    def update_node_content(self, node, *largs):
        node = node()
        if node is None:
            return
        node.refresh = True
        node.refresh = False

    def keyboard_shortcut(self, win, scancode, *largs):
        modifiers = largs[-1]
        if scancode == 101 and set(modifiers) & {'ctrl'} and not set(
                modifiers) & {'shift', 'alt', 'meta'}:
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

    def show_property(self, instance, value, key=None, index=-1, *largs):
        # normal call: (tree node, focus, )
        # nested call: (widget, prop value, prop key, index in dict/list)
        if value is False:
            return

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
            content = Factory.TextInput(text=str(value) or '', multiline=False)
            content.bind(text=partial(
                self.save_property_numeric, widget, key, index))
        elif isinstance(prop, StringProperty) or dtype == 'string':
            content = Factory.TextInput(text=value or '', multiline=True)
            content.bind(text=partial(
                self.save_property_text, widget, key, index))
        elif (isinstance(prop, ListProperty) or
              isinstance(prop, ReferenceListProperty) or
              isinstance(prop, VariableListProperty) or
              dtype == 'list'):
            content = Factory.GridLayout(cols=1, size_hint_y=None)
            content.bind(minimum_height=content.setter('height'))
            for i, item in enumerate(value):
                button = Factory.Button(
                    text=repr(item),
                    size_hint_y=None,
                    height=44
                )
                if isinstance(item, Factory.Widget):
                    button.bind(on_release=partial(self.highlight_widget, item,
                                                   False))
                else:
                    button.bind(on_release=partial(self.show_property, widget,
                                                   item, key, i))
                content.add_widget(button)
        elif isinstance(prop, OptionProperty):
            content = Factory.GridLayout(cols=1, size_hint_y=None)
            content.bind(minimum_height=content.setter('height'))
            for option in prop.options:
                button = Factory.ToggleButton(
                    text=option,
                    state='down' if option == value else 'normal',
                    group=repr(content.uid), size_hint_y=None,
                    height=44)
                button.bind(on_press=partial(
                    self.save_property_option, widget, key))
                content.add_widget(button)
        elif isinstance(prop, ObjectProperty):
            if isinstance(value, Factory.Widget):
                content = Factory.Button(text=repr(value))
                content.bind(on_release=partial(self.highlight_widget, value))
            elif isinstance(value, Factory.Texture):
                content = Factory.Image(texture=value)
            else:
                content = Factory.Label(text=repr(value))

        elif isinstance(prop, BooleanProperty):
            state = 'down' if value else 'normal'
            content = Factory.ToggleButton(text=key, state=state)
            content.bind(on_release=partial(self.save_property_boolean, widget,
                                            key, index))

        self.content.clear_widgets()
        if content:
            self.content.add_widget(content)

    def save_property_numeric(self, widget, key, index, instance, value):
        try:
            if index >= 0:
                getattr(widget, key)[index] = float(instance.text)
            else:
                setattr(widget, key, float(instance.text))
        except:
            pass

    def save_property_text(self, widget, key, index, instance, value):
        try:
            if index >= 0:
                getattr(widget, key)[index] = instance.text
            else:
                setattr(widget, key, instance.text)
        except:
            pass

    def save_property_boolean(self, widget, key, index, instance, ):
        try:
            value = instance.state == 'down'
            if index >= 0:
                getattr(widget, key)[index] = value
            else:
                setattr(widget, key, value)
        except:
            pass

    def save_property_option(self, widget, key, instance, *largs):
        try:
            setattr(widget, key, instance.text)
        except:
            pass

    def _update_widget_tree_node(self, node, widget, is_open=False):
        tree = self.widgettree
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
            if child is self:
                continue
            if child in nodes:
                cnode = tree.add_node(nodes[child], node)
            else:
                cnode = tree.add_node(TreeViewWidget(
                    text=child.__class__.__name__, widget=child.proxy_ref,
                    is_open=is_open), node)
            update_nodes.append((cnode, child))
        return update_nodes

    def update_widget_tree(self, *args):
        if not hasattr(self, '_window_node') or not self._window_node:
            self._window_node = self.widgettree.add_node(
                TreeViewWidget(text='Window', widget=self.win, is_open=True))

        nodes = self._update_widget_tree_node(self._window_node, self.win,
                                              is_open=True)
        while nodes:
            ntmp = nodes[:]
            nodes = []
            for node in ntmp:
                nodes += self._update_widget_tree_node(*node)

        self.widgettree.update_selected_widget(self.widget)


def create_inspector(win, ctx, *largs):
    '''Create an Inspector instance attached to the *ctx* and bound to the
    Window's :meth:`~kivy.core.window.WindowBase.on_keyboard` event for
    capturing the keyboard shortcut.

        :Parameters:
            `win`: A :class:`Window <kivy.core.window.WindowBase>`
                The application Window to bind to.
            `ctx`: A :class:`~kivy.uix.widget.Widget` or subclass
                The Widget to be inspected.

    '''
    # Dunno why, but if we are creating inspector within the start(), no lang
    # rules are applied.
    ctx.inspector = Inspector(win=win)
    win.bind(children=ctx.inspector.on_window_children,
             on_keyboard=ctx.inspector.keyboard_shortcut)


def start(win, ctx):
    ctx.ev_late_create = Clock.schedule_once(
        partial(create_inspector, win, ctx))


def stop(win, ctx):
    '''Stop and unload any active Inspectors for the given *ctx*.'''
    if hasattr(ctx, 'ev_late_create'):
        ctx.ev_late_create.cancel()
        del ctx.ev_late_create
    if hasattr(ctx, 'inspector'):
        win.unbind(children=ctx.inspector.on_window_children,
                   on_keyboard=ctx.inspector.keyboard_shortcut)
        win.remove_widget(ctx.inspector)
        del ctx.inspector
