'''
Hover Behavior
===============

The :class:`~kivy.uix.behaviors.button.HoverBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class provides
mouse hover behavior. You can combine this class with
other widgets, such as an :class:`~kivy.uix.button.Button`, to change
background colors or display other effects when mouse cursor is on top
of kivy widgets

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

Example
-------

The following example adds hover behavior to a slider and buttons,
displays available functionality::

from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty
from kivy.uix.properties import HoverBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.app import runTouchApp
from kivy.lang import Builder


class RootWidget(FloatLayout):
    hov_grab = ObjectProperty(None, allownone=True)
    min_hov = NumericProperty(0)

    def on_min_hov(self, _, value):
        HoverBehavior.set_min_hover_height(value)

    def on_hov_grab(self, _, value):
        if value:
            value.grab_hover()
        else:
            HoverBehavior.remove_hover_grab()

class HovButton(Button, HoverBehavior):
    pass

class HovSlider(Slider, HoverBehavior):
    grabbed_hover = BooleanProperty(False)
    hov_callback = None

    def on_touch_down(self, touch):
        ret = super(HovSlider, self).on_touch_down(touch)
        if ret:
            self.hov_callback(self)
            self.grabbed_hover = True
        return ret

    def on_touch_up(self, touch):
        ret = super(HovSlider, self).on_touch_up(touch)
        if ret:
            self.hov_callback(None)
            self.grabbed_hover = False
        return ret

Builder.load_string("""
<Label>:
    color: 0.9, 0.9, 0.9, 1
    text_size: self.width, None
    height: self.texture_size[1]
    halign: 'center'
    valign: 'center'

<HovButton>:
    background_color: [0.2, 0.2, 0.8, 1] if self.hovering else [0.2, 0.2, 0.2, 1]

<RootWidget>:
    Label:
        size_hint: 1, 0.1
        pos_hint: {'center': (0.5, 0.95)}
        text: "min_hover_height: %s  hover_grab: %s" % (root.min_hov, root.hov_grab)
        canvas.before:
            Color:
                rgb: 0.2, 0.2, 0.2
            Rectangle:
                size: self.size
                pos: self.pos

    HovSlider:
        id: hovslider
        size_hint: 0.9, 0.1
        pos_hint: {'center': (0.5, 0.7)}
        value_track: True
        value_track_color: (0.95, 0.1, 0.0, 1) if self.hovering or self.grabbed_hover else (0.3, 0.3, 0.5, 1)
        min: 0
        max: 1000
        value: int(self.max * 0.5)
        hov_callback: lambda value: setattr(root, "hov_grab", value)

    Label:
        size_hint_y: None
        pos: 0, hovslider.top + self.height
        text: "Slider that grabs hover and prevents other widgets from displaying hover effects when being slided"

    BoxLayout:
        id: sizebox
        size_hint: 1, 0.12
        pos: 0, tggrab.top
        orientation: 'horizontal'

        HovButton:
            size_hint_x: 0.5
            hover_height: 10
            text: 'Set min_hover_height: 10'
            on_release: root.min_hov = self.hover_height

        HovButton:
            size_hint_x: 0.5
            hover_height: 0
            text: 'Set min_hover_height: 0'
            on_release: root.min_hov = self.hover_height

    Label:
        size_hint: 0.9, None
        height: self.texture_size[1]
        pos: root.width * 0.05, sizebox.top + (self.height * 0.5)
        text_size: self.size
        text: "Buttons that change HoverBehavior min_hover_height to their own height, useful when you want to disable hovering for lower widgets after opening a popup or putting something else on top"

    HovButton:
        id: tggrab
        size_hint: 1, 0.12
        pos: 0, 0
        text: 'Toggle grab hover'
        on_release: setattr(root, "hov_grab", None) if root.hov_grab else setattr(root, "hov_grab", self)
""")

runTouchApp(RootWidget())


See :class:`~kivy.uix.behaviors.HoverBehavior` for details.
'''

__all__ = ('HoverBehavior', )

from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty
from kivy.weakproxy import WeakProxy
from kivy.core.window import Window


class HoverBehavior(object):
    '''
    The HoverBehavior `mixin <https://en.wikipedia.org/wiki/Mixin>`_ provides
    Hover behavior. When combined with a widget, hovering mouse cursor
    above it's position will call it's on_hovering event. Please see
    the :mod:`hover behaviors module <kivy.uix.behaviors.hover>` documentation
    for more information.

    .. versionadded:: 1.10.1
    '''

    _hover_grab_widget = None
    '''WeakProxy of widget which has grabbed focus or None'''

    _hover_widgets = []
    '''List of hover widget WeakProxy references'''

    min_hover_height = 0
    '''Numeric class attribute of minimum height where "hovering" property
    will be updated'''

    hovering = BooleanProperty(False)
    '''Hover state, is True when mouse enters it's position

    :attr:`hovering` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to `False`.
    '''

    hover_height = NumericProperty(0)
    '''Number that is compared to min_hover_height.

    :attr:`hover_height` is a :class:`~kivy.properties.NumericProperty` and
    defaults to `0`.
    '''

    def _on_hover_mouse_move(win, pos):
        '''Internal method that is binded on Window.mouse_pos.
        Compares mouse position with widget positions,
        ignoring disabled widgets and widgets with hover_height below
        HoverBehavior.min_hover_height,
        then sets widget hovering property to False or True'''

        collided = [] # widget weak proxies that collide with mouse pos

        if HoverBehavior._hover_grab_widget:
            HoverBehavior.hover_widget_refs = [HoverBehavior._hover_grab_widget]
        else:
            HoverBehavior.hover_widget_refs = HoverBehavior._hover_widgets
        for ref in HoverBehavior.hover_widget_refs:
            if not ref.disabled and ref.collide_point_window(*pos):
                # Get all widgets that are at mouse pos
                collided.append(ref)
            # Remove hover from all widgets that are not at mouse pos
            elif ref.hovering:
                ref.hovering = False

            if collided:
                # Find the highest widget and set it's hover to True
                # Set hover to False for other widgets
                highest = collided[0]
                if len(collided) > 1:
                    for ref in collided:
                        if ref.hover_height > highest.hover_height:
                            if highest.hovering:
                                highest.hovering = False
                            highest = ref
                        elif ref.hovering:
                            ref.hovering = False

                if HoverBehavior._hover_grab_widget:
                    if not highest.hovering:
                        highest.hovering = True

                elif highest.hover_height >= HoverBehavior.min_hover_height:
                    if not highest.hovering:
                        highest.hovering = True

    @staticmethod
    def force_update_hover():
        '''Gets window mouse position and updates hover state for all widgets'''
        HoverBehavior._on_hover_mouse_move(Window, Window.mouse_pos)

    @staticmethod
    def set_min_hover_height(number):
        '''Sets min_hover_height for HoverBehavior class'''
        HoverBehavior.min_hover_height = number

    @staticmethod
    def get_min_hover_height():
        '''Gets min_hover_height from HoverBehavior class'''
        return HoverBehavior.min_hover_height

    def __init__(self, **kwargs):
        super(HoverBehavior, self).__init__(**kwargs)
        self.bind(parent=self._on_parent_update_hover)

    def _on_parent_update_hover(self, _, parent):
        '''Adds self to hover system when has a parent,
        otherwise removes self from hover system'''
        if parent:
            self.hoverable_add()
        else:
            self.hoverable_remove()

    def hoverable_add(self):
        '''Add widget in hover system. By default, is called when widget
        is added to a parent'''
        HoverBehavior._hover_widgets.append(WeakProxy(self))

    def hoverable_remove(self):
        '''Remove widget from hover system. By default is called when widget
        is removed from a parent'''
        HoverBehavior._hover_widgets.remove(self)

    def grab_hover(self):
        '''Prevents other widgets from receiving hover'''
        HoverBehavior._hover_grab_widget = WeakProxy(self)

    @staticmethod
    def get_hover_grab_widget():
        '''Returns widget which has grabbed hover currently or None'''
        return HoverBehavior._hover_grab_widget

    @staticmethod
    def remove_hover_grab():
        '''Removes widget WeakProxy from hover system'''
        HoverBehavior._hover_grab_widget = None

    def collide_point_window(self, x, y):
        '''Widget collide point method that compares arguments to
        "self.to_window(self.x, self.y)" instead of "self.x, self.y"'''
        sx, sy = self.to_window(self.x, self.y)
        return sx <= x <= sx + self.width and sy <= y <= sy + self.height


Window.bind(mouse_pos=HoverBehavior._on_hover_mouse_move)
