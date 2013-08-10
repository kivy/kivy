'''
Compatibility module for Python 2.7 and > 3.3
=============================================
'''

__all__ = ('PY2', 'string_types', 'queue', 'iterkeys', 'itervalues', 'iteritems')

import sys
try:
    import queue
except ImportError:
    import Queue as queue

#: True if Python 2 intepreter is used
PY2 = sys.version_info[0] == 2

#: String types that can be used for checking if a object is a string
string_types = None
if PY2:
    string_types = basestring
else:
    string_types = str

if PY2:
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
else:
    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())
