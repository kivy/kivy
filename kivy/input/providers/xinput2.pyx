"""
Xinput2 input provider
=========================
"""

cdef extern from "xinput2_core.c":
    ctypedef struct TouchStruct:
        int t_id, state
        float x, y

cdef extern int init(int window_id)
cdef extern int idle()

# Dummy class to bridge between the MotionEventProvider class and C
class InputX11():

    def __init__(self):
        self.on_touch = None

    def start(self, window_id, on_touch):
        self.on_touch = on_touch
        init(window_id)

    def x11_idle(self):
        idle()

xinput = InputX11()

# Create callback for touch events from C->Cython
ctypedef int (*touch_cb_type)(TouchStruct *touch)
cdef extern void x11_set_touch_callback(touch_cb_type callback)
cdef int event_callback(TouchStruct *touch):
    py_touch = {"id": touch.t_id,
                "state": touch.state,
                "x": touch.x,
                "y": touch.y}
    xinput.on_touch(py_touch)
x11_set_touch_callback(event_callback)


#######
# Input provider
__all__ = ('Xinput2EventProvider', 'Xinput2Event')

from kivy.logger import Logger
from collections import deque
from kivy.base import EventLoop
from kivy.input.provider import MotionEventProvider
from kivy.input.factory import MotionEventFactory
from kivy.input.motionevent import MotionEvent


class Xinput2Event(MotionEvent):

    def depack(self, args):
        super(Xinput2Event, self).depack(args)
        if args[0] is None:
            return
        self.profile = ('pos',)
        width, height = EventLoop.window.system_size
        rx = args[0] / float(width)
        ry = 1. - args[1] / float(height)
        self.sx = rx
        self.sy = ry
        self.is_touch = True


class Xinput2EventProvider(MotionEventProvider):

    started = False

    def start(self):
        try:
            from kivy.core.window import Window
            window_id = Window.window_id
        except AttributeError:
            Logger.error("xinput2: This input provider only works in "
                         "combination with a x11 window")
            return
        except Exception as e:
            Logger.error("xinput2: Was not able to get window-id: %s" % e)
            return
        xinput.start(window_id=window_id, on_touch=self.on_touch)
        self.touch_queue = deque()
        self.touches = {}
        self.started = True

    def stop(self):
        self.started = False

    def update(self, dispatch_fn):
        if not self.started:
            return
        xinput.x11_idle()
        try:
            while True:
                event = self.touch_queue.popleft()
                dispatch_fn(*event)
        except IndexError:
            pass

    def on_touch(self, raw_touch):
        touches = self.touches
        args = [raw_touch["x"], raw_touch["y"]]

        if raw_touch["id"] not in self.touches:
            touch = Xinput2Event(self.device, raw_touch["id"], args)
            touches[raw_touch["id"]] = touch
            event = ('begin', touch)
        else:
            touch = touches[raw_touch["id"]]
            touch.move(args)
            if raw_touch["state"] == 1:
                event = ('update', touch)
            elif raw_touch["state"] == 2:
                event = ('end', touch)
                del touches[raw_touch["id"]]
            else:
                return
        self.touch_queue.append(event)


# registers
MotionEventFactory.register('xinput2', Xinput2EventProvider)
