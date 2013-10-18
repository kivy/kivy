'''Screen
======

This module changes some environement and configuration variables
to match the density / dpi / screensize of a specific device.

To see a list of the available screenid's, just run::

    python main.py -m screen

To simulate a medium-density screen such as the Motolora Droid 2::

    python main.py -m screen:droid2

To simulate a high-density screen such as HTC One X, in portrait::

    python main.py -m screen:onex,portrait

To simulate the iPad 2 screen::

    python main.py -m screen:ipad

If the generated window is too large, you can specify a scale::

    python main.py -m screen:note2,portrait,scale=.75

Note that to display your contents correctly on a scaled window you
must consistently use units 'dp' and 'sp' throughout your app. See
:mod:`~kiv.metrics` for more details.

'''

import sys
from os import environ
from kivy.config import Config
from kivy.logger import Logger

# taken from http://en.wikipedia.org/wiki/List_of_displays_by_pixel_density
devices = {
    # device: (name, width, height, dpi, density)
    'onex': ('HTC One X', 1280, 720, 312, 2),
    'one': ('HTC One', 1920, 1080, 468, 3),
    'onesv': ('HTC One SV', 480, 800, 216, 1.5),
    's3': ('Galaxy SIII', 1280, 720, 306, 2),
    'note2': ('Galaxy Note II', 1280, 720, 267, 2),
    'droid2': ('Motolora Droid 2', 854, 480, 240, 1.5),
    'xoom': ('Motolora Xoom', 1280, 800, 149, 1),
    'ipad': ('iPad (1 and 2)', 1024, 768, 132, 1),
    'ipad3': ('iPad 3', 2048, 1536, 264, 2),
    'iphone4': ('iPhone 4', 640, 960, 326, 2),
    'iphone5': ('iPhone 5', 640, 1136, 326, 2),
    'xperiae': ('Xperia E', 320, 480, 166, 1),
    'nexus4': ('Nexus 4', 1280, 768, 320, 2),
    'nexus7': ('Nexus 7 (2012 version)', 1280, 800, 216, 1.325),
    'nexus7.2': ('Nexus 7 (2013 version)', 1920, 1200, 323, 2),
}


def start(win, ctx):
    pass


def stop(win, ctx):
    pass


def apply_device(device, scale, orientation):
    name, width, height, dpi, density = devices[device]
    if orientation == 'portrait':
        width, height = height, width
    Logger.info('Screen: Apply screen settings for {0}'.format(name))
    Logger.info('Screen: size={0}x{1} dpi={2} density={3} '
        'orientation={4}'.format(width, height, dpi, density, orientation))
    try:
        scale = float(scale)
    except:
        scale = 1
    environ['KIVY_METRICS_DENSITY'] = str(density * scale)
    environ['KIVY_DPI'] = str(dpi * scale)
    Config.set('graphics', 'width', str(int(width * scale)))
    # simulate with the android bar
    # FIXME should be configurable
    Config.set('graphics', 'height', str(int(height * scale - 25 * density)))
    Config.set('graphics', 'fullscreen', '0')
    Config.set('graphics', 'show_mousecursor', '1')


def usage(device=None):
    if device:
        Logger.error('Screen: The specified device ({0}) is unknown.',
                device)
    print('\nModule usage: python main.py -m screen,deviceid[,orientation]\n')
    print('Availables devices:\n')
    print('{0:12} {1:<22} {2:<8} {3:<8} {4:<5} {5:<8}'.format(
        'Device ID', 'Name', 'Width', 'Height', 'DPI', 'Density'))
    for device, info in devices.items():
        print('{0:12} {1:<22} {2:<8} {3:<8} {4:<5} {5:<8}'.format(
            device, *info))
    print('\n')
    print('Simulate a medium-density screen such as Motolora Droid 2:\n')
    print('    python main.py -m screen,droid2\n')
    print('Simulate a high-density screen such as HTC One X, in portrait:\n')
    print('    python main.py -m screen,onex,portrait\n')
    print('Simulate the iPad 2 screen\n')
    print('    python main.py -m screen,ipad\n')
    sys.exit(1)


def configure(ctx):
    scale = ctx.pop('scale', None)
    orientation = 'landscape'
    ctx.pop('landscape', None)
    if ctx.pop('portrait', None):
        orientation = 'portrait'
    if not ctx:
        return usage(None)
    device = list(ctx.keys())[0]
    if device not in devices:
        return usage('')
    apply_device(device, scale, orientation)

