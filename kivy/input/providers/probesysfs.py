'''
Auto Create Input Provider Config Entry for Available MT Hardware (linux only).
===============================================================================

Thanks to Marc Tardif for the probing code, taken from scan-for-mt-device.

The device discovery is done by this provider. However, the reading of input can
be made by other providers like: hidinput, mtdev, linuxwacom. mtdev is used
prior to other providers. For more information about mtdev, check
:py:class:`~kivy.input.providers.mtdev`.

Here is an example of auto creation ::

    [input]
    # using mtdev
    device_%(name)s = probesysfs,provider=mtdev
    # using hidinput
    device_%(name)s = probesysfs,provider=hidinput
    # using mtdev with a match on name
    device_%(name)s = probesysfs,provider=mtdev,match=acer

    # using hidinput with custom parameters to hidinput (all on one line)
    %(name)s = probesysfs,
        provider=hidinput,param=min_pressure=1,param=max_pressure=99

    # you can also match your wacom touchscreen
    touch = probesysfs,match=E3 Finger,provider=linuxwacom,
        select_all=1,param=mode=touch
    # and your wacom pen
    pen = probesysfs,match=E3 Pen,provider=linuxwacom,
        select_all=1,param=mode=pen

By default, ProbeSysfs module will enumerate hardware from /sys/class/input
device, and configure hardware with ABS_MT_POSITION_X capability. But for
example, wacom screen doesn't support this capability. You can prevent this
behavior by putting select_all=1 in your config line.
'''

__all__ = ('ProbeSysfsHardwareProbe', )

import os
from os.path import sep

if 'KIVY_DOC' in os.environ:

    ProbeSysfsHardwareProbe = None

else:
    from re import match, IGNORECASE
    from glob import glob
    from subprocess import Popen, PIPE
    from kivy.logger import Logger
    from kivy.input.provider import MotionEventProvider
    from kivy.input.factory import MotionEventFactory

    # See linux/input.h
    ABS_MT_POSITION_X = 0x35

    _cache_input = None

    class Input(object):

        def __init__(self, path):
            self.path = path

        @property
        def device(self):
            base = os.path.basename(self.path)
            return os.path.join("/dev", "input", base)

        @property
        def name(self):
            path = os.path.join(self.path, "device", "name")
            return read_line(path)

        def get_capabilities(self):
            path = os.path.join(self.path, "device", "capabilities", "abs")
            line = read_line(path)
            capabilities = []
            long_bit = getconf("LONG_BIT")
            for i, word in enumerate(line.split(" ")):
                word = int(word, 16)
                subcapabilities = [bool(word & 1<<i) for i in range(long_bit)]
                capabilities[:0] = subcapabilities

            return capabilities

        def has_capability(self, capability):
            capabilities = self.get_capabilities()
            return len(capabilities) > capability and capabilities[capability]

    def getconf(var):
        output = Popen(["getconf", var], stdout=PIPE).communicate()[0]
        return int(output)

    def get_inputs(path):
        global _cache_input
        if _cache_input is None:
            event_glob = os.path.join(path, "event*")
            _cache_input = [Input(x) for x in glob(event_glob)]
        return _cache_input

    def read_line(path):
        f = open(path)
        try:
            return f.readline().strip()
        finally:
            f.close()

    class ProbeSysfsHardwareProbe(MotionEventProvider):

        def __new__(self, device, args):
            # hack to not return an instance of this provider.
            # :)
            instance = super(ProbeSysfsHardwareProbe, self).__new__(self)
            instance.__init__(device, args)

        def __init__(self, device, args):
            super(ProbeSysfsHardwareProbe, self).__init__(device, args)
            self.provider = 'mtdev'
            self.match = None
            self.input_path = '/sys/class/input'
            self.select_all = False
            self.use_regex = False
            self.args = []

            args = args.split(',')
            for arg in args:
                if arg == '':
                    continue
                arg = arg.split('=', 1)
                # ensure it's a key = value
                if len(arg) != 2:
                    Logger.error('ProbeSysfs: invalid parameters %s, not'
                                 ' key=value format' % arg)
                    continue

                key, value = arg
                if key == 'match':
                    self.match = value
                elif key == 'provider':
                    self.provider = value
                elif key == 'use_regex':
                    self.use_regex = bool(value)
                elif key == 'select_all':
                    self.select_all = bool(value)
                elif key == 'param':
                    self.args.append(value)
                else:
                    Logger.error('ProbeSysfs: unknown %s option' % key)
                    continue

            self.probe()

        def probe(self):
            inputs = get_inputs(self.input_path)
            if not self.select_all:
                inputs = [x for x in inputs if \
                          x.has_capability(ABS_MT_POSITION_X)]
            for device in inputs:
                Logger.debug('ProbeSysfs: found device: %s at %s' % (
                                 device.name, device.device))

                # must ignore ?
                if self.match:
                    if self.use_regex:
                        if not match(self.match, device.name, IGNORECASE):
                            Logger.debug('ProbeSysfs: device not match the'
                                         ' rule in config, ignoring.')
                            continue
                    else:
                        if self.match not in device.name:
                            continue

                Logger.info('ProbeSysfs: device match: %s' % device.device)

                d = device.device
                devicename = self.device % dict(name=d.split(sep)[-1])

                provider = MotionEventFactory.get(self.provider)
                if provider is None:
                    Logger.info('ProbeSysfs: unable to found provider %s' %
                                     self.provider)
                    Logger.info('ProbeSysfs: fallback on hidinput')
                    provider = MotionEventFactory.get('hidinput')
                if provider is None:
                    Logger.critical('ProbeSysfs: no input provider found'
                                    ' to handle this device !')
                    continue

                instance = provider(devicename, '%s,%s' % (device.device,
                                                           ','.join(self.args)))
                if instance:
                    from kivy.base import EventLoop
                    EventLoop.add_input_provider(instance)


    MotionEventFactory.register('probesysfs', ProbeSysfsHardwareProbe)
