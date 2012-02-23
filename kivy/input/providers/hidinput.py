'''
Native support of HID input from linux kernel
=============================================

Support start from 2.6.32-ubuntu, or 2.6.34.

To configure HIDInput, put in your configuration ::

    [input]
    # devicename = hidinput,/dev/input/eventXX
    # example with Stantum MTP4.3" screen
    stantum = hidinput,/dev/input/event2

.. note::
    You must have read access to the input event.

You have the possibility to use custom range for some X, Y and pressure value.
On some drivers, the range reported is invalid.
To fix that, you can add one of theses options on the argument line :

* invert_x : 1 to invert X axis
* invert_y : 1 to invert Y axis
* min_position_x : X minimum
* max_position_x : X maximum
* min_position_y : Y minimum
* max_position_y : Y maximum
* min_pressure : pressure minimum
* max_pressure : pressure maximum

For example, on Asus T101M, the touchscreen report a range from 0-4095 for X and
Y value, but real value are in a range from 0-32768. You can put it on
configuration ::

    [input]
    t101m = hidinput,/dev/input/event7,max_position_x=32768,max_position_y=32768

'''

__all__ = ('HIDInputMotionEventProvider', 'HIDMotionEvent')

import os
from kivy.input.motionevent import MotionEvent
from kivy.input.shape import ShapeRect


class HIDMotionEvent(MotionEvent):

    def depack(self, args):
        self.is_touch = True
        self.sx = args['x']
        self.sy = args['y']
        self.profile = ['pos']
        if 'size_w' in args and 'size_h' in args:
            self.shape = ShapeRect()
            self.shape.width = args['size_w']
            self.shape.height = args['size_h']
            self.profile.append('shape')
        if 'pressure' in args:
            self.pressure = args['pressure']
            self.profile.append('pressure')
        super(HIDMotionEvent, self).depack(args)

    def __str__(self):
        return '<HIDMotionEvent id=%d pos=(%f, %f) device=%s>' \
            % (self.id, self.sx, self.sy, self.device)

if 'KIVY_DOC' in os.environ:
    # documentation hack
    HIDInputMotionEventProvider = None

else:
    import threading
    import collections
    import struct
    import fcntl
    from kivy.input.provider import MotionEventProvider
    from kivy.input.factory import MotionEventFactory
    from kivy.logger import Logger

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
    EV_CNT = (EV_MAX+1)

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
    MSC_CNT = (MSC_MAX+1)

    ABS_MT_TOUCH_MAJOR = 0x30	# Major axis of touching ellipse
    ABS_MT_TOUCH_MINOR = 0x31	# Minor axis (omit if circular)
    ABS_MT_WIDTH_MAJOR = 0x32	# Major axis of approaching ellipse
    ABS_MT_WIDTH_MINOR = 0x33	# Minor axis (omit if circular)
    ABS_MT_ORIENTATION = 0x34	# Ellipse orientation
    ABS_MT_POSITION_X = 0x35	# Center X ellipse position
    ABS_MT_POSITION_Y = 0x36	# Center Y ellipse position
    ABS_MT_TOOL_TYPE = 0x37	# Type of touching device
    ABS_MT_BLOB_ID = 0x38	# Group a set of packets as a blob
    ABS_MT_TRACKING_ID = 0x39	# Unique ID of initiated contact
    ABS_MT_PRESSURE = 0x3a	# Pressure on contact area

    # some ioctl base (with 0 value)
    EVIOCGNAME = 2147501318
    EVIOCGBIT = 2147501344
    EVIOCGABS = 2149074240

    # sizeof(struct input_event)
    struct_input_event_sz = struct.calcsize('LLHHi')
    struct_input_absinfo_sz = struct.calcsize('iiiiii')
    sz_l = struct.calcsize('Q')

    class HIDInputMotionEventProvider(MotionEventProvider):

        options = ('min_position_x', 'max_position_x',
                   'min_position_y', 'max_position_y',
                   'min_pressure', 'max_pressure',
                   'invert_x', 'invert_y')

        def __init__(self, device, args):
            super(HIDInputMotionEventProvider, self).__init__(device, args)
            self.input_fn = None
            self.default_ranges = dict()

            # split arguments
            args = args.split(',')
            if not args:
                Logger.error('HIDInput: Filename missing in configuration')
                Logger.error('HIDInput: Use /dev/input/event0 for example')
                return None

            # read filename
            self.input_fn = args[0]
            Logger.info('HIDInput: Read event from <%s>' % self.input_fn)

            # read parameters
            for arg in args[1:]:
                if arg == '':
                    continue
                arg = arg.split('=')

                # ensure it's a key = value
                if len(arg) != 2:
                    Logger.error('HIDInput: invalid parameter '
                                 '%s, not in key=value format.' % arg)
                    continue

                # ensure the key exist
                key, value = arg
                if key not in HIDInputMotionEventProvider.options:
                    Logger.error('HIDInput: unknown %s option' % key)
                    continue

                # ensure the value
                try:
                    self.default_ranges[key] = int(value)
                except ValueError:
                    err = 'HIDInput: invalid value "%s" for "%s"' % (key, value)
                    Logger.error(err)
                    continue

                # all good!
                Logger.info('HIDInput: Set custom %s to %d' % (key, int(value)))

        def start(self):
            if self.input_fn is None:
                return
            self.uid = 0
            self.queue = collections.deque()
            self.thread = threading.Thread(
                target=self._thread_run,
                kwargs=dict(
                    queue=self.queue,
                    input_fn=self.input_fn,
                    device=self.device,
                    default_ranges=self.default_ranges))
            self.thread.daemon = True
            self.thread.start()

        def _thread_run(self, **kwargs):
            input_fn = kwargs.get('input_fn')
            queue = kwargs.get('queue')
            device = kwargs.get('device')
            drs = kwargs.get('default_ranges').get
            touches = {}
            touches_sent = []
            point = {}
            l_points = []

            # prepare some vars to get limit of some component
            range_min_position_x = 0
            range_max_position_x = 2048
            range_min_position_y = 0
            range_max_position_y = 2048
            range_min_pressure = 0
            range_max_pressure = 255
            invert_x = int(bool(drs('invert_x', 0)))
            invert_y = int(bool(drs('invert_y', 0)))

            def process(points):
                actives = [args['id'] for args in points]
                for args in points:
                    tid = args['id']
                    try:
                        touch = touches[tid]
                        if touch.sx == args['x'] and touch.sy == args['y']:
                            continue
                        touch.move(args)
                        if tid not in touches_sent:
                            queue.append(('begin', touch))
                            touches_sent.append(tid)
                        queue.append(('update', touch))
                    except KeyError:
                        touch = HIDMotionEvent(device, tid, args)
                        touches[touch.id] = touch

                for tid in touches.keys()[:]:
                    if tid not in actives:
                        touch = touches[tid]
                        if tid in touches_sent:
                            touch.update_time_end()
                            queue.append(('end', touch))
                            touches_sent.remove(tid)
                        del touches[tid]

            def normalize(value, vmin, vmax):
                return (value - vmin) / float(vmax - vmin)

            # open the input
            fd = open(input_fn, 'rb')

            # get the controler name (EVIOCGNAME)
            device_name = fcntl.ioctl(fd, EVIOCGNAME + (256 << 16),
                " " * 256).split('\x00')[0]
            Logger.info('HIDMotionEvent: using <%s>' % device_name)

            # get abs infos
            bit = fcntl.ioctl(fd, EVIOCGBIT + (EV_MAX << 16), ' ' * sz_l)
            bit, = struct.unpack('Q', bit)
            for x in xrange(EV_MAX):
                # preserve this, we may want other things than EV_ABS
                if x != EV_ABS:
                    continue
                # EV_ABS available for this device ?
                if (bit & (1 << x)) == 0:
                    continue
                # ask abs info keys to the devices
                sbit = fcntl.ioctl(fd, EVIOCGBIT + x + (KEY_MAX << 16),
                                    ' ' * sz_l)
                sbit, = struct.unpack('Q', sbit)
                for y in xrange(KEY_MAX):
                    if (sbit & (1 << y)) == 0:
                        continue
                    absinfo = fcntl.ioctl(fd, EVIOCGABS + y +
                                          (struct_input_absinfo_sz << 16),
                                          ' ' * struct_input_absinfo_sz)
                    abs_value, abs_min, abs_max, abs_fuzz, \
                        abs_flat, abs_res = struct.unpack('iiiiii', absinfo)
                    if y == ABS_MT_POSITION_X:
                        range_min_position_x = drs('min_position_x', abs_min)
                        range_max_position_x = drs('max_position_x', abs_max)
                        Logger.info('HIDMotionEvent: ' +
                            '<%s> range position X is %d - %d' % (
                            device_name, abs_min, abs_max))
                    elif y == ABS_MT_POSITION_Y:
                        range_min_position_y = drs('min_position_y', abs_min)
                        range_max_position_y = drs('max_position_y', abs_max)
                        Logger.info('HIDMotionEvent: ' +
                            '<%s> range position Y is %d - %d' % (
                            device_name, abs_min, abs_max))
                    elif y == ABS_MT_PRESSURE:
                        range_min_pressure = drs('min_pressure', abs_min)
                        range_max_pressure = drs('max_pressure', abs_max)
                        Logger.info('HIDMotionEvent: ' +
                            '<%s> range pressure is %d - %d' % (
                            device_name, abs_min, abs_max))

            # read until the end
            while fd:

                data = fd.read(struct_input_event_sz)
                if len(data) < struct_input_event_sz:
                    break

                # extract each event
                for i in xrange(len(data) / struct_input_event_sz):
                    ev = data[i * struct_input_event_sz:]

                    # extract timeval + event infos
                    tv_sec, tv_usec, ev_type, ev_code, ev_value = \
                            struct.unpack('LLHHi', ev[:struct_input_event_sz])

                    # sync event
                    if ev_type == EV_SYN:
                        if ev_code == SYN_MT_REPORT:
                            if 'id' not in point:
                                continue
                            l_points.append(point)
                        elif ev_code == SYN_REPORT:
                            process(l_points)
                            l_points = []

                    elif ev_type == EV_MSC and ev_code in (MSC_RAW, MSC_SCAN):
                        pass

                    else:
                        # compute multitouch track
                        if ev_code == ABS_MT_TRACKING_ID:
                            point = {}
                            point['id'] = ev_value
                        elif ev_code == ABS_MT_POSITION_X:
                            val = normalize(ev_value,
                                range_min_position_x, range_max_position_x)
                            if invert_x:
                                val = 1. - val
                            point['x'] = val
                        elif ev_code == ABS_MT_POSITION_Y:
                            val = 1. - normalize(ev_value,
                                range_min_position_y, range_max_position_y)
                            if invert_y:
                                val = 1. - val
                            point['y'] = val
                        elif ev_code == ABS_MT_ORIENTATION:
                            point['orientation'] = ev_value
                        elif ev_code == ABS_MT_BLOB_ID:
                            point['blobid'] = ev_value
                        elif ev_code == ABS_MT_PRESSURE:
                            point['pressure'] = normalize(ev_value,
                                range_min_pressure, range_max_pressure)
                        elif ev_code == ABS_MT_TOUCH_MAJOR:
                            point['size_w'] = ev_value
                        elif ev_code == ABS_MT_TOUCH_MINOR:
                            point['size_h'] = ev_value

        def update(self, dispatch_fn):
            # dispatch all event from threads
            try:
                while True:
                    event_type, touch = self.queue.popleft()
                    dispatch_fn(event_type, touch)
            except:
                pass


    MotionEventFactory.register('hidinput', HIDInputMotionEventProvider)
