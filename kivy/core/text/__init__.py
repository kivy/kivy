'''
Text
====

An abstraction of text creation. Depending of the selected backend, the
accuracy of text rendering may vary.

.. versionchanged:: 1.10.1
    :meth:`LabelBase.find_base_direction` added.

.. versionchanged:: 1.5.0
    :attr:`LabelBase.line_height` added.

.. versionchanged:: 1.0.7
    The :class:`LabelBase` does not generate any texture if the text has a
    width <= 1.

This is the backend layer for rendering text with different text providers,
you should only be using this directly if your needs aren't fulfilled by the
:class:`~kivy.uix.label.Label`.

Usage example::

    from kivy.core.text import Label as CoreLabel

    ...
    ...
    my_label = CoreLabel()
    my_label.text = 'hello'
    # the label is usually not drawn until needed, so force it to draw.
    my_label.refresh()
    # Now access the texture of the label and use it wherever and
    # however you may please.
    hello_texture = my_label.texture


Font Context Manager
====================

A font context is a namespace where multiple fonts are loaded; if a font is
missing a glyph needed to render text, it can fall back to a different font in
the same context. The font context manager can be used to query and manipulate
the state of font contexts when using the Pango text provider (no other
provider currently implements it).

.. versionadded:: 1.11.0

.. warning:: This feature requires the Pango text provider.

Font contexts can be created automatically by :class:`kivy.uix.label.Label` or
:class:`kivy.uix.textinput.TextInput`; if a non-existant context is used in
one of these classes, it will be created automatically, or if a font file is
specified without a context (this creates an isolated context, without
support for fallback).

Usage example::

    from kivy.uix.label import Label
    from kivy.core.text import FontContextManager as FCM

    # Create a font context containing system fonts + one custom TTF
    FCM.create('system://myapp')
    family = FCM.add_font('/path/to/file.ttf')

    # These are now interchangeable ways to refer to the custom font:
    lbl1 = Label(font_context='system://myapp', family_name=family)
    lbl2 = Label(font_context='system://myapp', font_name='/path/to/file.ttf')

    # You could also refer to a system font by family, since this is a
    # system:// font context
    lbl3 = Label(font_context='system://myapp', family_name='Arial')
'''

__all__ = ('LabelBase', 'Label',
           'FontContextManagerBase', 'FontContextManager')

import re
import os
from ast import literal_eval
from functools import partial
from copy import copy
from kivy import kivy_data_dir
from kivy.config import Config
from kivy.utils import platform
from kivy.graphics.texture import Texture
from kivy.core import core_select_lib
from kivy.core.text.text_layout import layout_text, LayoutWord
from kivy.resources import resource_find, resource_add_path
from kivy.compat import PY2
from kivy.setupconfig import USE_SDL2, USE_PANGOFT2


if 'KIVY_DOC' not in os.environ:
    _default_font_paths = literal_eval(Config.get('kivy', 'default_font'))
    DEFAULT_FONT = _default_font_paths.pop(0)
else:
    DEFAULT_FONT = None

FONT_REGULAR = 0
FONT_ITALIC = 1
FONT_BOLD = 2
FONT_BOLDITALIC = 3

whitespace_pat = re.compile('( +)')


class LabelBase(object):
    '''Core text label.
    This is the abstract class used by different backends to render text.

    .. warning::
        The core text label can't be changed at runtime. You must recreate one.

    :Parameters:
        `font_size`: int, defaults to 12
            Font size of the text
        `font_context`: str, defaults to None
            Context for the specified font (see :class:`kivy.uix.label.Label`
            for details). `None` will autocreate an isolated context named
            after the resolved font file.
        `font_name`: str, defaults to DEFAULT_FONT
            Font name of the text
        `font_family`: str, defaults to None
            Font family name to request for drawing, this can only be used
            with `font_context`.
        `bold`: bool, defaults to False
            Activate "bold" text style
        `italic`: bool, defaults to False
            Activate "italic" text style
        `text_size`: tuple, defaults to (None, None)
            Add constraint to render the text (inside a bounding box).
            If no size is given, the label size will be set to the text size.
        `padding`: float, defaults to None
            If it's a float, it will set padding_x and padding_y
        `padding_x`: float, defaults to 0.0
            Left/right padding
        `padding_y`: float, defaults to 0.0
            Top/bottom padding
        `halign`: str, defaults to "left"
            Horizontal text alignment inside the bounding box
        `valign`: str, defaults to "bottom"
            Vertical text alignment inside the bounding box
        `shorten`: bool, defaults to False
            Indicate whether the label should attempt to shorten its textual
            contents as much as possible if a `size` is given.
            Setting this to True without an appropriately set size will lead to
            unexpected results.
        `shorten_from`: str, defaults to `center`
            The side from which we should shorten the text from, can be left,
            right, or center. E.g. if left, the ellipsis will appear towards
            the left side and it will display as much text starting from the
            right as possible.
        `split_str`: string, defaults to `' '` (space)
            The string to use to split the words by when shortening. If empty,
            we can split after every character filling up the line as much as
            possible.
        `max_lines`: int, defaults to 0 (unlimited)
            If set, this indicate how maximum line are allowed to render the
            text. Works only if a limitation on text_size is set.
        `mipmap`: bool, defaults to False
            Create a mipmap for the texture
        `strip`: bool, defaults to False
            Whether each row of text has its leading and trailing spaces
            stripped. If `halign` is `justify` it is implicitly True.
        `strip_reflow`: bool, defaults to True
            Whether text that has been reflowed into a second line should
            be stripped, even if `strip` is False. This is only in effect when
            `size_hint_x` is not None, because otherwise lines are never
            split.
        `unicode_errors`: str, defaults to `'replace'`
            How to handle unicode decode errors. Can be `'strict'`, `'replace'`
            or `'ignore'`.
        `outline_width`: int, defaults to None
            Width in pixels for the outline.
        `outline_color`: tuple, defaults to (0, 0, 0)
            Color of the outline.
        `font_features`: str, defaults to None
            OpenType font features in CSS format (Pango only)
        `base_direction`: str, defaults to None (auto)
            Text direction, one of `None`, `'ltr'`, `'rtl'`, `'weak_ltr'`,
            or `'weak_rtl'` (Pango only)
        `text_language`: str, defaults to None (user locale)
            RFC-3066 format language tag as a string (Pango only)

    .. versionchanged:: 1.10.1
        `font_context`, `font_family`, `font_features`, `base_direction`
        and `text_language` were added.

    .. versionchanged:: 1.10.0
        `outline_width` and `outline_color` were added.

    .. versionchanged:: 1.9.0
        `strip`, `strip_reflow`, `shorten_from`, `split_str`, and
        `unicode_errors` were added.

    .. versionchanged:: 1.9.0
        `padding_x` and `padding_y` has been fixed to work as expected.
        In the past, the text was padded by the negative of their values.

    .. versionchanged:: 1.8.0
        `max_lines` parameters has been added.

    .. versionchanged:: 1.0.8
        `size` have been deprecated and replaced with `text_size`.

    .. versionchanged:: 1.0.7
        The `valign` is now respected. This wasn't the case previously
        so you might have an issue in your application if you have not
        considered this.

    '''

    __slots__ = ('options', 'texture', '_label', '_text_size')

    _cached_lines = []

    _fonts = {}

    _fonts_cache = {}

    _fonts_dirs = []

    _font_dirs_files = []

    _texture_1px = None

    _font_family_support = False

    def __init__(
        self, text='', font_size=12, font_name=DEFAULT_FONT, bold=False,
        italic=False, underline=False, strikethrough=False, font_family=None,
        halign='left', valign='bottom', shorten=False,
        text_size=None, mipmap=False, color=None, line_height=1.0, strip=False,
        strip_reflow=True, shorten_from='center', split_str=' ',
        unicode_errors='replace',
        font_hinting='normal', font_kerning=True, font_blended=True,
        outline_width=None, outline_color=None, font_context=None,
        font_features=None, base_direction=None, text_language=None,
        **kwargs):

        # Include system fonts_dir in resource paths.
        # This allows us to specify a font from those dirs.
        LabelBase.get_system_fonts_dir()

        options = {'text': text, 'font_size': font_size,
                   'font_name': font_name, 'bold': bold, 'italic': italic,
                   'underline': underline, 'strikethrough': strikethrough,
                   'font_family': font_family,
                   'halign': halign, 'valign': valign, 'shorten': shorten,
                   'mipmap': mipmap, 'line_height': line_height,
                   'strip': strip, 'strip_reflow': strip_reflow,
                   'shorten_from': shorten_from, 'split_str': split_str,
                   'unicode_errors': unicode_errors,
                   'font_hinting': font_hinting,
                   'font_kerning': font_kerning,
                   'font_blended': font_blended,
                   'outline_width': outline_width,
                   'font_context': font_context,
                   'font_features': font_features,
                   'base_direction': base_direction,
                   'text_language': text_language}

        kwargs_get = kwargs.get
        options['color'] = color or (1, 1, 1, 1)
        options['outline_color'] = outline_color or (0, 0, 0, 1)
        options['padding'] = kwargs_get('padding', (0, 0))
        if not isinstance(options['padding'], (list, tuple)):
            options['padding'] = (options['padding'], options['padding'])
        options['padding_x'] = kwargs_get('padding_x', options['padding'][0])
        options['padding_y'] = kwargs_get('padding_y', options['padding'][1])

        if 'size' in kwargs:
            options['text_size'] = kwargs['size']
        else:
            if text_size is None:
                options['text_size'] = (None, None)
            else:
                options['text_size'] = text_size

        self._text_size = options['text_size']
        self._text = options['text']
        self._internal_size = 0, 0  # the real computed text size (inclds pad)
        self._cached_lines = []

        self.options = options
        self.texture = None
        self.is_shortened = False
        self.resolve_font_name()

    @staticmethod
    def register(name, fn_regular, fn_italic=None, fn_bold=None,
                 fn_bolditalic=None):
        '''Register an alias for a Font.

        .. versionadded:: 1.1.0

        If you're using a ttf directly, you might not be able to use the
        bold/italic properties of
        the ttf version. If the font is delivered in multiple files
        (one regular, one italic and one bold), then you need to register these
        files and use the alias instead.

        All the fn_regular/fn_italic/fn_bold parameters are resolved with
        :func:`kivy.resources.resource_find`. If fn_italic/fn_bold are None,
        fn_regular will be used instead.
        '''

        fonts = []

        for font_type in fn_regular, fn_italic, fn_bold, fn_bolditalic:
            if font_type is not None:
                font = resource_find(font_type)

                if font is None:
                    raise IOError('File {0} not found'.format(font_type))
                else:
                    fonts.append(font)
            else:
                fonts.append(fonts[0])  # add regular font to list again

        LabelBase._fonts[name] = tuple(fonts)

    def resolve_font_name(self):
        options = self.options
        fontname = options['font_name']
        fonts = self._fonts
        fontscache = self._fonts_cache

        if self._font_family_support and options['font_family']:
            options['font_name_r'] = None
            return

        # is the font registered?
        if fontname in fonts:
            # return the preferred font for the current bold/italic combination
            italic = int(options['italic'])
            if options['bold']:
                bold = FONT_BOLD
            else:
                bold = FONT_REGULAR

            options['font_name_r'] = fonts[fontname][italic | bold]

        elif fontname in fontscache:
            options['font_name_r'] = fontscache[fontname]
        else:
            filename = resource_find(fontname)
            if not filename and not fontname.endswith('.ttf'):
                fontname = '{}.ttf'.format(fontname)
                filename = resource_find(fontname)

            if filename is None:
                # XXX for compatibility, check directly in the data dir
                filename = pep8_fn = os.path.join(kivy_data_dir, fontname)
                if not os.path.exists(pep8_fn) or not os.path.isfile(pep8_fn):
                    raise IOError('Label: File %r not found' % fontname)
            fontscache[fontname] = filename
            options['font_name_r'] = filename

    @staticmethod
    def get_system_fonts_dir():
        '''Return the directories used by the system for fonts.
        '''
        if LabelBase._fonts_dirs:
            return LabelBase._fonts_dirs

        fdirs = []
        if platform == 'linux':
            fdirs = [
                '/usr/share/fonts', '/usr/local/share/fonts',
                os.path.expanduser('~/.fonts'),
                os.path.expanduser('~/.local/share/fonts')]
        elif platform == 'macosx':
            fdirs = ['/Library/Fonts', '/System/Library/Fonts',
                     os.path.expanduser('~/Library/Fonts')]
        elif platform == 'win':
            fdirs = [os.path.join(os.environ['SYSTEMROOT'], 'Fonts')]
        elif platform == 'ios':
            fdirs = ['/System/Library/Fonts']
        elif platform == 'android':
            fdirs = ['/system/fonts']
        else:
            raise Exception("Unknown platform: {}".format(platform))

        fdirs.append(os.path.join(kivy_data_dir, 'fonts'))
        # register the font dirs
        rdirs = []
        _font_dir_files = []
        for fdir in fdirs:
            for _dir, dirs, files in os.walk(fdir):
                _font_dir_files.extend(files)
                resource_add_path(_dir)
                rdirs.append(_dir)
        LabelBase._fonts_dirs = rdirs
        LabelBase._font_dirs_files = _font_dir_files

        return rdirs

    def get_extents(self, text):
        '''Return a tuple (width, height) indicating the size of the specified
        text'''
        return (0, 0)

    def get_cached_extents(self):
        '''Returns a cached version of the :meth:`get_extents` function.

        ::

            >>> func = self._get_cached_extents()
            >>> func
            <built-in method size of pygame.font.Font object at 0x01E45650>
            >>> func('a line')
            (36, 18)

        .. warning::

            This method returns a size measuring function that is valid
            for the font settings used at the time :meth:`get_cached_extents`
            was called. Any change in the font settings will render the
            returned function incorrect. You should only use this if you know
            what you're doing.

        .. versionadded:: 1.9.0
        '''
        return self.get_extents

    def _render_begin(self):
        pass

    def _render_text(self, text, x, y):
        pass

    def _render_end(self):
        pass

    def shorten(self, text, margin=2):
        ''' Shortens the text to fit into a single line by the width specified
        by :attr:`text_size` [0]. If :attr:`text_size` [0] is None, it returns
        text text unchanged.

        :attr:`split_str` and :attr:`shorten_from` determines how the text is
        shortened.

        :params:

            `text` str, the text to be shortened.
            `margin` int, the amount of space to leave between the margins
            and the text. This is in addition to :attr:`padding_x`.

        :returns:
            the text shortened to fit into a single line.
        '''
        textwidth = self.get_cached_extents()
        uw = self.text_size[0]
        if uw is None or not text:
            return text

        opts = self.options
        uw = max(0, int(uw - opts['padding_x'] * 2 - margin))
        # if larger, it won't fit so don't even try extents
        chr = type(text)
        text = text.replace(chr('\n'), chr(' '))
        if len(text) <= uw and textwidth(text)[0] <= uw:
            return text
        c = opts['split_str']
        offset = 0 if len(c) else 1
        dir = opts['shorten_from'][0]
        elps = textwidth('...')[0]
        if elps > uw:
            self.is_shortened = True
            if textwidth('..')[0] <= uw:
                return '..'
            else:
                return '.'
        uw -= elps

        f = partial(text.find, c)
        f_rev = partial(text.rfind, c)
        # now find the first and last word
        e1, s2 = f(), f_rev()

        if dir != 'l':  # center or right
            # no split, or the first word doesn't even fit
            if e1 != -1:
                l1 = textwidth(text[:e1])[0]
                l2 = textwidth(text[s2 + 1:])[0]
            if e1 == -1 or l1 + l2 > uw:
                self.is_shortened = True
                if len(c):
                    opts['split_str'] = ''
                    res = self.shorten(text, margin)
                    opts['split_str'] = c
                    return res
                # at this point we do char by char so e1 must be zero
                if l1 <= uw:
                    return chr('{0}...').format(text[:e1])
                return chr('...')

            # both word fits, and there's at least on split_str
            if s2 == e1:  # there's only on split_str
                self.is_shortened = True
                return chr('{0}...{1}').format(text[:e1], text[s2 + 1:])

            # both the first and last word fits, and they start/end at diff pos
            if dir == 'r':
                ee1 = f(e1 + 1)
                while l2 + textwidth(text[:ee1])[0] <= uw:
                    e1 = ee1
                    if e1 == s2:
                        break
                    ee1 = f(e1 + 1)
            else:
                while True:
                    if l1 <= l2:
                        ee1 = f(e1 + 1)
                        l1 = textwidth(text[:ee1])[0]
                        if l2 + l1 > uw:
                            break
                        e1 = ee1
                        if e1 == s2:
                            break
                    else:
                        ss2 = f_rev(0, s2 - offset)
                        l2 = textwidth(text[ss2 + 1:])[0]
                        if l2 + l1 > uw:
                            break
                        s2 = ss2
                        if e1 == s2:
                            break
        else:  # left
            # no split, or the last word doesn't even fit
            if s2 != -1:
                l2 = textwidth(text[s2 + (1 if len(c) else -1):])[0]
                l1 = textwidth(text[:max(0, e1)])[0]
            # if split_str
            if s2 == -1 or l2 + l1 > uw:
                self.is_shortened = True
                if len(c):
                    opts['split_str'] = ''
                    res = self.shorten(text, margin)
                    opts['split_str'] = c
                    return res

                return chr('...')

            # both word fits, and there's at least on split_str
            if s2 == e1:  # there's only on split_str
                self.is_shortened = True
                return chr('{0}...{1}').format(text[:e1], text[s2 + 1:])

            # both the first and last word fits, and they start/end at diff pos
            ss2 = f_rev(0, s2 - offset)
            while l1 + textwidth(text[ss2 + 1:])[0] <= uw:
                s2 = ss2
                if s2 == e1:
                    break
                ss2 = f_rev(0, s2 - offset)

        self.is_shortened = True
        return chr('{0}...{1}').format(text[:e1], text[s2 + 1:])

    def _default_line_options(self, lines):
        for line in lines:
            if len(line.words):  # get opts from first line, first word
                return line.words[0].options
        return None

    def clear_texture(self):
        self._render_begin()
        data = self._render_end()
        assert(data)
        if data is not None and data.width > 1:
            self.texture.blit_data(data)
        return

    # FIXME: This should possibly use a Config value, and possibly we should
    #        expose pango_unichar_direction() / pango_bidi_type_for_unichar()
    @staticmethod
    def find_base_direction(text):
        '''Searches a string the first character that has a strong direction,
        according to the Unicode bidirectional algorithm. Returns `None` if
        the base direction cannot be determined, or one of `'ltr'` or `'rtl'`.

        .. versionadded: 1.10.1

        .. note:: This feature requires the Pango text provider.
        '''
        return 'ltr'

    def render_lines(self, lines, options, render_text, y, size):
        get_extents = self.get_cached_extents()
        uw, uh = options['text_size']
        xpad = options['padding_x']
        if uw is not None:
            uww = uw - 2 * xpad  # real width of just text
        w = size[0]
        sw = options['space_width']
        halign = options['halign']
        split = re.split
        find_base_dir = self.find_base_direction
        cur_base_dir = options['base_direction']

        for layout_line in lines:  # for plain label each line has only one str
            lw, lh = layout_line.w, layout_line.h
            line = ''
            assert len(layout_line.words) < 2
            if len(layout_line.words):
                last_word = layout_line.words[0]
                line = last_word.text
                if not cur_base_dir:
                    cur_base_dir = find_base_dir(line)
            x = xpad
            if halign == 'auto':
                if cur_base_dir and 'rtl' in cur_base_dir:
                    x = max(0, int(w - lw - xpad))  # right-align RTL text
            elif halign == 'center':
                x = int((w - lw) / 2.)
            elif halign == 'right':
                x = max(0, int(w - lw - xpad))

            # right left justify
            # divide left over space between `spaces`
            # TODO implement a better method of stretching glyphs?
            if (uw is not None and halign == 'justify' and line and not
                    layout_line.is_last_line):
                # number spaces needed to fill, and remainder
                n, rem = divmod(max(uww - lw, 0), sw)
                n = int(n)
                words = None
                if n or rem:
                    # there's no trailing space when justify is selected
                    words = split(whitespace_pat, line)
                if words is not None and len(words) > 1:
                    space = type(line)(' ')
                    # words: every even index is spaces, just add ltr n spaces
                    for i in range(n):
                        idx = (2 * i + 1) % (len(words) - 1)
                        words[idx] = words[idx] + space
                    if rem:
                        # render the last word at the edge, also add it to line
                        ext = get_extents(words[-1])
                        word = LayoutWord(last_word.options, ext[0], ext[1],
                                          words[-1])
                        layout_line.words.append(word)
                        last_word.lw = uww - ext[0]  # word was stretched
                        render_text(words[-1], x + last_word.lw, y)
                        last_word.text = line = ''.join(words[:-2])
                    else:
                        last_word.lw = uww  # word was stretched
                        last_word.text = line = ''.join(words)
                    layout_line.w = uww  # the line occupies full width

            if len(line):
                layout_line.x = x
                layout_line.y = y
                render_text(line, x, y)
            y += lh
        return y

    def _render_real(self):
        lines = self._cached_lines
        options = self._default_line_options(lines)
        if options is None:  # there was no text to render
            return self.clear_texture()

        old_opts = self.options
        ih = self._internal_size[1]  # the real size of text, not texture
        size = self.size
        valign = options['valign']

        y = ypad = options['padding_y']  # pos in the texture
        if valign == 'bottom':
            y = size[1] - ih + ypad
        elif valign == 'middle' or valign == 'center':
            y = int((size[1] - ih) / 2 + ypad)

        self._render_begin()
        self.render_lines(lines, options, self._render_text, y, size)

        # get data from provider
        data = self._render_end()
        assert(data)
        self.options = old_opts

        # If the text is 1px width, usually, the data is black.
        # Don't blit that kind of data, otherwise, you have a little black bar.
        if data is not None and data.width > 1:
            self.texture.blit_data(data)

    def render(self, real=False):
        '''Return a tuple (width, height) to create the image
        with the user constraints. (width, height) includes the padding.
        '''
        if real:
            return self._render_real()

        options = copy(self.options)
        options['space_width'] = self.get_extents(' ')[0]
        options['strip'] = strip = (options['strip'] or
                                    options['halign'] == 'justify')
        uw, uh = options['text_size'] = self._text_size
        text = self.text
        if strip:
            text = text.strip()

        self.is_shortened = False
        if uw is not None and options['shorten']:
            text = self.shorten(text)

        self._cached_lines = lines = []
        if not text:
            return 0, 0

        if uh is not None and (options['valign'] == 'middle' or
                               options['valign'] == 'center'):
            center = -1  # pos of newline
            if len(text) > 1:
                middle = int(len(text) // 2)
                l, r = text.rfind('\n', 0, middle), text.find('\n', middle)
                if l != -1 and r != -1:
                    center = l if center - l <= r - center else r
                elif l != -1:
                    center = l
                elif r != -1:
                    center = r
            # if a newline split text, render from center down and up til uh
            if center != -1:
                # layout from center down until half uh
                w, h, clipped = layout_text(text[center + 1:], lines, (0, 0),
                (uw, uh / 2), options, self.get_cached_extents(), True, True)
                # now layout from center upwards until uh is reached
                w, h, clipped = layout_text(text[:center + 1], lines, (w, h),
                (uw, uh), options, self.get_cached_extents(), False, True)
            else:  # if there's no new line, layout everything
                w, h, clipped = layout_text(text, lines, (0, 0), (uw, None),
                options, self.get_cached_extents(), True, True)
        else:  # top or bottom
            w, h, clipped = layout_text(text, lines, (0, 0), (uw, uh), options,
                self.get_cached_extents(), options['valign'] == 'top', True)
        self._internal_size = w, h
        if uw:
            w = uw
        if uh:
            h = uh
        if h > 1 and w < 2:
            w = 2
        return int(w), int(h)

    def _texture_refresh(self, *l):
        self.refresh()

    def _texture_fill(self, texture):
        # second pass, render for real
        self.render(real=True)

    def refresh(self):
        '''Force re-rendering of the text
        '''
        self.resolve_font_name()

        # first pass, calculating width/height
        sz = self.render()
        self._size_texture = sz
        self._size = (sz[0], sz[1])

        # if no text are rendered, return nothing.
        width, height = self._size
        if width <= 1 or height <= 1:
            self.texture = self.texture_1px
            return

        # create a delayed texture
        texture = self.texture
        if texture is None or \
                width != texture.width or \
                height != texture.height:
            texture = Texture.create(size=(width, height),
                                     mipmap=self.options['mipmap'],
                                     callback=self._texture_fill)
            texture.flip_vertical()
            texture.add_reload_observer(self._texture_refresh)
            self.texture = texture
        else:
            texture.ask_update(self._texture_fill)

    def _get_text(self):
        return self._text

    def _set_text(self, text):
        if text != self._text:
            self._text = text

    text = property(_get_text, _set_text, doc='Get/Set the text')
    label = property(_get_text, _set_text, doc='Get/Set the text')

    @property
    def texture_1px(self):
        if LabelBase._texture_1px is None:
            tex = Texture.create(size=(1, 1), colorfmt='rgba')
            tex.blit_buffer(b'\x00\x00\x00\x00', colorfmt='rgba')
            LabelBase._texture_1px = tex
        return LabelBase._texture_1px

    @property
    def size(self):
        return self._size

    @property
    def width(self):
        return self._size[0]

    @property
    def height(self):
        return self._size[1]

    @property
    def content_width(self):
        '''Return the content width; i.e. the width of the text without
        any padding.'''
        if self.texture is None:
            return 0
        return self.texture.width - 2 * self.options['padding_x']

    @property
    def content_height(self):
        '''Return the content height; i.e. the height of the text without
        any padding.'''
        if self.texture is None:
            return 0
        return self.texture.height - 2 * self.options['padding_y']

    @property
    def content_size(self):
        '''Return the content size (width, height)'''
        if self.texture is None:
            return (0, 0)
        return (self.content_width, self.content_height)

    @property
    def fontid(self):
        '''Return a unique id for all font parameters'''
        return str([self.options[x] for x in (
            'font_size', 'font_name_r', 'bold',
            'italic', 'underline', 'strikethrough')])

    def _get_text_size(self):
        return self._text_size

    def _set_text_size(self, x):
        self._text_size = x

    text_size = property(_get_text_size, _set_text_size,
                         doc='''Get/set the (width, height) of the '
                         'contrained rendering box''')

    usersize = property(_get_text_size, _set_text_size,
                        doc='''(deprecated) Use text_size instead.''')


class FontContextManagerBase(object):
    @staticmethod
    def create(font_context):
        '''Create a font context, you must specify a unique name (string).
        Returns `True` on success and `False` on failure.

        If `font_context` starts with one of the reserved words `'system://'`,
        `'directory://'`, `'fontconfig://'` or `'systemconfig://'`, the context
        is setup accordingly (exact results of this depends on your platform,
        environment and configuration).

        * `'system://'` loads the default system's FontConfig configuration
          and all fonts (usually including user fonts).
        * `directory://` contexts preload a directory of font files (specified
          in the context name), `systemconfig://` loads the system's FontConfig
          configuration (but no fonts), and `fontconfig://` loads FontConfig
          configuration file (specified in the context name!). These are for
          advanced users only, check the source code and FontConfig
          documentation for details.
        * Fonts automatically loaded to an isolated context (ie when no
          font context was specified) start with `'isolated://'`. This has
          no special effect, and only serves to help you identify them in
          the results returned from :meth:`list`.
        * Any other string is a context that will only draw with the font
          file(s) you explicitly add to it.

        .. versionadded:: 1.11.0

        .. note::
            Font contexts are created automatically by specifying a name in the
            `font_context` property of :class:`kivy.uix.label.Label` or
            :class:`kivy.uix.textinput.TextInput`. They are also auto-created
            by :meth:`add_font` by default, so you normally don't need to
            call this directly.

        .. note:: This feature requires the Pango text provider.
        '''
        raise NotImplementedError("No font_context support in text provider")

    @staticmethod
    def exists(font_context):
        '''Returns True if a font context with the given name exists.

        .. versionadded:: 1.11.0

        .. note:: This feature requires the Pango text provider.
        '''
        raise NotImplementedError("No font_context support in text provider")

    @staticmethod
    def destroy(font_context):
        '''Destroy a named font context (if it exists)

        .. versionadded:: 1.11.0

        .. note:: This feature requires the Pango text provider.
        '''
        raise NotImplementedError("No font_context support in text provider")

    @staticmethod
    def list():
        '''Returns a list of `bytes` objects, each representing a cached font
        context name. Note that entries that start with `isolated://` were
        autocreated by loading a font file with no font_context specified.

        .. versionadded:: 1.11.0

        .. note:: This feature requires the Pango text provider.
        '''
        raise NotImplementedError("No font_context support in text provider")

    @staticmethod
    def list_families(font_context):
        '''Returns a list of `bytes` objects, each representing a font family
        name that is available in the given `font_context`.

        .. versionadded:: 1.11.0

        .. note::
            Pango adds static "Serif", "Sans" and "Monospace" to the list in
            current versions, even if only a single custom font file is added
            to the context.

        .. note:: This feature requires the Pango text provider.
        '''
        raise NotImplementedError("No font_context support in text provider")

    @staticmethod
    def list_custom(font_context):
        '''Returns a dictionary representing all the custom-loaded fonts in
        the context. The key is a `bytes` object representing the full path
        to the font file, the value is a `bytes` object representing the font
        family name used to request drawing with the font.

        .. versionadded:: 1.11.0

        .. note:: This feature requires the Pango text provider.
        '''
        raise NotImplementedError("No font_context support in text provider")

    @staticmethod
    def add_font(font_context, filename, autocreate=True, family=None):
        '''Add a font file to a named font context. If `autocreate` is true,
        the context will be created if it does not exist (this is the
        default). You can specify the `family` argument (string) to skip
        auto-detecting the font family name.

        .. warning::

            The `family` argument is slated for removal if the underlying
            implementation can be fixed, It is offered as a way to optimize
            startup time for deployed applications (it avoids opening the
            file with FreeType2 to determine its family name). To use this,
            first load the font file without specifying `family`, and
            hardcode the returned (autodetected) `family` value in your font
            context initialization.

        .. versionadded:: 1.11.0

        .. note:: This feature requires the Pango text provider.
        '''
        raise NotImplementedError("No font_context support in text provider")


# Load the appropriate provider
label_libs = []
if USE_PANGOFT2:
    label_libs += [('pango', 'text_pango', 'LabelPango')]

if USE_SDL2:
    label_libs += [('sdl2', 'text_sdl2', 'LabelSDL2')]
else:
    label_libs += [('pygame', 'text_pygame', 'LabelPygame')]
label_libs += [
    ('pil', 'text_pil', 'LabelPIL')]
Text = Label = core_select_lib('text', label_libs)

if 'KIVY_DOC' not in os.environ:
    if not Label:
        from kivy.logger import Logger
        import sys
        Logger.critical('App: Unable to get a Text provider, abort.')
        sys.exit(1)

    # FIXME: Better way to do this
    if Label.__name__ == 'LabelPango':
        from kivy.core.text.text_pango import PangoFontContextManager
        FontContextManager = PangoFontContextManager()
    else:
        FontContextManager = FontContextManagerBase()


# For the first initialization, register the default font
    Label.register(DEFAULT_FONT, *_default_font_paths)
