'''
Compass example
===============

This example is a demonstration of Hardware class usage.
But it has severals drawbacks, like using only the magnetic sensor, and
extrapolating values to get the orientation. The compass is absolutely not
accurate.

The right way would be to get the accelerometer + magnetic, and computer
everything according to the phone orientation. This is not the purpose of this
example right now.

You can compile it with::

    ./build.py --package org.test.compass --name compass \
        --private ~/code/kivy/examples/android/compass \
        --window --version 1.0 debug installd
 
'''


import kivy
kivy.require('1.7.0')

from jnius import autoclass
from kivy.app import App
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.vector import Vector
from kivy.animation import Animation

Hardware = autoclass('org.renpy.android.Hardware')


class CompassApp(App):

    needle_angle = NumericProperty(0)

    def build(self):
        self._anim = None
        Hardware.magneticFieldSensorEnable(True)
        Clock.schedule_interval(self.update_compass, 1 / 10.)

    def update_compass(self, *args):
        # read the magnetic sensor from the Hardware class
        (x, y, z) = Hardware.magneticFieldSensorReading()

        # calculate the angle
        needle_angle = Vector(x , y).angle((0, 1)) + 90.

        # animate the needle
        if self._anim:
            self._anim.stop(self)
        self._anim = Animation(needle_angle=needle_angle, d=.2, t='out_quad')
        self._anim.start(self)

    def on_pause(self):
        # when you are going on pause, don't forget to stop the sensor
        Hardware.magneticFieldSensorEnable(False)
        return True

    def on_resume(self):
        # reactivate the sensor when you are back to the app
        Hardware.magneticFieldSensorEnable(True)

if __name__ == '__main__':
    CompassApp().run()

