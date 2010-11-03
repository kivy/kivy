'''
Utils: generic toolbox
'''

__all__ = ('intersection', 'difference', 'curry', 'strtotuple',
           'get_color_from_hex', 'get_color_for_pyglet', 'get_random_color',
           'is_color_transparent', 'boundary', 'connect',
           'deprecated', 'SafeList',
           'serialize_numpy', 'deserialize_numpy',
           'interpolate')

import inspect
import re
import functools
from kivy.logger import Logger

def boundary(value, minvalue, maxvalue):
    '''Limit a value between a minvalue and maxvalue'''
    return min(max(value, minvalue), maxvalue)

def intersection(set1, set2):
    '''Return intersection between 2 list'''
    return filter(lambda s:s in set2, set1)

def difference(set1, set2):
    '''Return difference between 2 list'''
    return filter(lambda s:s not in set2, set1)

def curry(fn, *cargs, **ckwargs):
    '''Change the function signature to pass new variable.'''
    def call_fn(*fargs, **fkwargs):
        d = ckwargs.copy()
        d.update(fkwargs)
        return fn(*(cargs + fargs), **d)
    return call_fn

def interpolate(value_from, value_to, step=10):
    '''Interpolate a value to another. Can be useful to smooth some transition.
    For example ::

        # instead of setting directly 
        self.pos = pos

        # use interpolate, and you'll have a nice transition
        self.pos = interpolate(self.pos, new_pos)

    .. warning::
        This interpolation work only on list/tuple/double with the same
        dimension. No test are done if the dimension is not the same.
    '''
    if type(value_from) in (list, tuple):
        out = []
        for x, y in zip(value_from, value_to):
            out.append(interpolate(x, y, step))
        return out
    else:
        return value_from + (value_to - value_from) / float(step)

def strtotuple(s):
    '''Convert a tuple string into tuple,
    with some security check. Designed to be used
    with eval() function ::

        a = (12, 54, 68)
        b = str(a)         # return '(12, 54, 68)'
        c = strtotuple(b)  # return (12, 54, 68)

    '''
    # security
    if not re.match('^[,.0-9 ()\[\]]*$', s):
        raise Exception('Invalid characters in string for tuple conversion')
    # fast syntax check
    if s.count('(') != s.count(')'):
        raise Exception('Invalid count of ( and )')
    if s.count('[') != s.count(']'):
        raise Exception('Invalid count of [ and ]')
    r = eval(s)
    if type(r) not in (list, tuple):
        raise Exception('Conversion failed')
    return r

def get_color_from_hex(s):
    '''Transform from hex string color to kivy color'''
    if s.startswith('#'):
        return get_color_from_hex(s[1:])

    value = [int(x, 16)/255. for x in re.split('([0-9a-f]{2})', s) if x != '']
    if len(value) == 3:
        value.append(1)
    return value

def get_random_color(alpha=1.0):
    ''' Returns a random color (4 tuple)

    :Parameters:
        `alpha` : float, default to 1.0
            if alpha == 'random' a random alpha value is generated
    '''
    from random import random
    if alpha == 'random':
        return [random(), random(), random(), random()]
    else:
        return [random(), random(), random(), alpha]


def get_color_for_pyglet(c):
    '''Transform from kivy color to pyglet color'''
    return map(lambda x: int(255 * x), c)

def is_color_transparent(c):
    '''Return true if alpha channel is 0'''
    if len(c) < 4:
        return False
    if float(c[3]) == 0.:
        return True
    return False

def connect(w1, p1, w2, p2, func=lambda x: x):
    '''Connect events to a widget property'''
    w1.connect(p1, w2, p2, func)

DEPRECATED_CALLERS = []
def deprecated(func):
    '''This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted the first time
    the function is used.'''

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        file, line, caller = inspect.stack()[1][1:4]
        caller_id = "%s:%s:%s" % (file, line, caller)
        # We want to print deprecated warnings only once:
        if caller_id not in DEPRECATED_CALLERS:
            DEPRECATED_CALLERS.append(caller_id)
            warning = (
                'Call to deprecated function %s in %s line %d.'
                'Called from %s line %d'
                ' by %s().') % (
                func.__name__,
                func.func_code.co_filename,
                func.func_code.co_firstlineno + 1,
                file, line, caller)
            Logger.warn(warning)
            if func.__doc__:
                Logger.warn(func.__doc__)
        return func(*args, **kwargs)
    return new_func


class SafeList(list):
    '''List with clear() method

    .. warning::
        Usage of iterate() function will decrease your performance.
    '''
    def clear(self):
        del self[:]

    @deprecated
    def iterate(self, reverse=False):
        if reverse:
            return reversed(iter(self))
        return iter(self)


def serialize_numpy(obj):
    import numpy
    from StringIO import StringIO
    from base64 import b64encode
    io = StringIO()
    numpy.save(io, obj)
    io.seek(0)
    return b64encode(io.read())

def deserialize_numpy(s):
    import numpy
    from StringIO import StringIO
    from base64 import b64decode
    io = StringIO(b64decode(s))
    return numpy.load(io)

