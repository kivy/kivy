'''
Native support for Multitouch devices on Linux, using libmtdev.
===============================================================

The Mtdev project is a part of the Ubuntu Maverick multitouch architecture.
You can read more on http://wiki.ubuntu.com/Multitouch

To configure MTDev, it's preferable to use probesysfs providers.
Check :py:class:`~kivy.input.providers.probesysfs` for more information.

Otherwise, add this to your configuration::

    [input]
    # devicename = hidinput,/dev/input/eventXX
    acert230h = mtdev,/dev/input/event2

.. note::
    You must have read access to the input event.

You can use a custom range for the X, Y and pressure values.
On some drivers, the range reported is invalid.
To fix that, you can add these options to the argument line:

* invert_x : 1 to invert X axis
* invert_y : 1 to invert Y axis
* min_position_x : X minimum
* max_position_x : X maximum
* min_position_y : Y minimum
* max_position_y : Y maximum
* min_pressure : pressure minimum
* max_pressure : pressure maximum
* min_touch_major : width shape minimum
* max_touch_major : width shape maximum
* min_touch_minor : width shape minimum
* max_touch_minor : height shape maximum
* rotation : 0,90,180 or 270 to rotate
'''

__all__ = ('MTDMotionEventProvider', 'MTDMotionEvent')

import os
import os.path
import time
from kivy.input.motionevent import MotionEvent
from kivy.input.shape import ShapeRect


class MTDMotionEvent(MotionEvent):

    def depack(self, args):
        self.is_touch = True
        if 'x' in args:
            self.sx = args['x']
        else:
            self.sx = -1
        if 'y' in args:
            self.sy = args['y']
        else:
            self.sy = -1
        self.profile = ['pos']
        if 'size_w' in args and 'size_h' in args:
            self.shape = ShapeRect()
            self.shape.width = args['size_w']
            self.shape.height = args['size_h']
            self.profile.append('shape')
        if 'pressure' in args:
            self.pressure = args['pressure']
            self.profile.append('pressure')
        super(MTDMotionEvent, self).depack(args)

    def __str__(self):
        i, sx, sy, d = (self.id, self.sx, self.sy, self.device)
        return '<MTDMotionEvent id=%d pos=(%f, %f) device=%s>' % (i, sx, sy, d)


if 'KIVY_DOC' in os.environ:

    # documentation hack
    MTDMotionEventProvider = None

else:
    import threading
    import collections
    from kivy.lib.mtdev import Device, \
        MTDEV_TYPE_EV_ABS, MTDEV_CODE_SLOT, MTDEV_CODE_POSITION_X, \
        MTDEV_CODE_POSITION_Y, MTDEV_CODE_PRESSURE, \
        MTDEV_CODE_TOUCH_MAJOR, MTDEV_CODE_TOUCH_MINOR, \
        MTDEV_CODE_TRACKING_ID, MTDEV_ABS_POSITION_X, \
        MTDEV_ABS_POSITION_Y, MTDEV_ABS_TOUCH_MINOR, \
        MTDEV_ABS_TOUCH_MAJOR
    from kivy.input.provider import MotionEventProvider
    from kivy.input.factory import MotionEventFactory
    from kivy.logger import Logger

    class MTDMotionEventProvider(MotionEventProvider):

        options = ('min_position_x', 'max_position_x',
                   'min_position_y', 'max_position_y',
                   'min_pressure', 'max_pressure',
                   'min_touch_major', 'max_touch_major',
                   'min_touch_minor', 'max_touch_minor',
                   'invert_x', 'invert_y',
                   'rotation')

        def __init__(self, device, args):
            super(MTDMotionEventProvider, self).__init__(device, args)
            self._device = None
            self.input_fn = None
            self.default_ranges = dict()

            # split arguments
            args = args.split(',')
            if not args:
                Logger.error('MTD: No filename pass to MTD configuration')
                Logger.error('MTD: Use /dev/input/event0 for example')
                return

            # read filename
            self.input_fn = args[0]
            Logger.info('MTD: Read event from <%s>' % self.input_fn)

            # read parameters
            for arg in args[1:]:
                if arg == '':
                    continue
                arg = arg.split('=')

                # ensure it's a key = value
                if len(arg) != 2:
                    err = 'MTD: Bad parameter %s: Not in key=value format' %\
                        arg
                    Logger.error(err)
                    continue

                # ensure the key exist
                key, value = arg
                if key not in MTDMotionEventProvider.options:
                    Logger.error('MTD: unknown %s option' % key)
                    continue

                # ensure the value
                try:
                    self.default_ranges[key] = int(value)
                except ValueError:
                    err = 'MTD: invalid value %s for option %s' % (key, value)
                    Logger.error(err)
                    continue

                # all good!
                Logger.info('MTD: Set custom %s to %d' % (key, int(value)))

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
            l_points = {}

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

            def process(points):
                for args in points:
                    # this can happen if we have a touch going on already at
                    # the start of the app
                    if 'id' not in args:
                        continue
                    tid = args['id']
                    try:
                        touch = touches[tid]
                    except KeyError:
                        touch = MTDMotionEvent(device, tid, args)
                        touches[touch.id] = touch
                    touch.move(args)
                    action = 'update'
                    if tid not in touches_sent:
                        action = 'begin'
                        touches_sent.append(tid)
                    if 'delete' in args:
                        action = 'end'
                        del args['delete']
                        del touches[touch.id]
                        touches_sent.remove(tid)
                        touch.update_time_end()
                    queue.append((action, touch))

            def normalize(value, vmin, vmax):
                try:
                    return (value - vmin) / float(vmax - vmin)
                except ZeroDivisionError:  # it's both in py2 and py3
                    return (value - vmin)

            # open mtdev device
            _fn = input_fn
            _slot = 0
            try:
                _device = Device(_fn)
            except OSError as e:
                if e.errno == 13:  # Permission denied
                    Logger.warn(
                        'MTD: Unable to open device "{0}". Please ensure you'
                        ' have the appropriate permissions.'.format(_fn))
                    return
                else:
                    raise
            _changes = set()

            # prepare some vars to get limit of some component
            ab = _device.get_abs(MTDEV_ABS_POSITION_X)
            range_min_position_x = drs('min_position_x', ab.minimum)
            range_max_position_x = drs('max_position_x', ab.maximum)
            Logger.info('MTD: <%s> range position X is %d - %d' %
                        (_fn, range_min_position_x, range_max_position_x))

            ab = _device.get_abs(MTDEV_ABS_POSITION_Y)
            range_min_position_y = drs('min_position_y', ab.minimum)
            range_max_position_y = drs('max_position_y', ab.maximum)
            Logger.info('MTD: <%s> range position Y is %d - %d' %
                        (_fn, range_min_position_y, range_max_position_y))

            ab = _device.get_abs(MTDEV_ABS_TOUCH_MAJOR)
            range_min_major = drs('min_touch_major', ab.minimum)
            range_max_major = drs('max_touch_major', ab.maximum)
            Logger.info('MTD: <%s> range touch major is %d - %d' %
                        (_fn, range_min_major, range_max_major))

            ab = _device.get_abs(MTDEV_ABS_TOUCH_MINOR)
            range_min_minor = drs('min_touch_minor', ab.minimum)
            range_max_minor = drs('max_touch_minor', ab.maximum)
            Logger.info('MTD: <%s> range touch minor is %d - %d' %
                        (_fn, range_min_minor, range_max_minor))

            range_min_pressure = drs('min_pressure', 0)
            range_max_pressure = drs('max_pressure', 255)
            Logger.info('MTD: <%s> range pressure is %d - %d' %
                        (_fn, range_min_pressure, range_max_pressure))

            invert_x = int(bool(drs('invert_x', 0)))
            invert_y = int(bool(drs('invert_y', 0)))
            Logger.info('MTD: <%s> axes invertion: X is %d, Y is %d' %
                        (_fn, invert_x, invert_y))

            rotation = drs('rotation', 0)
            Logger.info('MTD: <%s> rotation set to %d' %
                        (_fn, rotation))
            failures = 0
            while _device:
                # if device have disconnected lets try to connect
                if failures > 1000:
                    Logger.info('MTD: <%s> input device disconnected' % _fn)
                    while not os.path.exists(_fn):
                        time.sleep(0.05)
                    # input device is back online let's recreate device
                    _device.close()
                    _device = Device(_fn)
                    Logger.info('MTD: <%s> input device reconnected' % _fn)
                    failures = 0
                    continue

                # idle as much as we can.
                while _device.idle(1000):
                    continue

                # got data, read all without redoing idle
                while True:
                    data = _device.get()
                    if data is None:
                        failures += 1
                        break

                    failures = 0

                    # set the working slot
                    if data.type == MTDEV_TYPE_EV_ABS and \
                       data.code == MTDEV_CODE_SLOT:
                        _slot = data.value
                        continue

                    # fill the slot
                    if not (_slot in l_points):
                        l_points[_slot] = dict()
                    point = l_points[_slot]
                    ev_value = data.value
                    ev_code = data.code
                    if ev_code == MTDEV_CODE_POSITION_X:
                        val = normalize(ev_value,
                                        range_min_position_x,
                                        range_max_position_x)
                        assign_coord(point, val, invert_x, 'xy')
                    elif ev_code == MTDEV_CODE_POSITION_Y:
                        val = 1. - normalize(ev_value,
                                             range_min_position_y,
                                             range_max_position_y)
                        assign_coord(point, val, invert_y, 'yx')
                    elif ev_code == MTDEV_CODE_PRESSURE:
                        point['pressure'] = normalize(ev_value,
                                                      range_min_pressure,
                                                      range_max_pressure)
                    elif ev_code == MTDEV_CODE_TOUCH_MAJOR:
                        point['size_w'] = normalize(ev_value,
                                                    range_min_major,
                                                    range_max_major)
                    elif ev_code == MTDEV_CODE_TOUCH_MINOR:
                        point['size_h'] = normalize(ev_value,
                                                    range_min_minor,
                                                    range_max_minor)
                    elif ev_code == MTDEV_CODE_TRACKING_ID:
                        if ev_value == -1:
                            point['delete'] = True
                            # force process of changes here, as the slot can be
                            # reused.
                            _changes.add(_slot)
                            process([l_points[x] for x in _changes])
                            _changes.clear()
                            continue
                        else:
                            point['id'] = ev_value
                    else:
                        # unrecognized command, ignore.
                        continue
                    _changes.add(_slot)

                # push all changes
                if _changes:
                    process([l_points[x] for x in _changes])
                    _changes.clear()

        def update(self, dispatch_fn):
            # dispatch all event from threads
            try:
                while True:
                    event_type, touch = self.queue.popleft()
                    dispatch_fn(event_type, touch)
            except:
                pass

    MotionEventFactory.register('mtdev', MTDMotionEventProvider)
