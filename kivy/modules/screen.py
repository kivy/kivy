'''
Screen
======

This module change some environement and configuration to match the density /
dpi / screensize of a specific devices.

To see a list of the available screenid, just run::

    python main.py -m screen

Simulate a medium-density screen as Motolora Droid 2::

    python main.py -m screen:droid2

Simulate a high-density screen as HTC One X, in portrait::

    python main.py -m screen:onex,portrait

Simulate the iPad 2 screen::

    python main.py -m screen:ipad
'''

import sys
from os import environ
from kivy.config import Config
from kivy.logger import Logger

# taken from http://en.wikipedia.org/wiki/List_of_displays_by_pixel_density
devices = {
    # device: (name, width, height, dpi, density)
    'onex': ('HTC One X', 1280, 720, 312, 2),
    's3': ('Galaxy SIII', 1280, 720, 306, 2),
    'droid2': ('Motolora Droid 2', 854, 480, 240, 1.5),
    'xoom': ('Motolora Xoom', 1280, 800, 149, 1),
    'ipad': ('iPad (1 and 2)', 1024, 768, 132, 1),
    'ipad3': ('iPad 3', 2048, 1536, 264, 2),
    'iphone4': ('iPhone 4', 640, 960, 326, 2),
    'iphone5': ('iPhone 5', 640, 1136, 326, 2),
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
    environ['KIVY_METRICS_DENSITY'] = str(density)
    environ['KIVY_DPI'] = str(dpi)
    Config.set('graphics', 'width', str(width))
    Config.set('graphics', 'height', str(height))
    Config.set('graphics', 'fullscreen', '0')
    Config.set('graphics', 'show_mousecursor', '1')


def usage(device=None):
    if device:
        Logger.error('Screen: The specified device ({0}) is unknow.',
                device)
    print '\nModule usage: python main.py -m screen,deviceid[,orientation]\n'
    print 'Availables devices:\n'
    print '{0:12} {1:<22} {2:<8} {3:<8} {4:<5} {5:<8}'.format(
        'Device ID', 'Name', 'Width', 'Height', 'DPI', 'Density')
    for device, info in devices.iteritems():
        print '{0:12} {1:<22} {2:<8} {3:<8} {4:<5} {5:<8}'.format(
            device, *info)
    print '\n'
    print 'Simulate a medium-density screen as Motolora Droid 2:\n'
    print '    python main.py -m screen:droid2\n'
    print 'Simulate a high-density screen as HTC One X, in portrait:\n'
    print '    python main.py -m screen:onex,portrait\n'
    print 'Simulate the iPad 2 screen\n'
    print '    python main.py -m screen:ipad\n'
    sys.exit(1)


def configure(ctx):
    scale = ctx.pop('scale', None)
    orientation = 'landscape'
    ctx.pop('landscape', None)
    if ctx.pop('portrait', None):
        orientation = 'portrait'
    if not ctx:
        return usage(None)
    device = ctx.keys()[0]
    if device not in devices:
        return usage('')
    apply_device(device, scale, orientation)

