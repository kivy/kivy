'''
Switch
======

.. versionadded:: 1.0.7

.. image:: images/switch-on.jpg
    :align: right

.. image:: images/switch-off.jpg
    :align: right

The :class:`Switch` widget is active or inactive, like a mechanical light
switch. The user can swipe to the left/right to activate/deactivate it::

    switch = Switch(active=True)

To attach a callback that listens to the activation state::

    def callback(instance, value):
        print('the switch', instance, 'is', value)

    switch = Switch()
    switch.bind(active=callback)

By default, the representation of the widget is static and the background
image has a size of 83x32 pixels, and the sliding button image has a size of
41x32 pixels.
You can set your own images to be used in inactive, active and disabled states,
for both the background and the sliding button. Besides being able to define
the dimensions of each one of them.

There is also an option to set a horizontal spacing. Which allows you to
create styles in which there is a spacing between the sides of the sliding
button and the background.

.. warning::

    Avoid setting values too high for spacing. Especially values very close to
    or greater than half of the background_width value, as the sliding button
    may not have enough space to slide/be dragged.

The background image is centered within the widget. The sliding button image
is centered vertically within the widget and slides horizontally to the sides,
obeying the limit imposed by the spacing.

The entire widget is active, not just the part with graphics. As long as you
swipe over the widget's bounding box, it will work.

.. note::

    If you want to control the state with just a single touch instead of a
    swipe, use the :class:`ToggleButton` instead.
    However, the switch works with both a single touch and a swipe.

Kv Example::

    BoxLayout:
        Label:
            text: 'power up'
        Switch:
            id: switch
        Label:
            text: 'woooooooooooh' if switch.active else ''
'''


from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.properties import BooleanProperty, ObjectProperty, NumericProperty,\
                            StringProperty, ReferenceListProperty


class Switch(Widget):
    '''Switch class. See module documentation for more information.
    '''
    active = BooleanProperty(False)
    '''Indicate whether the switch is active or inactive.

    :attr:`active` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    background_width = NumericProperty(82)
    '''Allows to control the switch background height.

    :attr:`background_width` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 82.

    .. versionadded:: 2.1.0
    '''

    background_height = NumericProperty(32)
    '''Allows to control the switch background height.

    :attr:`background_height` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 32.

    .. versionadded:: 2.1.0
    '''

    background_size = ReferenceListProperty(background_width,
                                            background_height)
    '''Size of the switch background in the format (background_width,
    background_height)

    :attr:`background_size` is a
    :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`sliding_button_width`, :attr:`sliding_button_height`) properties.

    .. versionadded:: 2.1.0
    '''

    sliding_button_width = NumericProperty(41)
    '''Allows to control the switch sliding button width

    :attr:`button_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 41.

    .. versionadded:: 2.1.0
    '''

    sliding_button_height = NumericProperty(32)
    '''Allows to control the switch sliding button height

    :attr:`sliding_button_height` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 32.

    .. versionadded:: 2.1.0
    '''

    sliding_button_size = ReferenceListProperty(sliding_button_width,
                                                sliding_button_height)
    '''Size of the switch sliding button in the format (sliding_button_width,
    sliding_button_height)

    :attr:`sliding_button_size` is a
    :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`sliding_button_width`, :attr:`sliding_button_height`) properties.

    .. versionadded:: 2.1.0
    '''

    spacing = NumericProperty(0)
    '''Horizontal spacing allows you to control the space between the left of
    the background and the left of the slider when the switch is inactive, and
    the space between the right of the background and the right of the slider
    when the switch is active.
    This allows you to limit how far the slider can go, which facilitates
    styling. Especially in cases where there is a space between the sides of
    the button and the background.

    :attr:`spacing` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.

    .. versionadded:: 2.1.0
    '''

    background_inactive = StringProperty(
        'atlas://data/images/defaulttheme/switch-background')
    '''Switch background image used for the default graphical representation
    when the switch is inactive.

    :attr:`background_inactive` is a
    :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/switch-background'.

    .. versionadded:: 2.1.0
    '''

    background_active = StringProperty(
        'atlas://data/images/defaulttheme/switch-background')
    '''Switch background image used for the default graphical representation
    when the switch is active.

    :attr:`background_active` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/switch-background'.

    .. versionadded:: 2.1.0
    '''

    background_disabled = StringProperty(
        'atlas://data/images/defaulttheme/switch-background_disabled')
    '''Switch background image used for the default graphical representation
    when the switch is disabled (active or inactive).

    :attr:`background_disabled` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/switch-background_disabled'.

    .. versionadded:: 2.1.0
    '''

    sliding_button_inactive = StringProperty(
        'atlas://data/images/defaulttheme/switch-button')
    '''Switch sliding button image used for the default graphical
    representation when the switch is inactive.

    :attr:`sliding_button_inactive` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/switch-button'.

    .. versionadded:: 2.1.0
    '''

    sliding_button_active = StringProperty(
        'atlas://data/images/defaulttheme/switch-button')
    '''Switch sliding button image used for the default graphical
    representation when the switch is active.

    :attr:`sliding_button_active` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/switch-button'.

    .. versionadded:: 2.1.0
    '''

    sliding_button_disabled = StringProperty(
        'atlas://data/images/defaulttheme/switch-button_disabled')
    '''Switch sliding button image used for the default graphical
    representation when the switch is disabled (active or inactive).

    :attr:`sliding_button_disabled` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/switch-button_disabled'.

    .. versionadded:: 2.1.0
    '''

    touch_control = ObjectProperty(None, allownone=True)
    '''(internal) Contains the touch that currently interacts with the switch.

    :attr:`touch_control` is an :class:`~kivy.properties.ObjectProperty`
    and defaults to None.
    '''

    touch_distance = NumericProperty(0)
    '''(internal) Contains the distance between the initial position of the
    touch and the current position to determine if the swipe is from the left
    or right.

    :attr:`touch_distance` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.
    '''

    active_norm_pos = NumericProperty(0)
    '''(internal) Contains the normalized position of the movable element
    inside the switch.

    :attr:`active_norm_pos` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.
    '''

    norm_spacing = NumericProperty(0)
    '''(internal) Contains the normalized spacing inside the switch.

    :attr:`norm_spacing` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.

    .. versionadded:: 2.1.0
    '''

    def on_kv_post(self, *args):
        self.norm_spacing = min(abs(self.spacing / self.background_width), 0.499)
        self.active_norm_pos = abs(self.norm_spacing - int(self.active))
        self.bind(active=self.anim_sliding_button)

    def anim_sliding_button(self, *args):
        norm_pos = abs(self.norm_spacing - int(self.active))
        if self.active_norm_pos != norm_pos:
            Animation(active_norm_pos=norm_pos, t='out_quad', d=.2).start(self)

    def on_touch_down(self, touch):
        if self.disabled or self.touch_control is not None:
            return
        if not self.collide_point(*touch.pos):
            return
        touch.grab(self)
        self.touch_distance = 0
        self.touch_control = touch
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return
        self.touch_distance = touch.x - touch.ox
        if self.active:
            origin_pos = 1 - self.norm_spacing
        else:
            origin_pos = 0 + self.norm_spacing
        self.active_norm_pos = max(self.norm_spacing,
                                   min(1 - self.norm_spacing,
                                       origin_pos + self.touch_distance /
                                       max(1, self.background_width -
                                           self.sliding_button_width)))
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        # depending of the distance, activate by norm pos or invert
        if abs(touch.ox - touch.x) < 5:
            self.active = not self.active
        elif self.active != (self.active_norm_pos > 0.5):
            self.active = self.active_norm_pos > 0.5
        # animate back the sliding button to current state
        else:
            self.anim_sliding_button()
        self.touch_control = None
        return True


if __name__ == '__main__':
    from kivy.app import App

    class SwitchApp(App):
        def build(self):
            return Switch()

    SwitchApp().run()
