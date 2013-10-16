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

import kivy
kivy.require('1.0.9')

import weakref
from kivy.animation import Animation
from kivy.logger import Logger
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.treeview import TreeViewNode
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, \
        Translate, Rotate, Scale
from kivy.properties import ObjectProperty, BooleanProperty, ListProperty, \
        NumericProperty, StringProperty, OptionProperty, \
        ReferenceListProperty, AliasProperty, VariableListProperty
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from functools import partial
from kivy.lang import Builder
from kivy.vector import Vector


Builder.load_string('''
<Inspector>:
    layout: layout
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
                            and root.widget.parent is not root.win else None
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
                TreeView:
                    id: treeview
                    size_hint_y: None
                    hide_root: True
                    height: self.minimum_height

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
        text: [repr(getattr(root.widget, root.key)), root.refresh][0]\
                if root.widget else ''
        text_size: (self.width, None)
''')


class TreeViewProperty(BoxLayout, TreeViewNode):

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

    key = ObjectProperty(None, allownone=True)

    inspector = ObjectProperty(None)

    refresh = BooleanProperty(False)


class Inspector(FloatLayout):

    widget = ObjectProperty(None, allownone=True)

    layout = ObjectProperty(None)

    treeview = ObjectProperty(None)

    inspect_enabled = BooleanProperty(False)

    activated = BooleanProperty(False)

    widget_info = BooleanProperty(False)

    content = ObjectProperty(None)

    at_bottom = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(Inspector, self).__init__(**kwargs)
        self.avoid_bring_to_top = False
        self.win = kwargs.get('win')
        with self.canvas.before:
            self.gcolor = Color(1, 0, 0, .25)
            PushMatrix()
            self.gtranslate = Translate(0, 0, 0)
            self.grotate = Rotate(0, 0, 0, 1)
            self.gscale = Scale(1.)
            self.grect = Rectangle(size=(0, 0))
            PopMatrix()
        Clock.schedule_interval(self.update_widget_graphics, 0)

    def on_touch_down(self, touch):
        ret = super(Inspector, self).on_touch_down(touch)
        if not ret and self.inspect_enabled:
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
        if self.avoid_bring_to_top:
            return
        self.avoid_bring_to_top = True
        win.remove_widget(self)
        win.add_widget(self)
        self.avoid_bring_to_top = False

    def highlight_at(self, x, y):
        widget = None
        # reverse the loop - look at children on top first
        for child in reversed(self.win.children):
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

    def update_widget_graphics(self, *l):
        if not self.activated:
            return
        if self.widget is None:
            self.grect.size = 0, 0
            return
        gr = self.grect
        widget = self.widget

        # determine rotation
        a = Vector(1, 0)
        b = Vector(widget.to_window(*widget.to_parent(0, 0)))
        c = Vector(widget.to_window(*widget.to_parent(1, 0))) - b
        angle = -a.angle(c)

        # determine scale
        scale = c.length()

        # apply transform
        gr.size = widget.size
        self.gtranslate.xy = Vector(widget.to_window(*widget.pos))
        self.grotate.angle = angle
        # fix warning about scale property deprecation
        self.gscale.xyz = (scale,) * 3

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

    def animation_close(self, instance, value):
        if self.activated is False:
            self.win.remove_widget(self)
            self.content.clear_widgets()
            treeview = self.treeview
            for node in list(treeview.iterate_all_nodes())[:]:
                node.widget_ref = None
                treeview.remove_node(node)
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
        wk_widget = weakref.ref(widget)
        for key in keys:
            text = '%s' % key
            node = TreeViewProperty(text=text, key=key, widget_ref=wk_widget)
            node.bind(is_selected=self.show_property)
            widget.bind(**{key: partial(
                self.update_node_content, weakref.ref(node))})
            treeview.add_node(node)

    def update_node_content(self, node, *l):
        node = node()
        if node is None:
            return
        node.refresh = True
        node.refresh = False

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

    def show_property(self, instance, value, key=None, index=-1, *l):
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
            # trying to resolve type dynamicly
            if type(value) in (str, str):
                dtype = 'string'
            elif type(value) in (int, float):
                dtype = 'numeric'
            elif type(value) in (tuple, list):
                dtype = 'list'

        if isinstance(prop, NumericProperty) or dtype == 'numeric':
            content = TextInput(text=str(value) or '', multiline=False)
            content.bind(text=partial(
                self.save_property_numeric, widget, key, index))
        elif isinstance(prop, StringProperty) or dtype == 'string':
            content = TextInput(text=value or '', multiline=True)
            content.bind(text=partial(
                self.save_property_text, widget, key, index))
        elif (isinstance(prop, ListProperty) or
              isinstance(prop, ReferenceListProperty) or
              isinstance(prop, VariableListProperty) or
              dtype == 'list'):
            content = GridLayout(cols=1, size_hint_y=None)
            content.bind(minimum_height=content.setter('height'))
            for i, item in enumerate(value):
                button = Button(text=repr(item), size_hint_y=None, height=44)
                if isinstance(item, Widget):
                    button.bind(on_release=partial(self.highlight_widget, item,
                        False))
                else:
                    button.bind(on_release=partial(self.show_property, widget,
                        item, key, i))
                content.add_widget(button)
        elif isinstance(prop, OptionProperty):
            content = GridLayout(cols=1, size_hint_y=None)
            content.bind(minimum_height=content.setter('height'))
            for option in prop.options:
                button = ToggleButton(text=option,
                    state='down' if option == value else 'normal',
                    group=repr(content.uid), size_hint_y=None,
                    height=44)
                button.bind(on_press=partial(
                    self.save_property_option, widget, key))
                content.add_widget(button)
        elif isinstance(prop, ObjectProperty):
            if isinstance(value, Widget):
                content = Button(text=repr(value))
                content.bind(on_release=partial(self.highlight_widget, value))
            elif isinstance(value, Texture):
                content = Image(texture=value)
            else:
                content = Label(text=repr(value))

        elif isinstance(prop, BooleanProperty):
            state = 'down' if value else 'normal'
            content = ToggleButton(text=key, state=state)
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

    def save_property_option(self, widget, key, instance, *l):
        try:
            setattr(widget, key, instance.text)
        except:
            pass


def create_inspector(win, ctx, *l):
    '''Create an Inspector instance attached to the *ctx* and bound to the
    Windows :py:func:`~kivy.core.window.WindowBase.on_keyboard` event for
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
    Clock.schedule_once(partial(create_inspector, win, ctx))


def stop(win, ctx):
    '''Stop and unload any active Inspectors for the given *ctx*.'''
    if hasattr(ctx, 'inspector'):
        win.unbind(children=ctx.inspector.on_window_children,
                   on_keyboard=ctx.inspector.keyboard_shortcut)
        win.remove_widget(ctx.inspector)
        del ctx.inspector

