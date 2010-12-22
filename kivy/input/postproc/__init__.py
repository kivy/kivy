'''
Input Postprocessing
====================

'''

__all__ = ('kivy_postproc_modules', )

import os
import doubletap
import ignorelist
import retaintouch
import dejitter

# Mapping of ID to module
kivy_postproc_modules = {}

# Don't go further if we generate documentation
if 'KIVY_DOC' not in os.environ:
    kivy_postproc_modules['retaintouch'] = retaintouch.InputPostprocRetainTouch()
    kivy_postproc_modules['ignorelist'] = ignorelist.InputPostprocIgnoreList()
    kivy_postproc_modules['doubletap'] = doubletap.InputPostprocDoubleTap()
    kivy_postproc_modules['dejitter'] = dejitter.InputPostprocDejitter()
