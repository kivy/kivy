"""
Xinput2 input provider
=========================
"""

cdef extern from "xinput2_core.c":
    ctypedef struct TouchStruct:
        int id, state
        float x, y

cdef extern int start()
cdef extern int idle()

# Dummy class to bridge between the MotionEventProvider class and C
from kivy.event import EventDispatcher
class InputX11(EventDispatcher):

    def start(self):
        start()

    def x11_idle(self):
        idle()

    def on_touch_down(self, touch):
        pass

    def on_touch_move(self, touch):
        pass

    def on_touch_up(self, touch):
        pass
xinput = InputX11()

# Create callback for touch events from C->Cython
ctypedef int (*touch_cb_type)(TouchStruct *touch)
cdef extern void x11_set_touch_callback(touch_cb_type callback)
cdef int event_callback(TouchStruct *touch):
    touch_down = 0
    touch_move = 1
    touch_up = 3
    py_touch = {"id": touch.id,
                "x": touch.x,
                "y": touch.y}
    print touch.id, touch.state, touch.x, touch.y
    if touch.state == touch_down:
        xinput.on_touch_down(py_touch)
    elif touch.state == touch_move:
        xinput.on_touch_move(py_touch)
    elif touch.state == touch_up:
        xinput.on_touch_up(py_touch)
x11_set_touch_callback(event_callback)


#######
# Input provider
__all__ = ('Xinput2EventProvider', 'Xinput2Event')

from kivy.logger import Logger
from kivy.input.provider import MotionEventProvider
from kivy.input.factory import MotionEventFactory
from kivy.input.motionevent import MotionEvent


class Xinput2Event(MotionEvent):

    def depack(self, args):
        super(Xinput2Event, self).depack(args)
        if args[0] is None:
            return
        self.is_touch = True


class Xinput2EventProvider(MotionEventProvider):

    __handlers__ = {}

    def start(self):
        xinput.start()

    def update(self, dispatch_fn):
        xinput.x11_idle()


# registers
MotionEventFactory.register('xinput2', Xinput2EventProvider)
