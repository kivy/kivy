'''
Compatibility module for Python 2.7 and > 3.3
=============================================
'''

import sys
try:
    import queue
except ImportError:
    import Queue as queue

#: True if the code is running on Python 3 interpreter.
is_py3 = sys.version >= '3'

#: String types that can be used for checking if a object is a string
string_types = str
if not is_py3:
    string_types = basestring
