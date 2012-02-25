'''
Utils
=====

'''

__all__ = ('intersection', 'difference', 'strtotuple',
           'get_color_from_hex', 'get_random_color',
           'is_color_transparent', 'boundary',
           'deprecated', 'SafeList',
           'interpolate', 'OrderedDict', 'QueryDict',
           'platform')

from sys import platform as _sys_platform
from re import match, split
from UserDict import DictMixin

_platform_android = None
_platform_ios = None


def boundary(value, minvalue, maxvalue):
    '''Limit a value between a minvalue and maxvalue'''
    return min(max(value, minvalue), maxvalue)


def intersection(set1, set2):
    '''Return intersection between 2 list'''
    return filter(lambda s: s in set2, set1)


def difference(set1, set2):
    '''Return difference between 2 list'''
    return filter(lambda s: s not in set2, set1)


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


class QueryDict(dict):
    '''QueryDict is a dict() that can be queried with dot.

    .. versionadded:: 1.0.4

    ::

        d = QueryDict()
        # create a key named toto, with the value 1
        d.toto = 1
        # it's the same as
        d['toto'] = 1
    '''

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            try:
                return super(QueryDict, self).__getattr__(attr)
            except AttributeError:
                raise KeyError(attr)

    def __setattr__(self, attr, value):
        self.__setitem__(attr, value)


def format_bytes_to_human(size, precision=2):
    '''Format a bytes number to human size (B, KB, MB...)

    .. versionadded:: 1.0.8

    :Parameters:
        `size`: int
            Number that represent a bytes number
        `precision`: int
            Precision after the comma

    Examples::

        >>> format_bytes_to_human(6463)
        '6.31 KB'
        >>> format_bytes_to_human(646368746541)
        '601.98 GB'

    '''
    size = int(size)
    fmt = '%%1.%df %%s' % precision
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return fmt % (size, unit)
        size /= 1024.0


def platform():
    '''Return the version of the current platform.
    This will return one of: win, linux, android, macosx, ios, unknown

    .. versionadded:: 1.0.8

    .. warning:: ios is not currently reported.
    '''
    global _platform_ios, _platform_android

    if _platform_android is None:
        try:
            __import__('android')
            _platform_android = True
        except ImportError:
            _platform_android = False

    if _platform_ios is None:
        # TODO implement ios support here
        _platform_ios = False

    # On android, _sys_platform return 'linux2', so prefer to check the import
    # of Android module than trying to rely on _sys_platform.
    if _platform_android is True:
        return 'android'
    elif _platform_ios is True:
        return 'ios'
    elif _sys_platform in ('win32', 'cygwin'):
        return 'win'
    elif _sys_platform in ('darwin', ):
        return 'macosx'
    elif _sys_platform in ('linux2', 'linux3'):
        return 'linux'
    return 'unknown'

