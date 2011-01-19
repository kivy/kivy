'''
Utils
=====

'''

__all__ = ('intersection', 'difference', 'curry', 'strtotuple',
           'get_color_from_hex', 'get_color_for_pyglet', 'get_random_color',
           'is_color_transparent', 'boundary',
           'deprecated', 'SafeList',
           'interpolate', 'OrderedDict')

from re import match, split
from UserDict import DictMixin


def boundary(value, minvalue, maxvalue):
    '''Limit a value between a minvalue and maxvalue'''
    return min(max(value, minvalue), maxvalue)


def intersection(set1, set2):
    '''Return intersection between 2 list'''
    return filter(lambda s: s in set2, set1)


def difference(set1, set2):
    '''Return difference between 2 list'''
    return filter(lambda s: s not in set2, set1)


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
    if not match('^[,.0-9 ()\[\]]*$', s):
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

    value = [int(x, 16)/255. for x in split('([0-9a-f]{2})', s) if x != '']
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


def is_color_transparent(c):
    '''Return true if alpha channel is 0'''
    if len(c) < 4:
        return False
    if float(c[3]) == 0.:
        return True
    return False


DEPRECATED_CALLERS = []


def deprecated(func):
    '''This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted the first time
    the function is used.'''

    import inspect
    import functools

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
            from kivy.logger import Logger
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


class OrderedDict(dict, DictMixin):

    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        try:
            self.__end
        except AttributeError:
            self.clear()
        self.update(*args, **kwds)

    def clear(self):
        self.__end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.__map = {}                 # key --> [key, prev, next]
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            end = self.__end
            curr = end[1]
            curr[2] = end[1] = self.__map[key] = [key, curr, end]
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        key, prev, next = self.__map.pop(key)
        prev[2] = next
        next[1] = prev

    def __iter__(self):
        end = self.__end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.__end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def popitem(self, last=True):
        if not self:
            raise KeyError('dictionary is empty')
        if last:
            key = reversed(self).next()
        else:
            key = iter(self).next()
        value = self.pop(key)
        return key, value

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        tmp = self.__map, self.__end
        del self.__map, self.__end
        inst_dict = vars(self).copy()
        self.__map, self.__end = tmp
        if inst_dict:
            return (self.__class__, (items, ), inst_dict)
        return self.__class__, (items, )

    def keys(self):
        return list(self)

    setdefault = DictMixin.setdefault
    update = DictMixin.update
    pop = DictMixin.pop
    values = DictMixin.values
    items = DictMixin.items
    iterkeys = DictMixin.iterkeys
    itervalues = DictMixin.itervalues
    iteritems = DictMixin.iteritems

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__, )
        return '%s(%r)' % (self.__class__.__name__, self.items())

    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def __eq__(self, other):
        if isinstance(other, OrderedDict):
            return len(self)==len(other) and self.items() == other.items()
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other

