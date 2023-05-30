'''
Leap Motion - finger only
=========================
'''

__all__ = ('LeapFingerEventProvider', 'LeapFingerEvent')

from collections import deque
from kivy.logger import Logger
from kivy.input.provider import MotionEventProvider
from kivy.input.factory import MotionEventFactory
from kivy.input.motionevent import MotionEvent

_LEAP_QUEUE = deque()

Leap = InteractionBox = None


def normalize(value, a, b):
    return (value - a) / float(b - a)


class LeapFingerEvent(MotionEvent):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('is_touch', True)
        kwargs.setdefault('type_id', 'touch')
        super().__init__(*args, **kwargs)
        self.profile = ('pos', 'pos3d',)

    def depack(self, args):
        super().depack(args)
        if args[0] is None:
            return
        x, y, z = args
        self.sx = normalize(x, -150, 150)
        self.sy = normalize(y, 40, 460)
        self.sz = normalize(z, -350, 350)
        self.z = z


class LeapFingerEventProvider(MotionEventProvider):

    __handlers__ = {}

    def start(self):
        # don't do the import at start, or the error will be always displayed
        # for user who don't have Leap
        global Leap, InteractionBox
        import Leap
        from Leap import InteractionBox

        class LeapMotionListener(Leap.Listener):

            def on_init(self, controller):
                Logger.info('leapmotion: Initialized')

            def on_connect(self, controller):
                Logger.info('leapmotion: Connected')

            def on_disconnect(self, controller):
                Logger.info('leapmotion: Disconnected')

            def on_frame(self, controller):
                frame = controller.frame()
                _LEAP_QUEUE.append(frame)

            def on_exit(self, controller):
                pass

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
                # print(hand.id(), finger.id(), finger.tip())
                uid = '{0}:{1}'.format(hand.id, finger.id)
                available_uid.append(uid)
                position = finger.tip_position
                args = (position.x, position.y, position.z)
                if uid not in touches:
                    touch = LeapFingerEvent(self.device, uid, args)
                    events.append(('begin', touch))
                    touches[uid] = touch
                else:
                    touch = touches[uid]
                    touch.move(args)
                    events.append(('update', touch))
        for key in list(touches.keys())[:]:
            if key not in available_uid:
                events.append(('end', touches[key]))
                del touches[key]
        return events


# registers
MotionEventFactory.register('leapfinger', LeapFingerEventProvider)
