'''
Leap Motion - finger only
=========================
'''

__all__ = ('LeapFingerEventProvider', )

#from kivy.base import EventLoop
from collections import deque
from kivy.logger import Logger
from kivy.input.provider import MotionEventProvider
from kivy.input.factory import MotionEventFactory
from kivy.input.motionevent import MotionEvent
import Leap

_LEAP_QUEUE = deque()


def normalize(value, a, b):
    return (value - a) / float(b - a)

class LeapFingerEvent(MotionEvent):

    def depack(self, args):
        super(LeapFingerEvent, self).depack(args)
        if args[0] is None:
            return
        self.profile = ('pos', 'pos3d', )
        x, y, z = args
        self.sx = normalize(x, -150, 150)
        self.sy = normalize(y, 40, 460)
        self.z = z
        self.is_touch = True


class LeapFingerEventProvider(MotionEventProvider):
    __handlers__ = {}

    def start(self):
        self.uid = 0
        self.touches = {}
        self.listener = LeapMotionListener()
        self.controller = Leap.Controller(self.listener)

    def update(self, dispatch_fn):
        try:
            while True:
                frame = _LEAP_QUEUE.popleft()
                events = self.process_frame(frame)
                for ev in events:
                    dispatch_fn(*ev)
        except IndexError:
            pass

    def process_frame(self, frame):
        events = []
        touches = self.touches
        available_uid = []
        for hand in frame.hands:
            for finger in hand.fingers:
                #print hand.id(), finger.id(), finger.tip()
                uid = '{0}:{1}'.format(hand.id, finger.id)
                available_uid.append(uid)
                args = (finger.tip_position.x, finger.tip_position.y, finger.tip_position.z)
                if uid not in touches:
                    touch = LeapFingerEvent(self.device, uid, args)
                    events.append(('begin', touch))
                    touches[uid] = touch
                else:
                    touch = touches[uid]
                    touch.move(args)
                    events.append(('update', touch))
        for key in touches.keys()[:]:
            if key not in available_uid:
                events.append(('end', touches[key]))
                del touches[key]
        return events


class LeapMotionListener(Leap.Listener):

    def on_init(self, controller):
        Logger.info("leapmotion: Initialized")

    def on_connect(self, controller):
        Logger.info("leapmotion: Connected")

    def on_disconnect(self, controller):
        Logger.info("leapmotion: Disconnected")

    def on_frame(self, controller):
        #Logger.debug("leapmotion: OnFrame")
        frame = controller.frame()
        _LEAP_QUEUE.append(frame)

    def on_exit(self, controller):
        pass


# registers
MotionEventFactory.register('leapfinger', LeapFingerEventProvider)
