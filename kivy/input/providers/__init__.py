# pylint: disable=W0611
'''
Providers
=========

'''

import os

from kivy.utils import platform as core_platform
from kivy.logger import Logger
from kivy.setupconfig import USE_SDL3

import kivy.input.providers.tuio
import kivy.input.providers.mouse

platform = core_platform

if platform == 'win' or 'KIVY_DOC' in os.environ:
    try:
        import kivy.input.providers.wm_touch
        import kivy.input.providers.wm_pen
    except Exception:
        err = 'Input: WM_Touch/WM_Pen not supported by your version of Windows'
        Logger.warning(err)

if platform == 'macosx' or 'KIVY_DOC' in os.environ:
    try:
        import kivy.input.providers.mactouch
    except Exception:
        err = 'Input: MacMultitouchSupport is not supported by your system'
        Logger.exception(err)

if platform == 'linux' or 'KIVY_DOC' in os.environ:
    try:
        import kivy.input.providers.probesysfs
    except Exception:
        err = 'Input: ProbeSysfs is not supported by your version of linux'
        Logger.exception(err)
    try:
        import kivy.input.providers.mtdev
    except Exception:
        err = 'Input: MTDev is not supported by your version of linux'
        Logger.exception(err)
    try:
        import kivy.input.providers.hidinput
    except Exception:
        err = 'Input: HIDInput is not supported by your version of linux'
        Logger.exception(err)
    try:
        import kivy.input.providers.linuxwacom
    except Exception:
        err = 'Input: LinuxWacom is not supported by your version of linux'
        Logger.exception(err)

if (platform == 'android' and not USE_SDL3) or 'KIVY_DOC' in os.environ:
    try:
        import kivy.input.providers.androidjoystick
    except Exception:
        err = 'Input: AndroidJoystick is not supported by your version ' \
              'of linux'
        Logger.exception(err)

try:
    import kivy.input.providers.leapfinger  # NOQA
except Exception:
    err = 'Input: LeapFinger is not available on your system'
    Logger.exception(err)
