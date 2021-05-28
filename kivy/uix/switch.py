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

By default, the Switch widget has the property size_hint = (None, None) and the
property size = (82, 32). The representation of the widget is static and the
default background image has a size of 82x32 pixels and the slidding button
image has a size of 41x32 pixels. The background image is centered within the
widget and the slidding button that slides in x axis is verticaly centered
within the widget.

You can controll the background image height using
:attr:`switch_background_relative_size_hint_y` or
:attr:`switch_background_relative_size_hint_y`.

.. note::
    In order to avoid unespected behaviours, there is no property to control
    switch background width.
    The switch background width is the same of the Switch width.

You can also controll the size of the slidding button image of the switch using
the size hint relative to the Switch widget, with the
:attr:`switch_button_relative_size_hint_x` and
:attr:`switch_button_relative_size_hint_y` or
:attr:`switch_button_relative_size_hint` properties.
The size in absolute values (regardless of Switch size) can be set using the
:attr:`switch_button_width` and :attr:`switch_button_height` or
:attr:`switch_button_size` properties.


The entire widget is active, not just the part with graphics. As long as you
swipe over the widget's bounding box, it will work.


The background width is by default, the same of Switch width. However the
height is independent, so when setting the size_hint_y or heith of the Switch
widget, make sure that the Switch height match to the highest value between
slidding button height and background height.

The code bellow represents an incorrect way to set the switch properties, with
the widget's bounding box bigger than its components.
The red rectangle shows the actual size os the widget.

.. container:: align-right

    .. figure:: images/incorrect_switch_setting.png
        :scale: 50%

        incorrect switch setting

    .. figure:: images/correct_switch_setting.png
        :scale: 50%

        correct switch setting

.. code-block:: kv
    Switch:
        size_hint: (None, None)
        size: dp(82), dp(64)
        switch_background_relative_size_hint_y: 0.5
        switch_button_relative_size_hint: 0.5, 0.5
        canvas.before:
            Color:
                rgb: 1, 0, 0
            Rectangle:
                size: self.size
                pos: self.pos

Bellow is an example among many, of how to set switch properties correctly:

.. code-block:: kv
    Switch:
        size_hint: (None, None)
        size: dp(82), dp(32)
        switch_background_relative_size_hint_y: 1
        switch_button_relative_size_hint: 0.5, 1
        canvas.before:
            Color:
                rgba: 1, 0, 0
            Rectangle:
                size: self.size
                pos: self.pos

.. note::
    If you want to control the state with a single touch instead of a swipe,
    use the :class:`ToggleButton` instead.
    However, Switch works with both single touch and swipe.

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
from kivy.properties import (BooleanProperty, ObjectProperty, NumericProperty,
                             StringProperty, ReferenceListProperty)


class Switch(Widget):
    '''Switch class. See module documentation for more information.
    '''
    active = BooleanProperty(False)
    '''Indicate whether the switch is active or inactive.
    :attr:`active` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
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
    inside the switch, in the 0-1 range.
    :attr:`active_norm_pos` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 0.
    '''

    switch_background_relative_size_hint_y = NumericProperty(1, allownone=True)
    '''That property works relative to Switch widget width.

    Allows you to control the height of the switch background, relative to
    Switch widget width.

    Example of how to set switch background height as half of
    Switch widget height, i.e. 20:

    .. code-block:: kv
        Switch:
            size_hint: None, None
            size: 100, 40
            switch_background_relative_size_hint_y: 0.5

    :attr:`switch_background_relative_size_hint_y` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 1.

    .. versionadded:: 2.1.0
    '''

    switch_background_height = NumericProperty(32)
    '''Allows to control the switch background height independently of Switch
    widget height, once switch_background_relative_size_hint_y is set to None.

    :attr:`switch_background_height` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 32.

    .. versionadded:: 2.1.0
    '''

    switch_button_relative_size_hint_x = NumericProperty(0.5, allownone=True)
    '''That property works relative to Switch widget width.

    Allows you to control the width of the slidding switch button, relative to
    Switch widget width.

    Example of how to set switch button width as half of Switch widget width,
    i.e. 50:

    .. code-block:: kv
        Switch:
            size_hint: None, None
            size: 100, 40
            switch_button_relative_size_hint_x: 0.5


    :attr:`switch_button_relative_size_hint_x` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 0.5.

    .. versionadded:: 2.1.0
    '''

    switch_button_relative_size_hint_y = NumericProperty(1, allownone=True)
    '''That property works in the same way of
    :attr:`switch_button_relative_size_hint_x`,
    but relative to Switch widget heigh.

    :attr:`switch_button_relative_size_hint_y` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 1.

    .. versionadded:: 2.1.0
    '''

    switch_button_relative_size_hint = ReferenceListProperty(
        switch_button_relative_size_hint_x,
        switch_button_relative_size_hint_y)
    '''Size hint of the switch button relative to Switch widget in the format
    (switch_button_relative_size_hint_x, switch_button_relative_size_hint_y)

    :attr:`switch_background_relative_size_hint` is a
    :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`switch_background_relative_size_hint_x`,
    :attr:`switch_background_relative_size_hint_y`) properties.

    .. versionadded:: 2.1.0
    '''

    switch_button_width = NumericProperty(41)
    '''Allows to control the switch button width independently of Switch widget
    width, once switch_button_relative_size_hint_x is set to None.

    :attr:`switch_button_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 41.

    .. versionadded:: 2.1.0
    '''

    switch_button_height = NumericProperty(32)
    '''Allows to control the switch button height independently of Switch
    widget height, once switch_button_relative_size_hint_y is set to None.

    :attr:`switch_button_height` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 32.

    .. versionadded:: 2.1.0
    '''

    switch_button_size = ReferenceListProperty(
        switch_button_width,
        switch_button_height)
    '''Size of the switch button in the format (switch_button_width,
        switch_button_height)

    :attr:`switch_button_size` is a
    :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`switch_button_width`, :attr:`switch_button_height`) properties.

    .. versionadded:: 2.1.0
    '''

    switch_background_inactive = StringProperty(
        'atlas://data/images/defaulttheme/switch-background')
    '''Switch background image used for the default graphical representation
    when the switch is inactive.

    :attr:`switch_background_inactive` is a
    :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/switch-background'.

    .. versionadded:: 2.1.0
    '''

    switch_background_active = StringProperty(
        'atlas://data/images/defaulttheme/switch-background')
    '''Switch background image used for the default graphical representation
    when the switch is active.

    :attr:`switch_background_active` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/switch-background'.

    .. versionadded:: 2.1.0
    '''

    switch_background_disabled = StringProperty(
        'atlas://data/images/defaulttheme/switch-background_disabled')
    '''Switch background image used for the default graphical representation
    when the switch is disabled (active or inactive).

    :attr:`switch_background_disabled` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/switch-background_disabled'.

    .. versionadded:: 2.1.0
    '''

    switch_button = StringProperty(
        'atlas://data/images/defaulttheme/switch-button')
    '''Switch button image used for the default graphical representation when
    the switch is enabled (active or inactive).

    :attr:`switch_background_inactive` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/switch-button'.

    .. versionadded:: 2.1.0
    '''

    switch_button_disabled = StringProperty(
        'atlas://data/images/defaulttheme/switch-button_disabled')
    '''Switch button image used for the default graphical representation when
    the switch is disabled (active or inactive).

    :attr:`switch_background_inactive` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    'atlas://data/images/defaulttheme/switch-button_disabled'.

    .. versionadded:: 2.1.0
    '''

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
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        # depending of the distance, activate by norm pos or invert
        if abs(touch.ox - touch.x) < 5:
            self.active = not self.active
        else:
            self.active = self.active_norm_pos > 0.5
        Animation(active_norm_pos=int(self.active), t='out_quad',
                  d=.2).start(self)
        self.touch_control = None
        return True


if __name__ == '__main__':
    from kivy.app import App

    class SwitchApp(App):
        def build(self):
            return Switch()

    SwitchApp().run()
