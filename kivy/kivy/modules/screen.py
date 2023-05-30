'''Screen
======

This module changes some environment and configuration variables
to match the density / dpi / screensize of a specific device.

To see a list of the available screenid's, just run::

    python main.py -m screen

To simulate a medium-density screen such as the Motorola Droid 2::

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
    'onesv': ('HTC One SV', 800, 480, 216, 1.5),
    's3': ('Galaxy SIII', 1280, 720, 306, 2),
    'note2': ('Galaxy Note II', 1280, 720, 267, 2),
    'droid2': ('Motorola Droid 2', 854, 480, 240, 1.5),
    'xoom': ('Motorola Xoom', 1280, 800, 149, 1),
    'ipad': ('iPad (1 and 2)', 1024, 768, 132, 1),
    'ipad3': ('iPad 3', 2048, 1536, 264, 2),
    'iphone4': ('iPhone 4', 960, 640, 326, 2),
    'iphone5': ('iPhone 5', 1136, 640, 326, 2),
    'xperiae': ('Xperia E', 480, 320, 166, 1),
    'nexus4': ('Nexus 4', 1280, 768, 320, 2),
    'nexus7': ('Nexus 7 (2012 version)', 1280, 800, 216, 1.325),
    'nexus7.2': ('Nexus 7 (2013 version)', 1920, 1200, 323, 2),

    # taken from design.google.com/devices
    # please consider using another data instead of
    # a dict for autocompletion to work
    # these are all in landscape
    'phone_android_one': ('Android One', 854, 480, 218, 1.5),
    'phone_htc_one_m8': ('HTC One M8', 1920, 1080, 432, 3.0),
    'phone_htc_one_m9': ('HTC One M9', 1920, 1080, 432, 3.0),
    'phone_iphone': ('iPhone', 480, 320, 168, 1.0),
    'phone_iphone_4': ('iPhone 4', 960, 640, 320, 2.0),
    'phone_iphone_5': ('iPhone 5', 1136, 640, 320, 2.0),
    'phone_iphone_6': ('iPhone 6', 1334, 750, 326, 2.0),
    'phone_iphone_6_plus': ('iPhone 6 Plus', 1920, 1080, 400, 3.0),
    'phone_lg_g2': ('LG G2', 1920, 1080, 432, 3.0),
    'phone_lg_g3': ('LG G3', 2560, 1440, 533, 3.0),
    'phone_moto_g': ('Moto G', 1280, 720, 327, 2.0),
    'phone_moto_x': ('Moto X', 1280, 720, 313, 2.0),
    'phone_moto_x_2nd_gen': ('Moto X 2nd Gen', 1920, 1080, 432, 3.0),
    'phone_nexus_4': ('Nexus 4', 1280, 768, 240, 2.0),
    'phone_nexus_5': ('Nexus 5', 1920, 1080, 450, 3.0),
    'phone_nexus_5x': ('Nexus 5X', 1920, 1080, 432, 2.6),
    'phone_nexus_6': ('Nexus 6', 2560, 1440, 496, 3.5),
    'phone_nexus_6p': ('Nexus 6P', 2560, 1440, 514, 3.5),
    'phone_oneplus_3t': ('OnePlus 3t', 1863, 1080, 380, 2.375),
    'phone_oneplus_6t': ('OnePlus 6t', 2340, 1080, 420, 2.625),
    'phone_samsung_galaxy_note_4': ('Samsung Galaxy Note 4',
                                    2560, 1440, 514, 3.0),
    'phone_samsung_galaxy_s5': ('Samsung Galaxy S5', 1920, 1080, 372, 3.0),
    'phone_samsung_galaxy_s6': ('Samsung Galaxy S6', 2560, 1440, 576, 4.0),
    'phone_sony_xperia_c4': ('Sony Xperia C4', 1920, 1080, 400, 2.0),
    'phone_sony_xperia_z_ultra': ('Sony Xperia Z Ultra', 1920, 1080, 348, 2.0),
    'phone_sony_xperia_z1_compact': ('Sony Xperia Z1 Compact',
                                     1280, 720, 342, 2.0),
    'phone_sony_xperia_z2z3': ('Sony Xperia Z2/Z3', 1920, 1080, 432, 3.0),
    'phone_sony_xperia_z3_compact': ('Sony Xperia Z3 Compact',
                                     1280, 720, 313, 2.0),
    'tablet_dell_venue_8': ('Dell Venue 8', 2560, 1600, 355, 2.0),
    'tablet_ipad': ('iPad', 1024, 768, 132, 1.0),
    'tablet_ipad_mini': ('iPad Mini', 1024, 768, 163, 1.0),
    'tablet_ipad_mini_retina': ('iPad Mini Retina', 2048, 1536, 326, 2.0),
    'tablet_ipad_pro': ('iPad Pro', 2732, 2048, 265, 2.0),
    'tablet_ipad_retina': ('iPad Retina', 2048, 1536, 264, 2.0),
    'tablet_nexus_10': ('Nexus 10', 2560, 1600, 297, 2.0),
    'tablet_nexus_7_12': ('Nexus 7 12', 1280, 800, 216, 1.3),
    'tablet_nexus_7_13': ('Nexus 7 13', 1920, 1200, 324, 2.0),
    'tablet_nexus_9': ('Nexus 9', 2048, 1536, 288, 2.0),
    'tablet_samsung_galaxy_tab_10': ('Samsung Galaxy Tab 10',
                                     1280, 800, 148, 1.0),
    'tablet_sony_xperia_z3_tablet': ('Sony Xperia Z3 Tablet',
                                     1920, 1200, 282, 2.0),
    'tablet_sony_xperia_z4_tablet': ('Sony Xperia Z4 Tablet',
                                     2560, 1600, 297, 2.0),
    'tablet_huawei_mediapad_m3_lite_10': ('HUAWEI MediaPad M3 Lite 10',
                                          1920, 1200, 320, 2.25)

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
                'orientation={4}'.format(width, height, dpi, density,
                                         orientation))
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
    print('\nModule usage: python main.py -m screen:deviceid[,orientation]\n')
    print('Available devices:\n')
    print('{0:12} {1:<22} {2:<8} {3:<8} {4:<5} {5:<8}'.format(
        'Device ID', 'Name', 'Width', 'Height', 'DPI', 'Density'))
    for device, info in devices.items():
        print('{0:12} {1:<22} {2:<8} {3:<8} {4:<5} {5:<8}'.format(
            device, *info))
    print('\n')
    print('Simulate a medium-density screen such as Motorola Droid 2:\n')
    print('    python main.py -m screen:droid2\n')
    print('Simulate a high-density screen such as HTC One X, in portrait:\n')
    print('    python main.py -m screen:onex,portrait\n')
    print('Simulate the iPad 2 screen\n')
    print('    python main.py -m screen:ipad\n')
    print('If the generated window is too large, you can specify a scale:\n')
    print('    python main.py -m screen:note2,portrait,scale=.75\n')
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


if __name__ == "__main__":
    for n in devices.values():
        assert n[1] > n[2]
