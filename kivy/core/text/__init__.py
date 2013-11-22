'''
Text
====

An abstraction of text creation. Depending of the selected backend, the accuracy
of text rendering may vary.

.. versionchanged:: 1.5.0
    :data:`LabelBase.line_height` added.

.. versionchanged:: 1.0.7
    The :class:`LabelBase` does not generate any texture if the text has a
    width <= 1.
'''

__all__ = ('LabelBase', 'Label')

import re
import os
from kivy import kivy_data_dir
from kivy.graphics.texture import Texture
from kivy.core import core_select_lib
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
        `max_lines`: int, default to 0 (unlimited)
            If set, this indicate how maximum line are allowed to render the
            text. Works only if a limitation on text_size is set.
        `mipmap` : bool, default to False
            Create a mipmap for the texture

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
                 line_height=1.0, **kwargs):

        options = {'text': text, 'font_size': font_size,
            'font_name': font_name, 'bold': bold, 'italic': italic,
            'halign': halign, 'valign': valign, 'shorten': shorten,
            'mipmap': mipmap, 'line_height': line_height}

        options['color'] = color or (1, 1, 1, 1)
        options['padding'] = kwargs.get('padding', 0)
        options['padding_x'] = kwargs.get('padding_x', options['padding'])
        options['padding_y'] = kwargs.get('padding_y', options['padding'])

        if 'size' in kwargs:
            options['text_size'] = kwargs['size']
        else:
            if text_size is None:
                options['text_size'] = (None, None)
            else:
                options['text_size'] = text_size

        text_width, text_height = options['text_size']
        if text_width is not None:
            self._text_size = (
                text_width - options['padding_x'] * 2,
                text_height)
        else:
            self._text_size = options['text_size']

        self._text = options['text']
        self._internal_height = 0

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
            width = int(self.text_size[0])

        letters = '_..._' + text
        while textwidth(letters)[0] > width:
            letters = letters[:letters.rfind(' ')]

        max_letters = len(letters) - 2
        segment = (max_letters // 2)

        if segment - margin > 5:
            segment -= margin
            return u'{0}...{1}'.format(text[:segment].strip(),
                text[-segment:].strip())
        else:
            segment = max_letters - 3  # length of '...'
            return u'{0}...'.format(text[:segment].strip())

    def render(self, real=False):
        '''Return a tuple (width, height) to create the image
        with the user constraints.

        2 differents methods are used:
          * if the user does not set the width, split the line
            and calculate max width + height
          * if the user sets a width, blit per glyph
        '''

        options = self.options
        render_text = self._render_text
        get_extents = self.get_extents
        uw, uh = self.text_size
        max_lines = int(options.get('max_lines', 0))
        w, h = 0, 0
        x, y = 0, 0
        if real:
            self._render_begin()
            halign = options['halign']
            valign = options['valign']
            if valign == 'bottom':
                y = self.height - self._internal_height
            elif valign == 'middle':
                y = int((self.height - self._internal_height) / 2)
        else:
            self._internal_height = 0

        # no width specified, faster method
        if uw is None:
            index = 0
            for line in self.text.split('\n'):
                index += 1
                if max_lines > 0 and index > max_lines:
                    break
                lw, lh = get_extents(line)
                lh = lh * options['line_height']
                if real:
                    x = 0
                    if halign[0] == 'c':
                        # center
                        x = int((self.width - lw) / 2.)
                    elif halign[0] == 'r':
                        # right
                        x = int(self.width - lw)
                    if len(line):
                        render_text(line, x, y)
                    y += int(lh)
                else:
                    w = max(w, int(lw))
                    self._internal_height += int(lh)
            h = self._internal_height if uh is None else uh

        # constraint
        else:
            # precalculate id/name
            if not self.fontid in self._cache_glyphs:
                self._cache_glyphs[self.fontid] = {}
            cache = self._cache_glyphs[self.fontid]

            if not real:
                # verify that each glyph have size
                glyphs = list(set(self.text)) + ['.']
                for glyph in glyphs:
                    if not glyph in cache:
                        cache[glyph] = get_extents(glyph)

            # Shorten the text that we actually display
            text = self.text
            last_word_width = get_extents(text[text.rstrip().rfind(' '):])[0]
            if (options['shorten'] and get_extents(text)[0] >
                uw - last_word_width):
                text = self.shorten(text)

            # first, split lines
            glyphs = []
            lines = []
            lw = lh = 0
            for word in re.split(r'( |\n)', text):

                # calculate the word width
                ww, wh = 0, 0
                if word == '':
                    ww, wh = get_extents(' ')
                for glyph in word:
                    gw, gh = cache[glyph]
                    ww += gw
                    wh = max(gh, wh)
                wh = wh * options['line_height']

                # is the word fit on the uw ?
                if ww > uw:
                    lines.append(((ww, wh), 0, word))
                    lw = lh = x = 0
                    if max_lines > 0 and len(lines) >= max_lines:
                        break
                    continue

                # get the maximum height for this line
                lh = max(wh, lh)
                # is the word fit on the line ?
                if (word == '\n' or x + ww > uw) and lw != 0:
                    # no, push actuals glyph
                    # lw, lh), is_last_line, glyphs)
                    last_line = 1 if word == '\n' else 0
                    lines.append(((lw, lh), last_line, glyphs))
                    glyphs = []

                    # reset size
                    lw = lh = x = 0

                    # new line ? don't render
                    if word == '\n' or word == ' ':
                        continue

                # advance the width
                lw += ww
                x += ww
                lh = max(wh, lh)
                glyphs += list(word)

            # got some char left ?
            if lw != 0:
                lines.append(((lw, lh), 1, glyphs))

            # ensure the number of lines is not more than the user asked
            if max_lines > 0:
                lines = lines[:max_lines]

            if not real:
                self._internal_height = sum([size[1] for size, last_line,
                                            glyphs in lines])
                ll_h = lines[-1][0][1]
                lh_offset = ll_h - (ll_h / self.options['line_height'])
                self._internal_height = self._internal_height - lh_offset
                h = self._internal_height if uh is None else uh
                w = uw
            else:
                # really render now.
                for size, last_line, glyphs in lines:
                    x = 0
                    if halign[0] == 'c':
                        # center
                        x = int((self.width - size[0]) / 2.)
                    elif halign[0] == 'r':
                        # right
                        x = int(self.width - size[0])

                    # justification
                    just_space = 0
                    if halign[-1] == 'y':
                        # justified
                        if glyphs and not last_line:
                            x = 0
                            last_space = 1 if glyphs[-1] == ' ' else 0
                            _spaces = glyphs.count(' ') - last_space
                            # divide left over space between `spaces`
                            # TODO implement a better method of stretching
                            # glyphs?
                            if _spaces:
                                space_width = cache[' '][0] if last_space else 0
                                just_space = (((uw - size[0] + space_width) *
                                               1.) / (_spaces * 1.))

                    for glyph in glyphs:
                        lw, lh = cache[glyph]
                        if glyph == ' ':
                            x += just_space
                        elif glyph != '\n':
                            render_text(glyph, x, y)
                        x += lw
                    y += size[1]

        if not real:
            # was only the first pass
            # return with/height
            w = int(max(w, 1))
            h = int(max(h, 1))
            return w, h

        # get data from provider
        data = self._render_end()
        assert(data)

        # If the text is 1px width, usually, the data is black.
        # Don't blit that kind of data, otherwise, you have a little black bar.
        if data is not None and data.width > 1:
            self.texture.blit_data(data)

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
        self._size = sz[0] + self.options['padding_x'] * 2, \
                     sz[1] + self.options['padding_y'] * 2

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
                if type(self._text) is unicode:
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
        '''Return the content width'''
        if self.texture is None:
            return 0
        return self.texture.width + 2 * self.options['padding_x']

    @property
    def content_height(self):
        '''Return the content height'''
        if self.texture is None:
            return 0
        return self.texture.height + 2 * self.options['padding_y']

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
        doc='''Get/set the (width, height) of the contrained rendering box''')

    usersize = property(_get_text_size, _set_text_size,
        doc='''(deprecated) Use text_size instead.''')

# Load the appropriate provider
Label = core_select_lib('text', (
    ('pygame', 'text_pygame', 'LabelPygame'),
    ('sdlttf', 'text_sdlttf', 'LabelSDLttf'),
    ('pil', 'text_pil', 'LabelPIL'),
))

# For the first initalization, register the default font
if 'KIVY_DOC' not in os.environ:
    Label.register('DroidSans',
        'data/fonts/DroidSans.ttf',
        'data/fonts/DroidSans-Italic.ttf',
        'data/fonts/DroidSans-Bold.ttf',
        'data/fonts/DroidSans-BoldItalic.ttf')

