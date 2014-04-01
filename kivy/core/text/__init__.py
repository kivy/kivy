'''
Text
====

An abstraction of text creation. Depending of the selected backend, the
accuracy of text rendering may vary.

.. versionchanged:: 1.5.0
    :attr:`LabelBase.line_height` added.

.. versionchanged:: 1.0.7
    The :class:`LabelBase` does not generate any texture if the text has a
    width <= 1.
'''

__all__ = ('LabelBase', 'Label')

import re
import os
from copy import copy
from kivy import kivy_data_dir
from kivy.graphics.texture import Texture
from kivy.core import core_select_lib
from kivy.core.text.text_layout import layout_text, LayoutWord
from kivy.resources import resource_find
from kivy.compat import PY2

DEFAULT_FONT = 'DroidSans'

FONT_REGULAR = 0
FONT_ITALIC = 1
FONT_BOLD = 2
FONT_BOLDITALIC = 3


class LabelBase(object):
    '''Core text label.
    This is the abstract class used by different backends to render text.

    .. warning::
        The core text label can't be changed at runtime. You must recreate one.

    :Parameters:
        `font_size`: int, defaults to 12
            Font size of the text
        `font_name`: str, defaults to DEFAULT_FONT
            Font name of the text
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
        `max_lines`: int, defaults to 0 (unlimited)
            If set, this indicate how maximum line are allowed to render the
            text. Works only if a limitation on text_size is set.
        `mipmap` : bool, defaults to False
            Create a mipmap for the texture
        `strip` : bool, defaults to False
            Whether each row of text has its leading and trailing spaces
            stripped. If `halign` is `justify` it is implicitly True.

    .. versionchanged:: 1.8.1
        `strip` was added.

    .. versionchanged:: 1.8.1
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

    _cache_glyphs = {}

    _fonts = {}

    _fonts_cache = {}

    _texture_1px = None

    def __init__(self, text='', font_size=12, font_name=DEFAULT_FONT,
                 bold=False, italic=False, halign='left', valign='bottom',
                 shorten=False, text_size=None, mipmap=False, color=None,
                 line_height=1.0, strip=False, **kwargs):

        options = {'text': text, 'font_size': font_size,
                   'font_name': font_name, 'bold': bold, 'italic': italic,
                   'halign': halign, 'valign': valign, 'shorten': shorten,
                   'mipmap': mipmap, 'line_height': line_height,
                   'strip': strip}

        options['color'] = color or (1, 1, 1, 1)
        options['padding'] = kwargs.get('padding', (0, 0))
        if not isinstance(options['padding'], (list, tuple)):
            options['padding'] = (options['padding'], options['padding'])
        options['padding_x'] = kwargs.get('padding_x', options['padding'][0])
        options['padding_y'] = kwargs.get('padding_y', options['padding'][1])

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
                    raise IOError('File {0}s not found'.format(font_type))
                else:
                    fonts.append(font)
            else:
                fonts.append(fonts[-1])  # add regular font to list again

        LabelBase._fonts[name] = tuple(fonts)

    def resolve_font_name(self):
        options = self.options
        fontname = options['font_name']
        fonts = self._fonts
        fontscache = self._fonts_cache

        # is the font is registered ?
        if fontname in fonts:
            # return the prefered font for the current bold/italic combinaison
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
            if filename is None:
                # XXX for compatibility, check directly in the data dir
                filename = os.path.join(kivy_data_dir, fontname)
                if not os.path.exists(filename):
                    raise IOError('Label: File %r not found' % fontname)
            fontscache[fontname] = filename
            options['font_name_r'] = filename

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
            for the font settings used at the time :meth:`get_cached_extents
            was called. Any change in the font settings will render the
            returned function incorrect. You should only use this if you know
            what you're doing.

        .. versionadded:: 1.8.1
        '''
        return self.get_extents

    def _render_begin(self):
        pass

    def _render_text(self, text, x, y):
        pass

    def _render_end(self):
        pass

    def shorten(self, text, margin=2):
        # Just a tiny shortcut
        textwidth = self.get_extents
        if self.text_size[0] is None:
            width = 0
        else:
            width = max(0,
                        int(self.text_size[0] - self.options['padding_x'] * 2))

        letters = '_..._' + text
        while textwidth(letters)[0] > width:
            letters = letters[:letters.rfind(' ')]

        max_letters = len(letters) - 2
        segment = (max_letters // 2)

        if segment - margin > 5:
            segment -= margin
            return type(text)('{0}...{1}').format(text[:segment].strip(),
                                                  text[-segment:].strip())
        else:
            segment = max_letters - 3  # length of '...'
            return type(text)('{0}...').format(text[:segment].strip())

    def _render_real(self):
        lines = self._cached_lines
        options = None
        for line in lines:
            if len(line.words):  # get opts from first line, first word
                options = line.words[0].options
                break
        if not options:  # there was no text to render
            self._render_begin()
            data = self._render_end()
            assert(data)
            if data is not None and data.width > 1:
                self.texture.blit_data(data)
            return

        render_text = self._render_text
        get_extents = self.get_cached_extents()
        uw, uh = options['text_size']
        xpad, ypad = options['padding_x'], options['padding_y']
        x, y = xpad, ypad   # pos in the texture
        iw, ih = self._internal_size  # the real size of text, not texture
        rw = iw - 2 * xpad  # real width of just text
        w, h = self.size
        sw = options['space_width']
        halign = options['halign']
        valign = options['valign']
        split = re.split
        pat = re.compile('( +)')
        self._render_begin()

        if valign == 'bottom':
            y = h - ih + ypad
        elif valign == 'middle':
            y = int((h - ih) / 2 + ypad)

        for layout_line in lines:  # for plain label each line has only one str
            lw, lh = layout_line.w, layout_line.h
            line = ''
            assert len(layout_line.words) < 2
            if len(layout_line.words):
                last_word = layout_line.words[0]
                line = last_word.text
            x = xpad
            if halign[0] == 'c':  # center
                x = int((w - lw) / 2.)
            elif halign[0] == 'r':  # right
                x = max(0, int(w - lw - xpad))

            # right left justify
            # divide left over space between `spaces`
            # TODO implement a better method of stretching glyphs?
            if halign[-1] == 'y' and line and not layout_line.is_last_line:
                # number spaces needed to fill, and remainder
                n, rem = divmod(max(rw - lw, 0), sw)
                n = int(n)
                words = None
                if n or rem:
                    # there's no trailing space when justify is selected
                    words = split(pat, line)
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
                        last_word.lw = rw - ext[0]  # word was stretched
                        render_text(words[-1], x + last_word.lw, y)
                        last_word.text = line = ''.join(words[:-2])
                    else:
                        last_word.lw = rw  # word was stretched
                        last_word.text = line = ''.join(words)
                    layout_line.w = iw  # the line occupies full width


            if len(line):
                layout_line.x = x
                layout_line.y = y
                render_text(line, x, y)
            y += lh

        # get data from provider
        data = self._render_end()
        assert(data)

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
                                    options['halign'][-1] == 'y')
        uw, uh = options['text_size'] = self._text_size
        text = self.text
        if strip:
            text = text.strip()
        if uw is not None and options['shorten']:
            text = self.shorten(text)
        self._cached_lines = lines = []
        if not text:
            return 0, 0

        if uh is not None and options['valign'][-1] == 'e':  # middle
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
                self.get_cached_extents(), options['valign'][-1] == 'p', True)
        self._internal_size = w, h
        if uw:
            w = uw
        if uh:
            h = uh
        if h > 1 and w < 2:
            w = 2
        return w, h

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
        if PY2:
            try:
                if isinstance(self._text, unicode):
                    return self._text
                return self._text.decode('utf8')
            except AttributeError:
                # python 3 support
                return str(self._text)
            except UnicodeDecodeError:
                return self._text
        else:
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
            tex.blit_buffer(b'\x00\x00\x00\x00')
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
            'font_size', 'font_name_r', 'bold', 'italic')])

    def _get_text_size(self):
        return self._text_size

    def _set_text_size(self, x):
        self._text_size = x

    text_size = property(_get_text_size, _set_text_size,
                         doc='''Get/set the (width, height) of the '
                         'contrained rendering box''')

    usersize = property(_get_text_size, _set_text_size,
                        doc='''(deprecated) Use text_size instead.''')

# Load the appropriate provider
Label = core_select_lib('text', (
    ('pygame', 'text_pygame', 'LabelPygame'),
    ('sdlttf', 'text_sdlttf', 'LabelSDLttf'),
    ('pil', 'text_pil', 'LabelPIL'),
))

if 'KIVY_DOC' not in os.environ:
    if not Label:
        from kivy.logger import Logger
        import sys
        Logger.critical('App: Unable to get a Text provider, abort.')
        sys.exit(1)

# For the first initalization, register the default font
    Label.register('DroidSans',
                   'data/fonts/DroidSans.ttf',
                   'data/fonts/DroidSans-Italic.ttf',
                   'data/fonts/DroidSans-Bold.ttf',
                   'data/fonts/DroidSans-BoldItalic.ttf')
