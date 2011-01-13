'''
Input Postprocessing
====================

'''

__all__ = ('kivy_postproc_modules', )

import os
from doubletap import InputPostprocDoubleTap
from ignorelist import InputPostprocIgnoreList
from retaintouch import InputPostprocRetainTouch
from dejitter import InputPostprocDejitter

# Mapping of ID to module
kivy_postproc_modules = {}

# Don't go further if we generate documentation
if 'KIVY_DOC' not in os.environ:
    kivy_postproc_modules['retaintouch'] = InputPostprocRetainTouch()
    kivy_postproc_modules['ignorelist'] = InputPostprocIgnoreList()
    kivy_postproc_modules['doubletap'] = InputPostprocDoubleTap()
    kivy_postproc_modules['dejitter'] = InputPostprocDejitter()
