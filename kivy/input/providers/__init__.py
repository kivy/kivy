'''
Providers
=========

'''

import os

from kivy.utils import platform as core_platform
from kivy.logger import Logger
from kivy.input.providers.tuio import *
from kivy.input.providers.mouse import *

platform = core_platform()

if platform == 'win' or 'KIVY_DOC' in os.environ:
    try:
        from kivy.input.providers.wm_touch import *
        from kivy.input.providers.wm_pen import *
    except:
        err = 'Input: WM_Touch/WM_Pen not supported by your version of Windows'
        Logger.warning(err)

if platform == 'macosx' or 'KIVY_DOC' in os.environ:
    try:
        from kivy.input.providers.mactouch import *
    except:
        err = 'Input: MacMultitouchSupport is not supported by your system'
        Logger.exception(err)

if platform == 'linux' or 'KIVY_DOC' in os.environ:
    try:
        from kivy.input.providers.probesysfs import *
    except:
        err = 'Input: ProbeSysfs is not supported by your version of linux'
        Logger.exception(err)
    try:
        from kivy.input.providers.mtdev import *
    except:
        err = 'Input: MTDev is not supported by your version of linux'
        Logger.exception(err)
    try:
        from kivy.input.providers.hidinput import *
    except:
        err = 'Input: HIDInput is not supported by your version of linux'
        Logger.exception(err)

if platform == 'android' or 'KIVY_DOC' in os.environ:
    try:
        from kivy.input.providers.linuxwacom import *
    except:
        err = 'Input: LinuxWacom is not supported by your version of linux'
        Logger.exception(err)
    try:
        from kivy.input.providers.androidjoystick import *
    except:
        err = 'Input: AndroidJoystick is not supported by your version of linux'
        Logger.exception(err)
