'''
Parser utilities
================

Helper functions used for CSS parsing.
'''

__all__ = ('parse_color', 'parse_int', 'parse_float',
           'parse_string', 'parse_bool', 'parse_int2',
           'parse_float4', 'parse_filename')

import re
from kivy.logger import Logger
from kivy.resources import resource_find


class ColorException(Exception):
    pass


def parse_filename(filename):
    '''Parse a filename and search for it using `resource_find()`.
    If found, the resource path is returned, otherwise return the unmodified
    filename (as specified by the caller).'''
    filename = parse_string(filename)
    result = resource_find(filename)
    if result is None:
        Logger.error('Resource: unable to find <%s>' % filename)
    return result or filename


def color_error(text):
    # show warning and return a sane value
    Logger.warning(text)
    return (0, 0, 0, 1)


def parse_color(text):
    '''Parse a string to a kivy color. Supported formats:

        * rgb(r, g, b)
        * rgba(r, g, b, a)
        * rgb
        * rgba
        * rrggbb
        * rrggbbaa

    For hexadecimal values, you case also use:

        * #rgb
        * #rgba
        * #rrggbb
        * #rrggbbaa
    '''
    value = [1, 1, 1, 1]
    if text.startswith('rgb'):
        res = re.match('rgba?\((.*)\)', text)
        if res:
            try:
                # default r/g/b values to 1 if greater than 255 else x/255
                value = [1 if int(x) > 255. else (int(x) / 255.)
                         for x in re.split(',\ ?', res.groups()[0])]
                if len(value) < 3:
                    # in case of invalid input like rgb()/rgb(r)/rgb(r, g)
                    raise ValueError
            except ValueError:
                return color_error('ColorParser: Invalid color for %r' % text)
            except AttributeError:
                return color_error('ColorParser: Invalid color for %r' % text)
        else:
            return color_error('ColorParser: Invalid color for %r' % text)
        if len(value) == 3:
            value.append(1.)
    elif len(text):
        res = text
        if text[0] == '#':
            res = text[1:]
        lres = len(res)
        if lres == 3 or lres == 4:
            res = ''.join([x + x for x in res])
        elif lres != 6 and lres != 8:
            # raise ColorException('Invalid color format for %r' % text)
            return color_error(
                'ColorParser: Invalid color format for %r' % text)
        try:
            value = [int(res[i:i + 2], 16) / 255.
                     for i in range(0, len(res), 2)]
        except ValueError:
            return color_error('ColorParser: Invalid color for %r' % text)
        if lres == 6 or lres == 3:
            value.append(1.)
    return value


def parse_bool(text):
    '''Parse a string to a boolean, ignoring case. "true"/"1" is True,
    "false"/"0" is False. Anything else throws an exception.'''
    if text.lower() in ('true', '1'):
        return True
    elif text.lower() in ('false', '0'):
        return False
    raise Exception('Invalid boolean: %s' % text)


def parse_string(text):
    '''Parse a string to a string (removing single and double quotes).'''
    if len(text) >= 2 and text[0] in ('"', "'") and text[-1] in ('"', "'"):
        text = text[1:-1]
    return text.strip()


def parse_int2(text):
    '''Parse a string to a list of exactly 2 integers.

        >>> print(parse_int2("12 54"))
        12, 54

    '''
    texts = [x for x in text.split(' ') if x.strip() != '']
    value = list(map(parse_int, texts))
    if len(value) < 1:
        raise Exception('Invalid int2 format: %s' % text)
    elif len(value) == 1:
        return [value[0], value[0]]
    elif len(value) > 2:
        raise Exception('Too many values in %s: %s' % (text, str(value)))
    return value


def parse_float4(text):
    '''Parse a string to a list of exactly 4 floats.

        >>> parse_float4('54 87. 35 0')
        54, 87., 35, 0

    '''
    texts = [x for x in text.split(' ') if x.strip() != '']
    value = list(map(parse_float, texts))
    if len(value) < 1:
        raise Exception('Invalid float4 format: %s' % text)
    elif len(value) == 1:
        return [value[0] for x in range(4)]
    elif len(value) == 2:
        return [value[0], value[1], value[0], value[1]]
    elif len(value) == 3:
        # ambiguous case!
        return [value[0], value[1], value[0], value[2]]
    elif len(value) > 4:
        raise Exception('Too many values in %s' % text)
    return value


parse_int = int
parse_float = float
