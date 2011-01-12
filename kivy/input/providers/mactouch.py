'''
Native support of MultitouchSupport framework for MacBook (MaxOSX platform)
===========================================================================
'''

__all__ = ('MacTouchProvider', )

import ctypes
import threading
import collections
import os
from kivy.input.provider import TouchProvider
from kivy.input.factory import TouchFactory
from kivy.input.touch import Touch
from kivy.input.shape import TouchShapeRect

if 'KIVY_DOC' not in os.environ:
    CFArrayRef = ctypes.c_void_p
    CFMutableArrayRef = ctypes.c_void_p
    CFIndex = ctypes.c_long

    MultitouchSupport = ctypes.CDLL('/System/Library/PrivateFrameworks/MultitouchSupport.framework/MultitouchSupport')

    CFArrayGetCount = MultitouchSupport.CFArrayGetCount
    CFArrayGetCount.argtypes = [CFArrayRef]
    CFArrayGetCount.restype = CFIndex

    CFArrayGetValueAtIndex = MultitouchSupport.CFArrayGetValueAtIndex
    CFArrayGetValueAtIndex.argtypes = [CFArrayRef, CFIndex]
    CFArrayGetValueAtIndex.restype = ctypes.c_void_p

    MTDeviceCreateList = MultitouchSupport.MTDeviceCreateList
    MTDeviceCreateList.argtypes = []
    MTDeviceCreateList.restype = CFMutableArrayRef

    class MTPoint(ctypes.Structure):
        _fields_ = [('x', ctypes.c_float),
                    ('y', ctypes.c_float)]

    class MTVector(ctypes.Structure):
        _fields_ = [('position', MTPoint),
                    ('velocity', MTPoint)]

    class MTData(ctypes.Structure):
        _fields_ = [
                    ('frame', ctypes.c_int),
                    ('timestamp', ctypes.c_double),
                    ('identifier', ctypes.c_int),
                    # Current state (of unknown meaning).
                    ('state', ctypes.c_int),
                    ('unknown1', ctypes.c_int),
                    ('unknown2', ctypes.c_int),
                    # Normalized position and vector of the touch (0 to 1)
                    ('normalized', MTVector),
                    # The area of the touch.
                    ('size', ctypes.c_float),
                    ('unknown3', ctypes.c_int),
                    # The following three define the ellipsoid of a finger.
                    ('angle', ctypes.c_float),
                    ('major_axis', ctypes.c_float),
                    ('minor_axis', ctypes.c_float),
                    ('unknown4', MTVector),
                    ('unknown5_1', ctypes.c_int),
                    ('unknown5_2', ctypes.c_int),
                    ('unknown6', ctypes.c_float),
	]

        MTDataRef = ctypes.POINTER(MTData)

        MTContactCallbackFunction = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, MTDataRef,
                                        ctypes.c_int, ctypes.c_double, ctypes.c_int)

        MTDeviceRef = ctypes.c_void_p

        MTRegisterContactFrameCallback = MultitouchSupport.MTRegisterContactFrameCallback
        MTRegisterContactFrameCallback.argtypes = [MTDeviceRef, MTContactCallbackFunction]
        MTRegisterContactFrameCallback.restype = None

        MTDeviceStart = MultitouchSupport.MTDeviceStart
        MTDeviceStart.argtypes = [MTDeviceRef, ctypes.c_int]
        MTDeviceStart.restype = None

else:
	MTContactCallbackFunction = lambda x: None


class MacTouch(Touch):
    '''Touch representing a contact point on touchpad. Support pos and shape
    profile'''

    def depack(self, args):
        self.shape = TouchShapeRect()
        self.sx, self.sy = args[0], args[1]
        self.shape.width = args[2]
        self.shape.height = args[2]
        self.profile = ('pos', 'shape')
        super(MacTouch, self).depack(args)

    def __str__(self):
        return '<MacTouch id=%d pos=(%f, %f) device=%s>' % (self.id, self.sx, self.sy, self.device)

_instance = None

class MacTouchProvider(TouchProvider):

    def __init__(self, *largs, **kwargs):
        global _instance
        if _instance is not None:
            raise Exception('Only one MacTouch provider is allowed.')
        _instance = self
        super(MacTouchProvider, self).__init__(*largs, **kwargs)

    def start(self):
        # global uid
        self.uid = 0
        # touches will be per devices
        self.touches = {}
        # lock needed to access on uid
        self.lock = threading.Lock()
        # event queue to dispatch in main thread
        self.queue = collections.deque()

        # ok, listing devices, and attach !
        devices = MultitouchSupport.MTDeviceCreateList()
        num_devices = CFArrayGetCount(devices)
        print 'num_devices =', num_devices
        for i in xrange(num_devices):
            device = CFArrayGetValueAtIndex(devices, i)
            print 'device #%d: %016x' % (i, device)
            # create touch dict for this device
            data_id = str(device)
            self.touches[data_id] = {}
            # start !
            MTRegisterContactFrameCallback(device, self._mts_callback)
            MTDeviceStart(device, 0)

    def update(self, dispatch_fn):
        # dispatch all event from threads
        try:
            while True:
                event_type, touch = self.queue.popleft()
                dispatch_fn(event_type, touch)
        except:
            pass

    def stop(self):
        # i don't known how to stop it...
        pass

    @MTContactCallbackFunction
    def _mts_callback(device, data_ptr, n_fingers, timestamp, frame):
        global _instance
        devid = str(device)

        # XXX create live touch, we get one case that
        # the device announced by macosx don't match the device
        # in _mts_callback....
        if not devid in _instance.touches:
            _instance.touches[devid] = {}

        touches = _instance.touches[devid]
        actives = []

        for i in xrange(n_fingers):
            # get pointer on data
            data = data_ptr[i]

            # add this touch as an active touch
            actives.append(data.identifier)

            # extract identifier
            data_id = data.identifier

            # prepare argument position
            args = (data.normalized.position.x, data.normalized.position.y, data.size)

            if not data_id in touches:
                # increment uid
                _instance.lock.acquire()
                _instance.uid += 1
                # create a touch
                touch = MacTouch(_instance.device, _instance.uid, args)
                _instance.lock.release()
                # create event
                _instance.queue.append(('down', touch))
                # store touch
                touches[data_id] = touch
            else:
                touch = touches[data_id]
                # check if he really moved
                if data.normalized.position.x == touch.sx and \
                   data.normalized.position.y == touch.sy:
                    continue
                touch.move(args)
                _instance.queue.append(('move', touch))

        # delete old touchs
        for tid in touches.keys()[:]:
            if tid not in actives:
                touch = touches[tid]
                _instance.queue.append(('up', touch))
                del touches[tid]

        return 0

TouchFactory.register('mactouch', MacTouchProvider)

