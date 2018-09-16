from __future__ import division

from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.uix.slider import Slider
from kivy.properties import NumericProperty, OptionProperty, StringProperty
from kivy.logger import Logger

# Compatibility HACK: If GPIOInputProvider is not available
# launch warning instead of exception
try:
    from kivy.input.providers.gpioinput import GPIOEvent, AXIS_COORDS
except ImportError:
    Logger.warning(
        'GPIOInput: Module not found: DialBehavior is not available')
    AXIS_COORDS = {'x': 'x', 'y': 'y'}

    class GPIOEvent(object):
        pass


class DialBehavior(EventDispatcher):

    AXIS = AXIS_COORDS.values()

    dial_device = StringProperty(None, allownone=True)
    dial_axis = OptionProperty(AXIS[0], options=AXIS)
    dial_step = NumericProperty(1)
    dial_accelms = NumericProperty(200)

    def __init__(self, *args, **kwargs):
        self._last_update = 0
        self._dial_acc_value = 0
        super(DialBehavior, self).__init__(*args, **kwargs)
        self.register_event_type('on_dial')
        Window.bind(on_motion=self.on_motion)

    def on_motion(self, instance, evtype, event):
        if not isinstance(event, GPIOEvent):
            return False

        Logger.trace('%s: on_motion: evtype=%r event=%r' %
                     (self.__class__.__name__, evtype, event))

        # Filter on event conditions
        if ('dial' not in event.profile or
                (self.dial_device and self.dial_device != event.device) or
                (self.dial_axis and self.dial_axis not in event.push_attrs)):
            return False

        # Dial value received on the event for axis 'dial_axis' (+1/-1)
        dial_raw_value = getattr(event, self.dial_axis)

        # Reset accumulated value if direction changed or accel timeout
        if ((self._dial_acc_value * dial_raw_value < 0) or
                (event.time_update - self._last_update >
                    self.dial_accelms / 1000)):
            self._dial_acc_value = 0

        self._dial_acc_value += dial_raw_value
        self._last_update = event.time_update

        dial_value = self._dial_acc_value * self.dial_step

        Logger.debug(
            '%s: on_motion: dispatching on_dial(axis=%s, value=%d)' %
            (self.__class__.__name__, self.dial_axis, dial_value))
        self.dispatch('on_dial', dial_value)

        return False

    def on_dial(self, value):
        pass

    @staticmethod
    def constraint(x, min, max):
        return min if x < min else max if x > max else x


class DialSlider(DialBehavior, Slider):

    def on_dial(self, dial):
        self.value = self.constraint(
            self.value + dial,
            self.min,
            self.max)


if __name__ == '__main__':
    import kivy
    kivy.require('1.9.2')
    from kivy.base import runTouchApp
    from kivy.lang import Builder

    Builder.load_string("""

<DialSlider>:
    dial_axis: 'x'
    size_hint_y: 0.1
    min: 0
    max: 200
    value: 100

    """)

    runTouchApp(widget=DialSlider())
