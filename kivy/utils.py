# pylint: disable=W0611
'''
Utils
=====

.. versionchanged:: 1.6.0
    OrderedDict class has been removed. Use the collections.OrderedDict.

'''

__all__ = ('intersection', 'difference', 'strtotuple',
           'get_color_from_hex', 'get_hex_from_color', 'get_random_color',
           'is_color_transparent', 'boundary',
           'deprecated', 'SafeList',
           'interpolate', 'QueryDict',
           'platform', 'escape_markup', 'reify')

from os import environ
from sys import platform as _sys_platform
from re import match, split
try:
    from UserDict import UserDict
    from UserDict import DictMixin
except ImportError:
    from collections import UserDict
    from collections import MutableMapping as DictMixin

_platform_android = None
_platform_ios = None


def boundary(value, minvalue, maxvalue):
    '''Limit a value between a minvalue and maxvalue'''
    return min(max(value, minvalue), maxvalue)


def intersection(set1, set2):
    '''Return intersection between 2 list'''
    return [s for s in set1 if s in set2]


def difference(set1, set2):
    '''Return difference between 2 list'''
    return [s for s in set1 if s not in set2]


def interpolate(value_from, value_to, step=10):
    '''Interpolate a value to another. Can be useful to smooth some transition.
    For example::

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
    with eval() function::

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

    value = [int(x, 16) / 255.
             for x in split('([0-9a-f]{2})', s.lower()) if x != '']
    if len(value) == 3:
        value.append(1)
    return value


def get_hex_from_color(color):
    '''Transform from kivy color to hex::

        >>> get_hex_from_color((0, 1, 0))
        '#00ff00'
        >>> get_hex_from_color((.25, .77, .90, .5))
        '#3fc4e57f'

    .. versionadded:: 1.5.0
    '''
    return '#' + ''.join(['{0:02x}'.format(int(x * 255)) for x in color])


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
                            func.__code__.co_filename,
                            func.__code__.co_firstlineno + 1,
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
            return super(QueryDict, self).__getattr__(attr)

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


class Platform(object):
    # refactored to class to allow module function to be replaced
    # with module variable
    _platform = None

    @deprecated
    def __call__(self):
        return self._get_platform()

    def __eq__(self, other):
        return other == self._get_platform()

    def __ne__(self, other):
        return other != self._get_platform()

    def __str__(self):
        return self._get_platform()

    def __repr__(self):
        return 'platform name: \'{platform}\' from: \n{instance}'.format(
            platform=self._get_platform(),
            instance=super(Platform, self).__repr__()
        )

    def __hash__(self):
        return self._get_platform().__hash__()

    def _get_platform(self):
        if self._platform is not None:
            return self._platform
        global _platform_ios, _platform_android

        if _platform_android is None:
            # ANDROID_ARGUMENT and ANDROID_PRIVATE are 2 environment variables
            # from python-for-android project
            _platform_android = 'ANDROID_ARGUMENT' in environ

        if _platform_ios is None:
            _platform_ios = (environ.get('KIVY_BUILD', '') == 'ios')

        # On android, _sys_platform return 'linux2', so prefer to check the
        # import of Android module than trying to rely on _sys_platform.
        if _platform_android is True:
            return 'android'
        elif _platform_ios is True:
            return 'ios'
        elif _sys_platform in ('win32', 'cygwin'):
            return 'win'
        elif _sys_platform == 'darwin':
            return 'macosx'
        elif _sys_platform[:5] == 'linux':
            return 'linux'
        return 'unknown'


platform = Platform()
'''
.. versionadded:: 1.3.0

Deprecated since 1.8.0:  Use platform as variable instaed of a function.\n
Calling platform() will return one of: *win*, *linux*, *android*, *macosx*,
*ios*, or *unknown*.

.. versionchanged:: 1.8.0

`platform` also behaves like a regular variable in comparisons like so::

    from kivy import platform
    if platform == 'linux':
        do_linux_things()
    if platform() == 'linux': # triggers deprecation warning
        do_more_linux_things()
    foo = {'linux' : do_linux_things}
    foo[platform]() # calls do_linux_things
    p = platform # assigns to a module object
    if p is 'android':
        do_android_things()
    p += 'some string' # error!

'''


def escape_markup(text):
    '''
    Escape markup characters found in the text. Intended to be used when markup
    text is activated on the Label::

        untrusted_text = escape_markup('Look at the example [1]')
        text = '[color=ff0000]' + untrusted_text + '[/color]'
        w = Label(text=text, markup=True)

    .. versionadded:: 1.3.0
    '''
    return text.replace('[', '&bl;').replace(']', '&br;').replace('&', '&amp;')


class reify(object):
    '''
    Put the result of a method which uses this (non-data) descriptor decorator
    in the instance dict after the first call, effectively replacing the
    decorator with an instance variable.

    It acts like @property, except that the function is only ever called once;
    after that, the value is cached as a regular attribute. This gives you lazy
    attribute creation on objects that are meant to be immutable.

    Taken from Pyramid project.
    '''

    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, inst, cls):
        if inst is None:
            return self
        retval = self.func(inst)
        setattr(inst, self.func.__name__, retval)
        return retval

