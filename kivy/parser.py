'''
Parser utilities
================

Helper functions used for CSS
'''

__all__ = ('parse_image', 'parse_color', 'parse_int', 'parse_float',
           'parse_string', 'parse_bool', 'parse_int2',
           'parse_float4', 'parse_filename')

import re
from kivy.logger import Logger
from kivy.resources import resource_find
from kivy.core.image import Image
from kivy.core.svg import Svg


def parse_filename(filename):
    '''Parse a filename and search for it using `resource_find()`.
    If found, the resource path is returned, otherwise return the unmodified
    filename (as specified by the caller).'''
    filename = parse_string(filename)
    result = resource_find(filename)
    if result is None:
        Logger.error('Resource: unable to found <%s>' % filename)
    return result or filename


def parse_image(filename):
    '''Parse a filename and load it in a Widget (Image or Svg).
    Svg is used only if the file extension is '.svg', otherwise Image.'''
    filename = parse_filename(filename)
    if filename in (None, 'None', u'None'):
        return None
    if filename.lower().endswith('.svg'):
        return Svg(filename)
    else:
        return Image(filename)
    raise Exception('Error trying to load image specified in css: %s' \
                    % filename)


def parse_color(text):
    '''Parse a string to a kivy color. Supported formats :
        * rgb(r, g, b)
        * rgba(r, g, b, a)
        * #aaa
        * #rrggbb
    '''
    value = [1, 1, 1, 1]
    if text.startswith('rgb'):
        res = re.match('rgba?\((.*)\)', text)
        value = map(lambda x: int(x) / 255., re.split(',\ ?', res.groups()[0]))
        if len(value) == 3:
            value.append(1.)
    elif text.startswith('#'):
        res = text[1:]
        if len(res) == 3:
            res = ''.join(map(lambda x: x+x, res))
        value = [int(x, 16) / 255. for x in re.split(
                 '(?i)([0-9a-f]{2})', res) if x != '']
        if len(value) == 3:
            value.append(1.)
    return value


def parse_bool(text):
    '''Parse a string to a boolean, ignoring case. "true"/"1" is True, "false"/"0"
       is False. Anything else throws an exception.'''
    if text.lower() in ('true', '1'):
        return True
    elif text.lower() in ('false', '0'):
        return False
    raise Exception('Invalid boolean: %s' % text)


def parse_string(text):
    '''Parse a string to a string (remove single and double quotes)'''
    if len(text) >= 2 and text[0] in ('"', "'") and text[-1] in ('"', "'"):
        text = text[1:-1]
    return text.strip()


def parse_int2(text):
    '''Parse a string to a list of exactly 2 integers

        >>> print parse_int2("12 54")
        12, 54

    '''
    texts = [x for x in text.split(' ') if x.strip() != '']
    value = map(parse_int, texts)
    if len(value) < 1:
        raise Exception('Invalid int2 format: %s' % text)
    elif len(value) == 1:
        return [value[0], value[0]]
    elif len(value) > 2:
        raise Exception('Too many values in %s: %s' % (text, str(value)))
    return value


def parse_float4(text):
    '''Parse a string to a list of exactly 4 floats

        >>> parse_float4('54 87. 35 0')
        54, 87., 35, 0

    '''
    texts = [x for x in text.split(' ') if x.strip() != '']
    value = map(parse_float, texts)
    if len(value) < 1:
        raise Exception('Invalid float4 format: %s' % text)
    elif len(value) == 1:
        return map(lambda x: value[0], range(4))
    elif len(value) == 2:
        return [value[0], value[1], value[0], value[1]]
    elif len(value) == 3:
        # ambigous case!
        return [value[0], value[1], value[0], value[2]]
    elif len(value) > 4:
        raise Exception('Too many values in %s' % text)
    return value

parse_int = int
parse_float = float

