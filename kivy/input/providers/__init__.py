# pylint: disable=W0611
'''
Providers
=========

The list of available input **providerid**\s is as follows:

+-----------------------------------+------------+
| Provider                          | providerid |
+===================================+============+
| Android Joystick                  | android    |
+-----------------------------------+------------+
| HID Input (linux)                 | hidinput   |
+-----------------------------------+------------+
| Linux Multitouch (using libmtdev) | mtdev      |
+-----------------------------------+------------+
| MacOS Touch Device                | mactouch   |
+-----------------------------------+------------+
| Mouse                             | mouse      |
+-----------------------------------+------------+
| TUIO                              | tuio       |
+-----------------------------------+------------+
| LeapMotion (10 fingers)           | leapfinger |
+-----------------------------------+------------+
| LeapMotion (2 hands)              | leaphand   |
+-----------------------------------+------------+
| Wacom (linux)                     | linuxwacom |
+-----------------------------------+------------+
| Windows Touch                     | wm_touch   |
+-----------------------------------+------------+
| Windows Pen                       | wm_pen     |
+-----------------------------------+------------+

In order to activate an input provider, you need to add it to the **input**
section of the configuration. For example::

    [input]
    acert230h = mtdev,/dev/input/event2

Please see the :mod:`kivy.config` **input** section for more detail on how to
use these **providerid**\s.

For specific details on the input providers, please see the module specific
documentation below.
'''

import os

from kivy.utils import platform as core_platform
from kivy.logger import Logger
from kivy.setupconfig import USE_SDL2

import kivy.input.providers.tuio
import kivy.input.providers.mouse

platform = core_platform

if platform == 'win' or 'KIVY_DOC' in os.environ:
    try:
        import kivy.input.providers.wm_touch
        import kivy.input.providers.wm_pen
    except:
        err = 'Input: WM_Touch/WM_Pen not supported by your version of Windows'
        Logger.warning(err)

if platform == 'macosx' or 'KIVY_DOC' in os.environ:
    try:
        import kivy.input.providers.mactouch
    except:
        err = 'Input: MacMultitouchSupport is not supported by your system'
        Logger.exception(err)

if platform == 'linux' or 'KIVY_DOC' in os.environ:
    try:
        import kivy.input.providers.probesysfs
    except:
        err = 'Input: ProbeSysfs is not supported by your version of linux'
        Logger.exception(err)
    try:
        import kivy.input.providers.mtdev
    except:
        err = 'Input: MTDev is not supported by your version of linux'
        Logger.exception(err)
    try:
        import kivy.input.providers.hidinput
    except:
        err = 'Input: HIDInput is not supported by your version of linux'
        Logger.exception(err)
    try:
        import kivy.input.providers.linuxwacom
    except:
        err = 'Input: LinuxWacom is not supported by your version of linux'
        Logger.exception(err)

if (platform == 'android' and not USE_SDL2) or 'KIVY_DOC' in os.environ:
    try:
        import kivy.input.providers.androidjoystick
    except:
        err = 'Input: AndroidJoystick is not supported by your version ' \
              'of linux'
        Logger.exception(err)

try:
    import kivy.input.providers.leapfinger  # NOQA
    import kivy.input.providers.leaphand  # NOQA
except:
    err = 'Input: LeapFinger/LeapHand is not available on your system'
    Logger.exception(err)
