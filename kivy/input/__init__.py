# pylint: disable=W0611
'''
Input management
================

Our input system is wide and simple at the same time. We are currently able to
natively support :

* Windows multitouch events (pencil and finger)
* MacOSX touchpads
* Linux multitouch events (kernel and mtdev)
* Linux wacom drivers (pencil and finger)
* TUIO

All the input management is configurable in the Kivy :mod:`~kivy.config`. You
can easily use many multitouch devices in one Kivy application.

When the events have been read from the devices, they are dispatched through
a post processing module before being sent to your application. We also have
several default modules for :

* Double tap detection
* Decreasing jittering
* Decreasing the inaccuracy of touch on "bad" DIY hardware
* Ignoring regions
'''


from kivy.input.motionevent import MotionEvent
from kivy.input.postproc import kivy_postproc_modules
from kivy.input.provider import MotionEventProvider
from kivy.input.factory import MotionEventFactory
import kivy.input.providers

__all__ = (
    MotionEvent.__name__,
    MotionEventProvider.__name__,
    MotionEventFactory.__name__,
    'kivy_postproc_modules')

