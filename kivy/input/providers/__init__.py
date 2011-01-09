'''
Providers
=========

'''

import sys
import os

from kivy.logger import Logger
from kivy.input.providers.tuio import *
from kivy.input.providers.mouse import *

if sys.platform == 'win32' or 'KIVY_DOC' in os.environ:
    try:
        from kivy.input.providers.wm_touch import *
        from kivy.input.providers.wm_pen import *
    except:
        Logger.warning('Input: WM_Touch/WM_Pen is not supported by your version of Windows')

if sys.platform == 'darwin' or 'KIVY_DOC' in os.environ:
    try:
        from kivy.input.providers.mactouch import *
    except:
        Logger.exception('Input: MacMultitouchSupport is not supported by your system')

if sys.platform == 'linux2' or 'KIVY_DOC' in os.environ:
    try:
        from kivy.input.providers.probesysfs import *
    except:
        Logger.exception('Input: ProbeSysfs is not supported by your version of linux')
    try:
        from kivy.input.providers.mtdev import *
    except:
        Logger.exception('Input: MTDev is not supported by your version of linux')
    try:
        from kivy.input.providers.hidinput import *
    except:
        Logger.exception('Input: HIDInput is not supported by your version of linux')
    try:
        from kivy.input.providers.linuxwacom import *
    except:
        Logger.exception('Input: LinuxWacom is not supported by your version of linux')
    try:
        from kivy.input.providers.androidjoystick import *
    except:
        Logger.exception('Input: AndroidJoystick is not supported by your version of linux')
