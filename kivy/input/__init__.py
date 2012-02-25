'''
Input management
================

Our input system is wide and simple at the same time. We are currently able to
support natively :

* Windows multitouch event (pencil and finger)
* MacOSX touchpad
* Linux multitouch event (kernel and mtdev)
* Linux wacom driver (pencil and finger)
* TUIO

All the input management is configurable in the Kivy configuration. You can
easily use many multitouch device into one Kivy application.

When the event have been read from devices, they are dispatched through post
processing module, before sending them to your application. We got also several
module by default for :

* Double tap detection
* Decrease jittering
* Decrease the loose of touch on "bad" DIY hardware
* Ignore regions
'''


from kivy.input.motionevent import MotionEvent
from kivy.input.postproc import kivy_postproc_modules
from kivy.input.provider import MotionEventProvider
from kivy.input.factory import MotionEventFactory
__import__('kivy.input.providers')

__all__ = (
    MotionEvent.__name__,
    MotionEventProvider.__name__,
    MotionEventFactory.__name__,
    'kivy_postproc_modules')

