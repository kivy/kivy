'''
Switch
======

.. versionadded:: 1.0.7

.. image:: images/switch-on.jpg
    :align: right

.. image:: images/switch-off.jpg
    :align: right

The switch is a boolean widget that can be active or inactive. You can swipe to
the left or right to activate or deactivate it::

    switch = Switch(active=True)

And attach a callback to listen the activation state::

    def callback(instance, value):
        print 'the switch', instance, 'is', value

    switch = Switch()
    switch.bind(active=callback)

By default, the representation of the widget is static. The minimum size
required is 83x32 pixels (according to the background image) and is displayed in
the center of the widget.

All the widget is active, not only the displayed part. If you swipe to the left
from anywhere, or from the right, it will work.
'''


from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.properties import BooleanProperty, ObjectProperty, NumericProperty


class Switch(Widget):
    '''Switch class, see module documentation for more information.
    '''

    active = BooleanProperty(False)
    '''Indicate if the switch is activated or not.

    :data:`active` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    touch_control = ObjectProperty(None, allownone=True)
    '''(internal) Used to store the current touch that interact with the switch.

    :data:`touch_control` is a :class:`~kivy.properties.ObjectProperty`, default
    to None.
    '''

    touch_distance = NumericProperty(0)
    '''(internal) Used to store the distance between the initial position of the
    touch and the current position to determinate if the swipe is from left or
    right.

    :data:`touch_distance` is a :class:`~kivy.properties.NumericProperty`,
    default to 0.
    '''

    active_norm_pos = NumericProperty(0)
    '''(internal) Used to store the normalized position of the movable element
    inside the switch, in the 0-1 range.

    :data:`active_norm_pos` is a :class:`~kivy.properties.NumericProperty`,
    default to 0.
    '''

    def on_touch_down(self, touch):
        if self.touch_control is not None:
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
    from kivy.base import runTouchApp
    runTouchApp(Switch())

