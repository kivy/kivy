# coding utf-8
'''
Native support for HID input from the linux kernel
==================================================

Support starts from 2.6.32-ubuntu, or 2.6.34.

To configure HIDInput, add this to your configuration::

    [input]
    # devicename = hidinput,/dev/input/eventXX
    # example with Stantum MTP4.3" screen
    stantum = hidinput,/dev/input/event2

.. note::
    You must have read access to the input event.

You can use a custom range for the X, Y and pressure values.
For some drivers, the range reported is invalid.
To fix that, you can add these options to the argument line:

* invert_x : 1 to invert X axis
* invert_y : 1 to invert Y axis
* min_position_x : X minimum
* max_position_x : X maximum
* min_position_y : Y minimum
* max_position_y : Y maximum
* min_pressure : pressure minimum
* max_pressure : pressure maximum
* rotation : rotate the input coordinate (0, 90, 180, 270)

For example, on the Asus T101M, the touchscreen reports a range from 0-4095 for
the X and Y values, but the real values are in a range from 0-32768. To correct
this, you can add the following to the configuration::

    [input]
    t101m = hidinput,/dev/input/event7,max_position_x=32768,\
max_position_y=32768

.. versionadded:: 1.9.1

    `rotation` configuration token added.

'''

__all__ = ('HIDInputMotionEventProvider', 'HIDMotionEvent')

import os
from kivy.input.motionevent import MotionEvent
from kivy.input.shape import ShapeRect
# late imports
Window = None
Keyboard = None


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

    ABS_X = 0x00
    ABS_Y = 0x01
    ABS_PRESSURE = 0x18
    ABS_MT_TOUCH_MAJOR = 0x30  # Major axis of touching ellipse
    ABS_MT_TOUCH_MINOR = 0x31  # Minor axis (omit if circular)
    ABS_MT_WIDTH_MAJOR = 0x32  # Major axis of approaching ellipse
    ABS_MT_WIDTH_MINOR = 0x33  # Minor axis (omit if circular)
    ABS_MT_ORIENTATION = 0x34  # Ellipse orientation
    ABS_MT_POSITION_X = 0x35   # Center X ellipse position
    ABS_MT_POSITION_Y = 0x36   # Center Y ellipse position
    ABS_MT_TOOL_TYPE = 0x37    # Type of touching device
    ABS_MT_BLOB_ID = 0x38      # Group a set of packets as a blob
    ABS_MT_TRACKING_ID = 0x39  # Unique ID of initiated contact
    ABS_MT_PRESSURE = 0x3a     # Pressure on contact area

    # some ioctl base (with 0 value)
    EVIOCGNAME = 2147501318
    EVIOCGBIT = 2147501344
    EVIOCGABS = 2149074240

    keyboard_keys = {
        0x29: ('`', '~'),
        0x02: ('1', '!'),
        0x03: ('2', '@'),
        0x04: ('3', '#'),
        0x05: ('4', '$'),
        0x06: ('5', '%'),
        0x07: ('6', '^'),
        0x08: ('7', '&'),
        0x09: ('8', '*'),
        0x0a: ('9', '('),
        0x0b: ('0', ')'),
        0x0c: ('-', '_'),
        0x0d: ('=', '+'),
        0x0e: ('backspace', ),
        0x0f: ('tab', ),
        0x10: ('q', 'Q'),
        0x11: ('w', 'W'),
        0x12: ('e', 'E'),
        0x13: ('r', 'R'),
        0x14: ('t', 'T'),
        0x15: ('y', 'Y'),
        0x16: ('u', 'U'),
        0x17: ('i', 'I'),
        0x18: ('o', 'O'),
        0x19: ('p', 'P'),
        0x1a: ('[', '{'),
        0x1b: (']', '}'),
        0x2b: ('\\', '|'),
        0x3a: ('capslock', ),
        0x1e: ('a', 'A'),
        0x1f: ('s', 'S'),
        0x20: ('d', 'D'),
        0x21: ('f', 'F'),
        0x22: ('g', 'G'),
        0x23: ('h', 'H'),
        0x24: ('j', 'J'),
        0x25: ('k', 'K'),
        0x26: ('l', 'L'),
        0x27: (';', ':'),
        0x28: ("'", '"'),
        0xff: ('non-US-1', ),
        0x1c: ('enter', ),
        0x2a: ('shift', ),
        0x2c: ('z', 'Z'),
        0x2d: ('x', 'X'),
        0x2e: ('c', 'C'),
        0x2f: ('v', 'V'),
        0x30: ('b', 'B'),
        0x31: ('n', 'N'),
        0x32: ('m', 'M'),
        0x33: (',', '<'),
        0x34: ('.', '>'),
        0x35: ('/', '?'),
        0x36: ('shift', ),
        0x56: ('pipe', ),
        0x1d: ('ctrl', ),
        0x7D: ('super', ),
        0x38: ('alt', ),
        0x39: ('spacebar', ),
        0x64: ('alt-gr', ),
        0x7e: ('super', ),
        0x7f: ('compose', ),
        0x61: ('ctrl', ),
        0x45: ('numlock', ),
        0x47: ('numpad7', 'home'),
        0x4b: ('numpad4', 'left'),
        0x4f: ('numpad1', 'end'),
        0x48: ('numpad8', 'up'),
        0x4c: ('numpad5', ),
        0x50: ('numpad2', 'down'),
        0x52: ('numpad0', 'insert'),
        0x37: ('numpadmul', ),
        0x62: ('numpaddivide', ),
        0x49: ('numpad9', 'pageup'),
        0x4d: ('numpad6', 'right'),
        0x51: ('numpad3', 'pagedown'),
        0x53: ('numpaddecimal', 'delete'),
        0x4a: ('numpadsubstract', ),
        0x4e: ('numpadadd', ),
        0x60: ('numpadenter', ),
        0x01: ('escape', ),
        0x3b: ('f1', ),
        0x3c: ('f2', ),
        0x3d: ('f3', ),
        0x3e: ('f4', ),
        0x3f: ('f5', ),
        0x40: ('f6', ),
        0x41: ('f7', ),
        0x42: ('f8', ),
        0x43: ('f9', ),
        0x44: ('f10', ),
        0x57: ('f11', ),
        0x58: ('f12', ),
        0x54: ('Alt+SysRq', ),
        0x46: ('Screenlock', ),
        0x67: ('up', ),
        0x6c: ('down', ),
        0x69: ('left', ),
        0x6a: ('right', ),
        0x6e: ('insert', ),
        0x6f: ('delete', ),
        0x66: ('home', ),
        0x6b: ('end', ),
        0x68: ('pageup', ),
        0x6d: ('pagedown', ),
        0x63: ('print', ),
        0x77: ('pause', ),


        # TODO combinations
        # e0-37    PrtScr
        # e0-46    Ctrl+Break
        # e0-5b    LWin (USB: LGUI)
        # e0-5c    RWin (USB: RGUI)
        # e0-5d    Menu
        # e0-5f    Sleep
        # e0-5e    Power
        # e0-63    Wake
        # e0-38    RAlt
        # e0-1d    RCtrl
        # e0-52    Insert
        # e0-53    Delete
        # e0-47    Home
        # e0-4f    End
        # e0-49    PgUp
        # e0-51    PgDn
        # e0-4b    Left
        # e0-48    Up
        # e0-50    Down
        # e0-4d    Right
        # e0-35    KP-/
        # e0-1c    KP-Enter
        # e1-1d-45 77      Pause
    }

    keys_str = {
        'spacebar': ' ',
        'tab': '	',
        'shift': '',
        'alt': '',
        'ctrl': '',
        'escape': '',
        'numpad1': '1',
        'numpad2': '2',
        'numpad3': '3',
        'numpad4': '4',
        'numpad5': '5',
        'numpad6': '6',
        'numpad7': '7',
        'numpad8': '8',
        'numpad9': '9',
        'numpad0': '0',
        'numpadmul': '*',
        'numpaddivide': '/',
        'numpadadd': '+',
        'numpadsubstract': '-',
    }

    # sizeof(struct input_event)
    struct_input_event_sz = struct.calcsize('LLHHi')
    struct_input_absinfo_sz = struct.calcsize('iiiiii')
    sz_l = struct.calcsize('Q')

    class HIDInputMotionEventProvider(MotionEventProvider):

        options = ('min_position_x', 'max_position_x',
                   'min_position_y', 'max_position_y',
                   'min_pressure', 'max_pressure',
                   'invert_x', 'invert_y', 'rotation')

        def __init__(self, device, args):
            super(HIDInputMotionEventProvider, self).__init__(device, args)
            global Window, Keyboard

            if Window is None:
                from kivy.core.window import Window
            if Keyboard is None:
                from kivy.core.window import Keyboard

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
                    err = 'HIDInput: invalid value "%s" for "%s"' % (
                        key, value)
                    Logger.error(err)
                    continue

                # all good!
                Logger.info('HIDInput: Set custom %s to %d' % (
                    key, int(value)))

            if 'rotation' not in self.default_ranges:
                self.default_ranges['rotation'] = 0
            elif self.default_ranges['rotation'] not in (0, 90, 180, 270):
                Logger.error('HIDInput: invalid rotation value ({})'.format(
                    self.default_ranges['rotation']))
                self.default_ranges['rotation'] = 0

        def start(self):
            if self.input_fn is None:
                return
            self.uid = 0
            self.queue = collections.deque()
            self.dispatch_queue = []
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
            queue = self.queue
            dispatch_queue = self.dispatch_queue
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
            range_min_abs_x = 0
            range_max_abs_x = 255
            range_min_abs_y = 0
            range_max_abs_y = 255
            range_min_abs_pressure = 0
            range_max_abs_pressure = 255
            invert_x = int(bool(drs('invert_x', 0)))
            invert_y = int(bool(drs('invert_y', 1)))
            rotation = drs('rotation', 0)

            def assign_coord(point, value, invert, coords):
                cx, cy = coords
                if invert:
                    value = 1. - value
                if rotation == 0:
                    point[cx] = value
                elif rotation == 90:
                    point[cy] = value
                elif rotation == 180:
                    point[cx] = 1. - value
                elif rotation == 270:
                    point[cy] = 1. - value

            def assign_rel_coord(point, value, invert, coords):
                cx, cy = coords
                if invert:
                    value = -1 * value
                if rotation == 0:
                    point[cx] += value
                elif rotation == 90:
                    point[cy] += value
                elif rotation == 180:
                    point[cx] += -value
                elif rotation == 270:
                    point[cy] += -value

            def process_as_multitouch(tv_sec, tv_usec, ev_type,
                                      ev_code, ev_value):
                # sync event
                if ev_type == EV_SYN:
                    if ev_code == SYN_MT_REPORT:
                        if 'id' not in point:
                            return
                        l_points.append(point.copy())
                    elif ev_code == SYN_REPORT:
                        process(l_points)
                        del l_points[:]

                elif ev_type == EV_MSC and ev_code in (MSC_RAW, MSC_SCAN):
                    pass

                else:
                    # compute multitouch track
                    if ev_code == ABS_MT_TRACKING_ID:
                        point.clear()
                        point['id'] = ev_value
                    elif ev_code == ABS_MT_POSITION_X:
                        val = normalize(ev_value,
                                        range_min_position_x,
                                        range_max_position_x)
                        assign_coord(point, val, invert_x, 'xy')
                    elif ev_code == ABS_MT_POSITION_Y:
                        val = 1. - normalize(ev_value,
                                             range_min_position_y,
                                             range_max_position_y)
                        assign_coord(point, val, invert_y, 'yx')
                    elif ev_code == ABS_MT_ORIENTATION:
                        point['orientation'] = ev_value
                    elif ev_code == ABS_MT_BLOB_ID:
                        point['blobid'] = ev_value
                    elif ev_code == ABS_MT_PRESSURE:
                        point['pressure'] = normalize(ev_value,
                                                      range_min_pressure,
                                                      range_max_pressure)
                    elif ev_code == ABS_MT_TOUCH_MAJOR:
                        point['size_w'] = ev_value
                    elif ev_code == ABS_MT_TOUCH_MINOR:
                        point['size_h'] = ev_value

            def process_as_mouse_or_keyboard(
                tv_sec, tv_usec, ev_type, ev_code, ev_value):
                if ev_type == EV_SYN:
                    if ev_code == SYN_REPORT:
                        process([point])
                elif ev_type == EV_REL:
                    if ev_code == 0:
                        assign_rel_coord(point,
                            min(1., max(-1., ev_value / 1000.)),
                            invert_x, 'xy')
                    elif ev_code == 1:
                        assign_rel_coord(point,
                            min(1., max(-1., ev_value / 1000.)),
                            invert_y, 'yx')
                elif ev_type != EV_KEY:
                    if ev_code == ABS_X:
                        val = normalize(ev_value,
                                        range_min_abs_x,
                                        range_max_abs_x)
                        assign_coord(point, val, invert_x, 'xy')
                    elif ev_code == ABS_Y:
                        val = 1. - normalize(ev_value,
                                             range_min_abs_y,
                                             range_max_abs_y)
                        assign_coord(point, val, invert_y, 'yx')
                    elif ev_code == ABS_PRESSURE:
                        point['pressure'] = normalize(ev_value,
                                                      range_min_abs_pressure,
                                                      range_max_abs_pressure)
                else:
                    buttons = {
                        272: 'left',
                        273: 'right',
                        274: 'middle',
                        275: 'side',
                        276: 'extra',
                        277: 'forward',
                        278: 'back',
                        279: 'task',
                        330: 'touch',
                        320: 'pen'}

                    if ev_code in buttons.keys():
                        if ev_value:
                            if 'button' not in point:
                                point['button'] = buttons[ev_code]
                                point['id'] += 1
                                if '_avoid' in point:
                                    del point['_avoid']
                        elif 'button' in point:
                            if point['button'] == buttons[ev_code]:
                                del point['button']
                                point['id'] += 1
                                point['_avoid'] = True
                    else:
                        if ev_value == 1:
                            z = keyboard_keys[ev_code][-1
                                if 'shift' in Window._modifiers else 0]
                            if z == 'shift' or z == 'alt':
                                Window._modifiers.append(z)
                            dispatch_queue.append(('key_down', (
                                Keyboard.keycodes[z.lower()], ev_code,
                                keys_str.get(z, z), Window._modifiers)))
                        elif ev_value == 0:
                            z = keyboard_keys[ev_code][-1
                                if 'shift' in Window._modifiers else 0]
                            dispatch_queue.append(('key_up', (
                                Keyboard.keycodes[z.lower()], ev_code,
                                keys_str.get(z, z), Window._modifiers)))
                            if z == 'shift':
                                Window._modifiers.remove('shift')

            def process(points):
                if not is_multitouch:
                    dispatch_queue.append(('mouse_pos', (
                        points[0]['x'] * Window.width,
                        points[0]['y'] * Window.height)))

                actives = [args['id']
                           for args in points
                           if 'id' in args and '_avoid' not in args]
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
                        if '_avoid' not in args:
                            touch = HIDMotionEvent(device, tid, args)
                            touches[touch.id] = touch
                            if tid not in touches_sent:
                                queue.append(('begin', touch))
                                touches_sent.append(tid)

                for tid in list(touches.keys())[:]:
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
            device_name = str(fcntl.ioctl(fd, EVIOCGNAME + (256 << 16),
                                      " " * 256)).split('\x00')[0]
            Logger.info('HIDMotionEvent: using <%s>' % device_name)

            # get abs infos
            bit = fcntl.ioctl(fd, EVIOCGBIT + (EV_MAX << 16), ' ' * sz_l)
            bit, = struct.unpack('Q', bit)
            is_multitouch = False
            for x in range(EV_MAX):
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
                for y in range(KEY_MAX):
                    if (sbit & (1 << y)) == 0:
                        continue
                    absinfo = fcntl.ioctl(fd, EVIOCGABS + y +
                                          (struct_input_absinfo_sz << 16),
                                          ' ' * struct_input_absinfo_sz)
                    abs_value, abs_min, abs_max, abs_fuzz, \
                        abs_flat, abs_res = struct.unpack('iiiiii', absinfo)
                    if y == ABS_MT_POSITION_X:
                        is_multitouch = True
                        range_min_position_x = drs('min_position_x', abs_min)
                        range_max_position_x = drs('max_position_x', abs_max)
                        Logger.info('HIDMotionEvent: ' +
                                    '<%s> range position X is %d - %d' % (
                                        device_name, abs_min, abs_max))
                    elif y == ABS_MT_POSITION_Y:
                        is_multitouch = True
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
                    elif y == ABS_X:
                        range_min_abs_x = drs('min_abs_x', abs_min)
                        range_max_abs_x = drs('max_abs_x', abs_max)
                        Logger.info('HIDMotionEvent: ' +
                                    '<%s> range ABS X position is %d - %d' % (
                                        device_name, abs_min, abs_max))
                    elif y == ABS_Y:
                        range_min_abs_y = drs('min_abs_y', abs_min)
                        range_max_abs_y = drs('max_abs_y', abs_max)
                        Logger.info('HIDMotionEvent: ' +
                                    '<%s> range ABS Y position is %d - %d' % (
                                        device_name, abs_min, abs_max))
                    elif y == ABS_PRESSURE:
                        range_min_abs_pressure = drs(
                            'min_abs_pressure', abs_min)
                        range_max_abs_pressure = drs(
                            'max_abs_pressure', abs_max)
                        Logger.info('HIDMotionEvent: ' +
                                    '<%s> range ABS pressure is %d - %d' % (
                                        device_name, abs_min, abs_max))

            # init the point
            if not is_multitouch:
                point = {'x': .5, 'y': .5, 'id': 0, '_avoid': True}

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

                    if is_multitouch:
                        process_as_multitouch(*infos)
                    else:
                        process_as_mouse_or_keyboard(*infos)

        def update(self, dispatch_fn):
            # dispatch all events from threads
            dispatch_queue = self.dispatch_queue
            n = len(dispatch_queue)
            for name, args in dispatch_queue[:n]:
                if name == 'mouse_pos':
                    Window.mouse_pos = args
                elif name == 'key_down':
                    if not Window.dispatch('on_key_down', *args):
                        Window.dispatch('on_keyboard', *args)
                elif name == 'key_up':
                    Window.dispatch('on_key_up', *args)
            del dispatch_queue[:n]

            try:
                while True:
                    event_type, touch = self.queue.popleft()
                    dispatch_fn(event_type, touch)
            except:
                pass

    MotionEventFactory.register('hidinput', HIDInputMotionEventProvider)
