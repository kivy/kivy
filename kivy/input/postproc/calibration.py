'''
Calibration
===========

.. versionadded:: 1.9.0

Recalibrate input device to a specific range / offset.

Let's say you have 3 1080p displays, the 2 firsts are multitouch. By default,
both will have mixed touch, the range will conflict with each others: the 0-1
range will goes to 0-5760 px (remember, 3 * 1920 = 5760.)

To fix it, you need to manually reference them. For example::

    [input]
    left = mtdev,/dev/input/event17
    middle = mtdev,/dev/input/event15
    # the right screen is just a display.

Then, you can use the calibration postproc module::

    [postproc:calibration]
    left = xratio=0.3333
    middle = xratio=0.3333,xoffset=0.3333

Now, the touches from the left screen will be within 0-0.3333 range, and the
touches from the middle screen will be within 0.3333-0.6666 range.

You can also match calibration rules to devices based on their provider type.
This is useful when probesysfs is used to match devices. For example::

    [input]
    mtdev_%(name)s = probesysfs,provider=mtdev

Then to apply calibration to any mtdev device, you can assign rules to the
provider name enclosed by parentheses::

    [postproc:calibration]
    (mtdev) = xratio=0.3333,xoffset=0.3333

Calibrating devices like this means the device's path doesn't need to be
configured ahead of time. Note that with this method, all mtdev inputs will
have the same calibration applied to them. For this reason, matching by
provider will typically be useful when expecting only one input device.
'''

__all__ = ('InputPostprocCalibration', )

from kivy.config import Config
from kivy.logger import Logger
from kivy.input import providers
from kivy.input.factory import MotionEventFactory
from kivy.input.motionevent import MotionEvent


class InputPostprocCalibration(object):
    '''Recalibrate the inputs.

    The configuration must go within a section named `postproc:calibration`.
    Within the section, you must have a line like::

        devicename = param=value,param=value

    If you wish to match by provider, you must have a line like::

        (provider) = param=value,param=value

    :Parameters:
        `xratio`: float
            Value to multiply X
        `yratio`: float
            Value to multiply Y
        `xoffset`: float
            Value to add to X
        `yoffset`: float
            Value to add to Y
        `auto`: str
            If set, then the touch is transformed from screen-relative
            to window-relative The value is used as an indication of
            screen size, e.g for fullHD:

                auto=1920x1080

            If present, this setting overrides all the others.
            This assumes the input device exactly covers the display
            area, if they are different, the computations will be wrong.

    .. versionchanged:: 1.11.0
        Added `auto` parameter
    '''

    def __init__(self):
        super(InputPostprocCalibration, self).__init__()
        self.devices = {}
        self.frame = 0
        self.provider_map = self._get_provider_map()
        if not Config.has_section('postproc:calibration'):
            return
        default_params = {'xoffset': 0, 'yoffset': 0, 'xratio': 1, 'yratio': 1}
        for device_key, params_str in Config.items('postproc:calibration'):
            params = default_params.copy()
            for param in params_str.split(','):
                param = param.strip()
                if not param:
                    continue
                key, value = param.split('=', 1)
                if key == 'auto':
                    width, height = [float(x) for x in value.split('x')]
                    params['auto'] = width, height
                    break
                if key not in ('xoffset', 'yoffset', 'xratio', 'yratio'):
                    Logger.error(
                        'Calibration: invalid key provided: {}'.format(key))
                params[key] = float(value)
            self.devices[device_key] = params

    def _get_provider_map(self):
        """Iterates through all registered input provider names and finds the
        respective MotionEvent subclass for each. Returns a dict of MotionEvent
        subclasses mapped to their provider name.
        """
        provider_map = {}
        for input_provider in MotionEventFactory.list():
            if not hasattr(providers, input_provider):
                continue

            p = getattr(providers, input_provider)
            for m in p.__all__:
                event = getattr(p, m)
                if issubclass(event, MotionEvent):
                    provider_map[event] = input_provider

        return provider_map

    def _get_provider_key(self, event):
        """Returns the provider key for the event if the provider is configured
        for calibration.
        """
        input_type = self.provider_map.get(event.__class__)
        key = '({})'.format(input_type)
        if input_type and key in self.devices:
            return key

    def process(self, events):
        # avoid doing any processing if there is no device to calibrate at all.
        if not self.devices:
            return events

        self.frame += 1
        frame = self.frame
        to_remove = []
        for etype, event in events:
            # frame-based logic below doesn't account for
            # end events having been already processed
            if etype == 'end':
                continue

            if event.device in self.devices:
                dev = event.device
            else:
                dev = self._get_provider_key(event)
            if not dev:
                continue

            # some providers use the same event to update and end
            if 'calibration:frame' not in event.ud:
                event.ud['calibration:frame'] = frame
            elif event.ud['calibration:frame'] == frame:
                continue
            event.ud['calibration:frame'] = frame

            params = self.devices[dev]
            if 'auto' in params:
                event.sx, event.sy = self.auto_calibrate(
                    event.sx, event.sy, params['auto'])
                if not (0 <= event.sx <= 1 and 0 <= event.sy <= 1):
                    to_remove.append((etype, event))
            else:
                event.sx = event.sx * params['xratio'] + params['xoffset']
                event.sy = event.sy * params['yratio'] + params['yoffset']

        for event in to_remove:
            events.remove(event)

        return events

    def auto_calibrate(self, sx, sy, size):
        from kivy.core.window import Window as W
        WIDTH, HEIGHT = size

        xratio = WIDTH / W.width
        yratio = HEIGHT / W.height

        xoffset = - W.left / W.width
        yoffset = - (HEIGHT - W.top - W.height) / W.height

        sx = sx * xratio + xoffset
        sy = sy * yratio + yoffset

        return sx, sy
