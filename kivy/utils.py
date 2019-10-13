# pylint: disable=W0611
'''
Utils
=====

The Utils module provides a selection of general utility functions and classes
that may be useful for various applications. These include maths, color,
algebraic and platform functions.

.. versionchanged:: 1.6.0
    The OrderedDict class has been removed. Use collections.OrderedDict
    instead.

'''

__all__ = ('intersection', 'difference', 'strtotuple',
           'get_color_from_hex', 'get_hex_from_color', 'get_random_color',
           'is_color_transparent', 'hex_colormap', 'colormap', 'boundary',
           'deprecated', 'SafeList',
           'interpolate', 'QueryDict',
           'platform', 'escape_markup', 'reify', 'rgba')

from os import environ
from sys import platform as _sys_platform
from re import match, split
from kivy.compat import string_types


def boundary(value, minvalue, maxvalue):
    '''Limit a value between a minvalue and maxvalue.'''
    return min(max(value, minvalue), maxvalue)


def intersection(set1, set2):
    '''Return the intersection of 2 lists.'''
    return [s for s in set1 if s in set2]


def difference(set1, set2):
    '''Return the difference between 2 lists.'''
    return [s for s in set1 if s not in set2]


def interpolate(value_from, value_to, step=10):
    '''Interpolate between two values. This can be useful for smoothing some
    transitions. For example::

        # instead of setting directly
        self.pos = pos

        # use interpolate, and you'll have a nicer transition
        self.pos = interpolate(self.pos, new_pos)

    .. warning::
        These interpolations work only on lists/tuples/doubles with the same
        dimensions. No test is done to check the dimensions are the same.
    '''
    if type(value_from) in (list, tuple):
        out = []
        for x, y in zip(value_from, value_to):
            out.append(interpolate(x, y, step))
        return out
    else:
        return value_from + (value_to - value_from) / float(step)


def strtotuple(s):
    '''Convert a tuple string into a tuple
    with some security checks. Designed to be used
    with the eval() function::

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


def rgba(s, *args):
    '''Return a Kivy color (4 value from 0-1 range) from either a hex string or
    a list of 0-255 values.

    .. versionadded:: 1.10.0
    '''
    if isinstance(s, string_types):
        return get_color_from_hex(s)
    if isinstance(s, (list, tuple)):
        s = [x / 255. for x in s]
        if len(s) == 3:
            s.append(1)
        return s
    if isinstance(s, (int, float)):
        s = [s / 255.]
        s.extend(x / 255. for x in args)
        if len(s) == 3:
            s.append(1)
        return s
    raise Exception('Invalid value (not a string / list / tuple)')


def get_color_from_hex(s):
    '''Transform a hex string color to a kivy
    :class:`~kivy.graphics.Color`.
    '''
    if s.startswith('#'):
        return get_color_from_hex(s[1:])

    value = [int(x, 16) / 255.
             for x in split('([0-9a-f]{2})', s.lower()) if x != '']
    if len(value) == 3:
        value.append(1)
    return value


def get_hex_from_color(color):
    '''Transform a kivy :class:`~kivy.graphics.Color` to a hex value::

        >>> get_hex_from_color((0, 1, 0))
        '#00ff00'
        >>> get_hex_from_color((.25, .77, .90, .5))
        '#3fc4e57f'

    .. versionadded:: 1.5.0
    '''
    return '#' + ''.join(['{0:02x}'.format(int(x * 255)) for x in color])


def get_random_color(alpha=1.0):
    '''Returns a random color (4 tuple).

    :Parameters:
        `alpha`: float, defaults to 1.0
            If alpha == 'random', a random alpha value is generated.
    '''
    from random import random
    if alpha == 'random':
        return [random(), random(), random(), random()]
    else:
        return [random(), random(), random(), alpha]


def is_color_transparent(c):
    '''Return True if the alpha channel is 0.'''
    if len(c) < 4:
        return False
    if float(c[3]) == 0.:
        return True
    return False


hex_colormap = {
    'aliceblue': '#f0f8ff',
    'antiquewhite': '#faebd7',
    'aqua': '#00ffff',
    'aquamarine': '#7fffd4',
    'azure': '#f0ffff',
    'beige': '#f5f5dc',
    'bisque': '#ffe4c4',
    'black': '#000000',
    'blanchedalmond': '#ffebcd',
    'blue': '#0000ff',
    'blueviolet': '#8a2be2',
    'brown': '#a52a2a',
    'burlywood': '#deb887',
    'cadetblue': '#5f9ea0',
    'chartreuse': '#7fff00',
    'chocolate': '#d2691e',
    'coral': '#ff7f50',
    'cornflowerblue': '#6495ed',
    'cornsilk': '#fff8dc',
    'crimson': '#dc143c',
    'cyan': '#00ffff',
    'darkblue': '#00008b',
    'darkcyan': '#008b8b',
    'darkgoldenrod': '#b8860b',
    'darkgray': '#a9a9a9',
    'darkgrey': '#a9a9a9',
    'darkgreen': '#006400',
    'darkkhaki': '#bdb76b',
    'darkmagenta': '#8b008b',
    'darkolivegreen': '#556b2f',
    'darkorange': '#ff8c00',
    'darkorchid': '#9932cc',
    'darkred': '#8b0000',
    'darksalmon': '#e9967a',
    'darkseagreen': '#8fbc8f',
    'darkslateblue': '#483d8b',
    'darkslategray': '#2f4f4f',
    'darkslategrey': '#2f4f4f',
    'darkturquoise': '#00ced1',
    'darkviolet': '#9400d3',
    'deeppink': '#ff1493',
    'deepskyblue': '#00bfff',
    'dimgray': '#696969',
    'dimgrey': '#696969',
    'dodgerblue': '#1e90ff',
    'firebrick': '#b22222',
    'floralwhite': '#fffaf0',
    'forestgreen': '#228b22',
    'fuchsia': '#ff00ff',
    'gainsboro': '#dcdcdc',
    'ghostwhite': '#f8f8ff',
    'gold': '#ffd700',
    'goldenrod': '#daa520',
    'gray': '#808080',
    'grey': '#808080',
    'green': '#008000',
    'greenyellow': '#adff2f',
    'honeydew': '#f0fff0',
    'hotpink': '#ff69b4',
    'indianred': '#cd5c5c',
    'indigo': '#4b0082',
    'ivory': '#fffff0',
    'khaki': '#f0e68c',
    'lavender': '#e6e6fa',
    'lavenderblush': '#fff0f5',
    'lawngreen': '#7cfc00',
    'lemonchiffon': '#fffacd',
    'lightblue': '#add8e6',
    'lightcoral': '#f08080',
    'lightcyan': '#e0ffff',
    'lightgoldenrodyellow': '#fafad2',
    'lightgreen': '#90ee90',
    'lightgray': '#d3d3d3',
    'lightgrey': '#d3d3d3',
    'lightpink': '#ffb6c1',
    'lightsalmon': '#ffa07a',
    'lightseagreen': '#20b2aa',
    'lightskyblue': '#87cefa',
    'lightslategray': '#778899',
    'lightslategrey': '#778899',
    'lightsteelblue': '#b0c4de',
    'lightyellow': '#ffffe0',
    'lime': '#00ff00',
    'limegreen': '#32cd32',
    'linen': '#faf0e6',
    'magenta': '#ff00ff',
    'maroon': '#800000',
    'mediumaquamarine': '#66cdaa',
    'mediumblue': '#0000cd',
    'mediumorchid': '#ba55d3',
    'mediumpurple': '#9370db',
    'mediumseagreen': '#3cb371',
    'mediumslateblue': '#7b68ee',
    'mediumspringgreen': '#00fa9a',
    'mediumturquoise': '#48d1cc',
    'mediumvioletred': '#c71585',
    'midnightblue': '#191970',
    'mintcream': '#f5fffa',
    'mistyrose': '#ffe4e1',
    'moccasin': '#ffe4b5',
    'navajowhite': '#ffdead',
    'navy': '#000080',
    'oldlace': '#fdf5e6',
    'olive': '#808000',
    'olivedrab': '#6b8e23',
    'orange': '#ffa500',
    'orangered': '#ff4500',
    'orchid': '#da70d6',
    'palegoldenrod': '#eee8aa',
    'palegreen': '#98fb98',
    'paleturquoise': '#afeeee',
    'palevioletred': '#db7093',
    'papayawhip': '#ffefd5',
    'peachpuff': '#ffdab9',
    'peru': '#cd853f',
    'pink': '#ffc0cb',
    'plum': '#dda0dd',
    'powderblue': '#b0e0e6',
    'purple': '#800080',
    'red': '#ff0000',
    'rosybrown': '#bc8f8f',
    'royalblue': '#4169e1',
    'saddlebrown': '#8b4513',
    'salmon': '#fa8072',
    'sandybrown': '#f4a460',
    'seagreen': '#2e8b57',
    'seashell': '#fff5ee',
    'sienna': '#a0522d',
    'silver': '#c0c0c0',
    'skyblue': '#87ceeb',
    'slateblue': '#6a5acd',
    'slategray': '#708090',
    'slategrey': '#708090',
    'snow': '#fffafa',
    'springgreen': '#00ff7f',
    'steelblue': '#4682b4',
    'tan': '#d2b48c',
    'teal': '#008080',
    'thistle': '#d8bfd8',
    'tomato': '#ff6347',
    'turquoise': '#40e0d0',
    'violet': '#ee82ee',
    'wheat': '#f5deb3',
    'white': '#ffffff',
    'whitesmoke': '#f5f5f5',
    'yellow': '#ffff00',
    'yellowgreen': '#9acd32',
}

colormap = {k: get_color_from_hex(v) for k, v in hex_colormap.items()}

DEPRECATED_CALLERS = []


def deprecated(func=None, msg=''):
    '''This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted the first time
    the function is used.'''

    import inspect
    import functools

    if func is None:
        return functools.partial(deprecated, msg=msg)

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
                ' by %s().' % (
                    func.__name__,
                    func.__code__.co_filename,
                    func.__code__.co_firstlineno + 1,
                    file, line, caller))

            if msg:
                warning = '{}: {}'.format(msg, warning)
            warning = 'Deprecated: ' + warning

            from kivy.logger import Logger
            Logger.warning(warning)
            if func.__doc__:
                Logger.warning(func.__doc__)
        return func(*args, **kwargs)
    return new_func


class SafeList(list):
    '''List with a clear() method.

    .. warning::
        Usage of the iterate() function will decrease your performance.
    '''

    def clear(self):
        del self[:]

    @deprecated
    def iterate(self, reverse=False):
        if reverse:
            return iter(reversed(self))
        return iter(self)


class QueryDict(dict):
    '''QueryDict is a dict() that can be queried with dot.

    ::

        d = QueryDict()
        # create a key named toto, with the value 1
        d.toto = 1
        # it's the same as
        d['toto'] = 1

    .. versionadded:: 1.0.4
    '''

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            return super(QueryDict, self).__getattr__(attr)

    def __setattr__(self, attr, value):
        self.__setitem__(attr, value)


def format_bytes_to_human(size, precision=2):
    '''Format a byte value to a human readable representation (B, KB, MB...).

    .. versionadded:: 1.0.8

    :Parameters:
        `size`: int
            Number that represents the bytes value
        `precision`: int, defaults to 2
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


def _get_platform():
    # On Android sys.platform returns 'linux2', so prefer to check the
    # presence of python-for-android environment variables (ANDROID_ARGUMENT
    # or ANDROID_PRIVATE).
    if 'ANDROID_ARGUMENT' in environ:
        return 'android'
    elif environ.get('KIVY_BUILD', '') == 'ios':
        return 'ios'
    elif _sys_platform in ('win32', 'cygwin'):
        return 'win'
    elif _sys_platform == 'darwin':
        return 'macosx'
    elif _sys_platform.startswith('linux'):
        return 'linux'
    elif _sys_platform.startswith('freebsd'):
        return 'linux'
    return 'unknown'


platform = _get_platform()
'''
A string identifying the current operating system. It is one
of: `'win'`, `'linux'`, `'android'`, `'macosx'`, `'ios'` or `'unknown'`.
You can use it as follows::

    from kivy.utils import platform
    if platform == 'linux':
        do_linux_things()

.. versionadded:: 1.3.0

.. versionchanged:: 1.8.0

    platform is now a variable instead of a function.
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
    return text.replace('&', '&amp;').replace('[', '&bl;').replace(']', '&br;')


class reify(object):
    '''
    Put the result of a method which uses this (non-data) descriptor decorator
    in the instance dict after the first call, effectively replacing the
    decorator with an instance variable.

    It acts like @property, except that the function is only ever called once;
    after that, the value is cached as a regular attribute. This gives you lazy
    attribute creation on objects that are meant to be immutable.

    Taken from the `Pyramid project <https://pypi.python.org/pypi/pyramid/>`_.

    To use this as a decorator::

         @reify
         def lazy(self):
              ...
              return hard_to_compute_int
         first_time = self.lazy   # lazy is reify obj, reify.__get__() runs
         second_time = self.lazy  # lazy is hard_to_compute_int
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
