'''
Compatibility module for Python 2.7 and > 3.3
=============================================

This module provides a set of utility types and functions for optimization and
to aid in writing Python 2/3 compatibile code.
'''

__all__ = ('PY2', 'clock', 'string_types', 'queue', 'iterkeys',
           'itervalues', 'iteritems', 'isclose')

import sys
import time
from math import isinf, fabs
try:
    import queue
except ImportError:
    import Queue as queue
try:
    from math import isclose
except ImportError:
    isclose = None

PY2 = sys.version_info[0] == 2
'''True if this version of python is 2.x.'''

clock = None
'''A clock with the highest available resolution on your current Operating
System.'''

string_types = None
'''A utility type for detecting string in a Python 2/3 friendly way. For
example:

.. code-block:: python

    if isinstance(s, string_types):
        print("It's a string or unicode type")
    else:
        print("It's something else.")
'''

text_type = None
if PY2:
    string_types = basestring
    text_type = unicode
else:
    string_types = text_type = str

#: unichr is just chr in py3, since all strings are unicode
if PY2:
    unichr = unichr
else:
    unichr = chr

if PY2:
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
else:
    iterkeys = lambda d: iter(d.keys())
    itervalues = lambda d: iter(d.values())
    iteritems = lambda d: iter(d.items())


if PY2:
    if sys.platform in ('win32', 'cygwin'):
        clock = time.clock
    else:
        clock = time.time
else:
    clock = time.perf_counter


def _isclose(a, b, rel_tol=1e-9, abs_tol=0.0):
    '''Measures whether two floats are "close" to each other. Identical to
    https://docs.python.org/3.6/library/math.html#math.isclose, for older
    versions of python.
    '''

    if a == b:  # short-circuit exact equality
        return True

    if rel_tol < 0.0 or abs_tol < 0.0:
        raise ValueError('error tolerances must be non-negative')

    # use cmath so it will work with complex ot float
    if isinf(abs(a)) or isinf(abs(b)):
        # This includes the case of two infinities of opposite sign, or
        # one infinity and one finite number. Two infinities of opposite sign
        # would otherwise have an infinite relative tolerance.
        return False
    diff = fabs(b - a)

    return (((diff <= fabs(rel_tol * b)) or
             (diff <= fabs(rel_tol * a))) or
            (diff <= abs_tol))


if isclose is None:
    isclose = _isclose
