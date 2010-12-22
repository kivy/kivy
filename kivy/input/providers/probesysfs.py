'''
Create input entry for each Multitouch hardware found (linux only).
===================================================================

Thanks to Marc Tardif for the probing code, used from scan-for-mt-device script.

The device discovery is done by this provider. However, the reading of input can
be made by 2 other providers: hidinput or mtdev. mtdev is used prior to
hidinput. For more information about mtdev, check
:py:class:`~kivy.input.providers.mtdev`.

Here is an example of auto creation ::

    [input]
    # using mtdev
    device_%(name)s = probesysfs,provider=mtdev
    # using hidinput
    device_%(name)s = probesysfs,provider=hidinput
    # using mtdev with a match on name
    device_%(name)s = probesysfs,provider=mtdev,match=acer

    # using hidinput with custom parameters to hidinput
    %(name)s = probesysfs,provider=hidinput,param=min_pressure=1,param=max_pressure=99

ProbeSysfs module will enumerate hardware from /sys/class/input device, and
configure hardware with ABS_MT_POSITION_X capability.
'''

__all__ = ('ProbeSysfsHardwareProbe', )

import os

if 'KIVY_DOC' in os.environ:

    ProbeSysfsHardwareProbe = None

else:
    import kivy
    import sys
    import re
    from glob import glob
    from subprocess import Popen, PIPE
    from kivy.logger import Logger
    from kivy.input.provider import TouchProvider
    from kivy.input.factory import TouchFactory

    # See linux/input.h
    ABS_MT_POSITION_X = 0x35

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
        event_glob = os.path.join(path, "event*")
        for event_path in glob(event_glob):
            yield Input(event_path)

    def read_line(path):
        f = open(path)
        try:
            return f.readline().strip()
        finally:
            f.close()

    class ProbeSysfsHardwareProbe(TouchProvider):

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
                elif key == 'param':
                    self.args.append(value)
                else:
                    Logger.error('ProbeSysfs: unknown %s option' % key)
                    continue

            self.probe()

        def probe(self):
            inputs = get_inputs(self.input_path)
            inputs = [x for x in inputs if x.has_capability(ABS_MT_POSITION_X)]
            for device in inputs:
                Logger.info('ProbeSysfs: found device: %s at %s' % (
                                 device.name, device.device))

                # must ignore ?
                if self.match:
                    if not re.match(self.match, device.name, re.IGNORECASE):
                        Logger.warning('ProbeSysfs: device not match the'
                                       ' rule in config, ignoring.')
                        continue

                devicename = self.device % dict(name=device.device.split(os.path.sep)[-1])

                provider = TouchFactory.get(self.provider)
                if provider is None:
                    Logger.info('ProbeSysfs: unable to found provider %s' %
                                     self.provider)
                    Logger.info('ProbeSysfs: fallback on hidinput')
                    provider = TouchFactory.get('hidinput')
                if provider is None:
                    Logger.critical('ProbeSysfs: no input provider found'
                                    ' to handle this device !')
                    continue

                instance = provider(devicename, '%s,%s' % (device.device,
                                                           ','.join(self.args)))
                if instance:
                    kivy.kivy_providers.append(instance)



    TouchFactory.register('probesysfs', ProbeSysfsHardwareProbe)
