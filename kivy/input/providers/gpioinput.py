# coding utf-8
from __future__ import print_function, division

'''
Support for GPIO input from the linux kernel using gpio devtree
==================================================

To configure GPIOInput, add this to your configuration::

    [input]
    # devicename = gpioinput,/dev/input/eventXX,[accel_time=xx(ms)]
    # example with Rotary Encoder for volume
    volume = gpioinput,/dev/input/event2

.. note::
    You must have read access to the input event.

.. versionadded:: NOT RELEASED

'''

__all__ = ('GPIOEventProvider', 'GPIOEvent')

import os
from collections import defaultdict

import threading
import collections
import struct
import fcntl
from kivy.input.provider import MotionEventProvider
from kivy.input.factory import MotionEventFactory
from kivy.input.motionevent import MotionEvent
from kivy.input.shape import ShapeRect
from kivy.logger import Logger

Window = None

#
# This part is taken from linux-source-2.6.32/include/linux/input.h
#

# Event types
EV_SYN = 0x00
EV_KEY = 0x01
EV_REL = 0x02
EV_ABS = 0x03
EV_MSC = 0x04
EV_SW = 0x05
EV_LED = 0x11
EV_SND = 0x12
EV_REP = 0x14
EV_FF = 0x15
EV_PWR = 0x16
EV_FF_STATUS = 0x17
EV_MAX = 0x1f
EV_CNT = (EV_MAX + 1)

KEY_MAX = 0x2ff

# Synchronization events
SYN_REPORT = 0
SYN_CONFIG = 1
SYN_MT_REPORT = 2

# Misc events
MSC_SERIAL = 0x00
MSC_PULSELED = 0x01
MSC_GESTURE = 0x02
MSC_RAW = 0x03
MSC_SCAN = 0x04
MSC_MAX = 0x07
MSC_CNT = (MSC_MAX + 1)

# Relative axis events
REL_X = 0x00
REL_Y = 0x01
REL_Z = 0x02
REL_RX = 0x03
REL_RY = 0x04
REL_RZ = 0x05
REL_HWHEEL = 0x06
REL_DIAL = 0x07
REL_WHEEL = 0x08
REL_MISC = 0x09
REL_MAX = 0x0f
REL_CNT = (REL_MAX + 1)

# some ioctl base (with 0 value)
EVIOCGNAME = 2147501318
EVIOCGBIT = 2147501344
EVIOCGABS = 2149074240

# Relation between rel ev_codes and axis coordinates
AXIS_COORDS = {
    REL_X: 'x',
    REL_Y: 'y',
    REL_Z: 'z',
    REL_RX: 'rx',
    REL_RY: 'ry',
    REL_RZ: 'rz',
    REL_HWHEEL: 'hwheel',
    REL_DIAL: 'dial',
    REL_WHEEL: 'wheel',
}

# sizeof(struct input_event)
struct_input_event_sz = struct.calcsize('LLHHi')
struct_input_absinfo_sz = struct.calcsize('iiiiii')
sz_l = struct.calcsize('Q')


class GPIOEvent(MotionEvent):

    def depack(self, args):
        super(GPIOEvent, self).depack(args)
        for k, v in args.items():
            self.__dict__[k] = v
        if getattr(self, 'is_rotary', False):
            self.profile.append('dial')

    def __str__(self):
        return '<%s id=%d device=%s>' \
            % (self.__class__.__name__, self.id, self.device)


class GPIOEventProvider(MotionEventProvider):

    options = {
    }

    def __init__(self, device, args):
        super(GPIOEventProvider, self).__init__(device, args)
        global Window
        if Window is None:
            from kivy.core.window import Window

        self.input_fn = None
        self.device_name = None

        # Accumulated info for any axis
        # TODO: Get REL codes from device capabilities
        self._axis_info = {AXIS_COORDS[ev_code]: 0
                           for ev_code in AXIS_COORDS.keys()}
        self._pending_axis = set()

        # split arguments
        args = args.split(',')

        # read filename
        self.input_fn = args[0]
        Logger.info('GPIOInput: Read event from <%s>' % self.input_fn)

        options = dict(self.options)
        for arg in args[1:]:
            try:
                arg_name, arg_value = arg.split('=')
            except ValueError:
                Logger.warning(
                    "GPIOInput: <%s> Wrong option '%s'."
                    % (self.device, arg))
                continue

            if arg_name in self.options.keys():
                Logger.info(
                    "GPIOInput: <%s> Set option %s to %s"
                    % (self.device, arg_name, arg_value))
                options[arg_name] = arg_value
            else:
                Logger.warning("GPIOInput: <%s> Option '%s' not available."
                               % (self.device_name, arg_name))
                continue

        for op_name, op_value in options.iteritems():
            self.__dict__[op_name] = op_value

    def start(self):
        if self.input_fn is None:
            return
        self.uid = 0
        self.dispatch_queue = []
        self.thread = threading.Thread(
            target=self._thread_run,
            kwargs=dict(
                input_fn=self.input_fn,
                device=self.device))
        self.thread.daemon = True
        self.thread.start()

    def _thread_run(self, **kwargs):

        def process_as_rotary(tv_sec, tv_usec, ev_type, ev_code, ev_value):

            tv_msec = tv_sec * 1000 + tv_usec / 1000

            if ev_type == EV_SYN:
                if ev_code == SYN_REPORT:
                    if not self._pending_axis:
                        return

                    ev_props = {'push_attrs': list(self._pending_axis),
                                'is_touch': False,
                                'is_rotary': True}
                    for ax_coord in self._pending_axis:
                        ev_props[ax_coord] = self._axis_info[ax_coord]
                        self._axis_info[ax_coord] = 0

                    Logger.trace(
                        "GPIOInput:(%0.3f) <%s>[<EV_SYN>,<SYN_REPORT>] %s"
                        % (tv_msec / 1000, self.device, ev_props))

                    self.dispatch_queue.append(
                        GPIOEvent(self.device,
                                  'GPIOEvent_%d' % tv_msec,
                                  ev_props))
                    self._pending_axis.clear()

            elif ev_type == EV_REL:
                ax_coord = AXIS_COORDS[ev_code]
                self._axis_info[ax_coord] += ev_value
                self._pending_axis.add(ax_coord)

                Logger.trace(
                    "GPIOInput:(%0.3f)<%s>[<EV_REL>,AXIS %d(%s),VALUE %d]"
                    % (tv_msec / 1000, self.device, ev_code, ax_coord,
                       ev_value))

        # open the input
        fd = open(self.input_fn, 'rb')

        # get the controller name (EVIOCGNAME)
        self.device_name = str(fcntl.ioctl(fd,
                                           EVIOCGNAME + (256 << 16),
                                           " " * 256)
                               ).split('\x00')[0]

        Logger.info('GPIOEvent: using <%s> as <%s>' %
                    (self.device_name, self.device))

        # read until the end
        while fd:

            data = fd.read(struct_input_event_sz)
            if len(data) < struct_input_event_sz:
                break

            # extract each event
            for i in range(int(len(data) / struct_input_event_sz)):
                ev = data[i * struct_input_event_sz:]
                # extract timeval + event infos
                infos = struct.unpack('LLHHi', ev[:struct_input_event_sz])
                process_as_rotary(*infos)

    def update(self, dispatch_fn):
        # dispatch all events from threads

        try:
            while True:
                me = self.dispatch_queue.pop(0)
                Window.dispatch('on_motion', 'begin', me)
                Logger.trace('GPIOEvent: dispatching %r' % me)
        except IndexError:
            pass


if 'KIVY_DOC' in os.environ:
    # documentation hack
    GPIOEventProvider = None
else:
    MotionEventFactory.register('gpioinput', GPIOEventProvider)
