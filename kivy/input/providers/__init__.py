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
        err = 'Input: WM_Touch/WM_Pen not supported by your version of Windows'
        Logger.warning(err)

if sys.platform == 'darwin' or 'KIVY_DOC' in os.environ:
    try:
        from kivy.input.providers.mactouch import *
    except:
        err = 'Input: MacMultitouchSupport is not supported by your system'
        Logger.exception(err)

if sys.platform == 'linux2' or 'KIVY_DOC' in os.environ:
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
    try:
        from kivy.input.providers.linuxwacom import *
    except:
        err = 'Input: LinuxWacom is not supported by your version of linux'
        Logger.exception()
