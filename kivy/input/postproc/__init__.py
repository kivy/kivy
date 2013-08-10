'''
Input Postprocessing
====================

'''

__all__ = ('kivy_postproc_modules', )

import os
from kivy.input.postproc.doubletap import InputPostprocDoubleTap
from kivy.input.postproc.tripletap import InputPostprocTripleTap
from kivy.input.postproc.ignorelist import InputPostprocIgnoreList
from kivy.input.postproc.retaintouch import InputPostprocRetainTouch
from kivy.input.postproc.dejitter import InputPostprocDejitter

# Mapping of ID to module
kivy_postproc_modules = {}

# Don't go further if we generate documentation
if 'KIVY_DOC' not in os.environ:
    kivy_postproc_modules['retaintouch'] = InputPostprocRetainTouch()
    kivy_postproc_modules['ignorelist'] = InputPostprocIgnoreList()
    kivy_postproc_modules['doubletap'] = InputPostprocDoubleTap()
    kivy_postproc_modules['tripletap'] = InputPostprocTripleTap()
    kivy_postproc_modules['dejitter'] = InputPostprocDejitter()
