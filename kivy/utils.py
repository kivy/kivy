# pylint: disable=W0611
'''
Utils
=====

'''

__all__ = ('intersection', 'difference', 'strtotuple',
           'get_color_from_hex', 'get_random_color',
           'is_color_transparent', 'boundary',
           'interpolate', 'QueryDict', 'platform', 'escape_markup')

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
    return [s for s in set1 if s in set2]

def difference(set1, set2, both=False):
    '''Return difference between 2 list
    .. versionchanged: 1.4.0
        added :data:`both` argument. If true, includes differences
        from both lists
    '''

    if not both:
        return [s for s in set1 if s not in set2]
    else:
        return [s for s in set1 + set2 if s not in set1 or s not in set2]

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


def is_color_transparent(color):
    '''Return true if alpha channel is 0'''
    return len(color) == 4 and color[3] == 0


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

    try:
        import android
        return 'android'
    except ImportError:
        #TODO: implement ios support here
        try:
            import ios
            return 'ios'
        except ImportError:
            if _sys_platform in ('win32', 'cygwin'):
                return 'win'
            elif _sys_platform in ('darwin', ):
                return 'macosx'
            elif _sys_platform in ('linux2', 'linux3'):
                return 'linux'
            else:
                return 'unknown'

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

