'''
Text
====

Abstraction of text creation. Depending of the selected backend, the text
rendering can be more or less accurate.

.. versionchanged:: 1.0.7
    The :class:`LabelBase` don't generate any texture is the text have a width
    <= 1.
'''

__all__ = ('LabelBase', 'Label')

import re
import os
from kivy import kivy_data_dir
from kivy.graphics.texture import Texture
from kivy.core import core_select_lib
from kivy.resources import resource_find

DEFAULT_FONT = 'DroidSans'

FONT_REGULAR = 0
FONT_ITALIC = 1
FONT_BOLD = 2
FONT_BOLDITALIC = 3


class LabelBase(object):
    '''Core text label.
    This is the abstract class used for different backend to render text.

    .. warning::
        The core text label can't be changed at runtime, you must recreate one.

    .. versionadded::
        In 1.0.7, the valign is now respected. This wasn't the case before. You
        might have issue in your application if you never think about that
        before.

    .. versionadded::
        In 1.0.8, `size` have been deprecated and replaced with `text_size`

    :Parameters:
        `font_size`: int, default to 12
            Font size of the text
        `font_name`: str, default to DEFAULT_FONT
            Font name of the text
        `bold`: bool, default to False
            Activate "bold" text style
        `italic`: bool, default to False
            Activate "italic" text style
        `text_size`: tuple, default to (None, None)
            Add constraint to render the text (inside a bounding box)
            If no size is given, the label size will be set to the text size.
        `padding`: float, default to None
            If it's a float, it will set padding_x and padding_y
        `padding_x`: float, default to 0.0
            Left/right padding
        `padding_y`: float, default to 0.0
            Top/bottom padding
        `halign`: str, default to "left"
            Horizontal text alignement inside bounding box
        `valign`: str, default to "bottom"
            Vertical text alignement inside bounding box
        `shorten`: bool, defaults to False
            Indicate whether the label should attempt to shorten its textual
            contents as much as possible if a `size` is given.
            Setting this to True without an appropriately set size will lead
            unexpected results.
        `mipmap` : bool, default to False
            Create mipmap for the texture
    '''

    __slots__ = ('options', 'texture', '_label', '_text_size')

    _cache_glyphs = {}

    _fonts = {}

    _fonts_cache = {}

    def __init__(self, text='', font_size=12, font_name=DEFAULT_FONT,
                 bold=False, italic=False, halign='left', valign='bottom',
                 shorten=False, text_size=None, mipmap=False, color=None,
                 **kwargs):

        options = {'text': text, 'font_size': font_size,
            'font_name': font_name, 'bold': bold, 'italic': italic,
            'halign': halign, 'valign': valign, 'shorten': shorten,
            'mipmap': mipmap}

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

        If you're using a ttf directly, you might not be able to use bold/italic
        of the ttf version. If the font is delivered with different version of
        it (one regular, one italic and one bold), then you need to register it
        and use the alias instead.

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
                fonts.append(fonts[-1]) # add regular font to list again

        LabelBase._fonts[name] = tuple(fonts)

    def resolve_font_name(self):
        options = self.options
        fontname = self.options['font_name']
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
        '''Return a tuple with (width, height) for a text.'''
        return (0, 0)

    def _render_begin(self):
        pass

    def _render_text(self, text, x, y):
        pass

    def _render_end(self):
        pass

    def shorten(self, text, margin=2):
        # Just a tiny shortcut
        textwidth = lambda txt: self.get_extents(txt)[0]
        if self.text_size[0] is None:
            width = 0
        else:
            width = int(self.text_size[0])

        letters = text + '...'
        letter_width = textwidth(letters) // len(letters)
        max_letters = width // letter_width
        segment = (max_letters // 2)

        if segment - margin > 5:
            segment -= margin
            return '{0}...{1}'.format(text[:segment].strip(),
                text[-segment:].strip())
        else:
            segment = max_letters - 3 # length of '...'
            return '{0}...'.format(text[:segment].strip())

    def render(self, real=False):
        '''Return a tuple(width, height) to create the image
        with the user constraints.

        2 differents methods are used:
          * if user don't set width, splitting line
            and calculate max width + height
          * if user set a width, blit per glyph
        '''

        options = self.options
        render_text = self._render_text
        get_extents = self.get_extents
        uw, uh = self.text_size
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
            for line in self.text.split('\n'):
                lw, lh = get_extents(line)
                if real:
                    x = 0
                    if halign == 'center':
                        x = int((self.width - lw) / 2.)
                    elif halign == 'right':
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
            if options['shorten'] and get_extents(text)[0] > uw:
                text = self.shorten(text)

            # first, split lines
            glyphs = []
            lines = []
            lw = lh = 0
            for word in re.split(r'( |\n)', text):

                # calculate the word width
                ww, wh = 0, 0
                for glyph in word:
                    gw, gh = cache[glyph]
                    ww += gw
                    wh = max(gh, wh)

                # is the word fit on the uw ?
                if ww > uw:
                    lines.append(((ww, wh), word))
                    lw = lh = x = 0
                    continue

                # get the maximum height for this line
                lh = max(wh, lh)

                # is the word fit on the line ?
                if (word == '\n' or x + ww > uw) and lw != 0:
                    # no, push actuals glyph
                    lines.append(((lw, lh), glyphs))
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
                lines.append(((lw, lh), glyphs))

            if not real:
                self._internal_height = sum([size[1] for size, glyphs in lines])
                h = self._internal_height if uh is None else uh
                w = uw
            else:
                # really render now.
                for size, glyphs in lines:
                    x = 0
                    if halign == 'center':
                        x = int((self.width - size[0]) / 2.)
                    elif halign == 'right':
                        x = int(self.width - size[0])
                    for glyph in glyphs:
                        lw, lh = cache[glyph]
                        if glyph != ' ' and glyph != '\n':
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

        # if data width is too tiny, just create texture, don't really render!
        if data.width <= 1:
            if self.texture:
                self.texture = None
            return

        # create texture is necessary
        texture = self.texture
        mipmap = options['mipmap']
        if texture is None or \
                self.width != texture.width or \
                self.height != texture.height:
            texture = Texture.create_from_data(data, mipmap=mipmap)
            data = None
            texture.flip_vertical()
            texture.add_reload_observer(self._texture_refresh)
            self.texture = texture

        # update texture
        # If the text is 1px width, usually, the data is black.
        # Don't blit that kind of data, otherwise, you have a little black bar.
        if data is not None and data.width > 1:
            texture.blit_data(data)

    def _texture_refresh(self, *l):
        self.refresh()

    def refresh(self):
        '''Force re-rendering of the text
        '''
        self.resolve_font_name()

        # first pass, calculating width/height
        sz = self.render()
        self._size = sz
        # second pass, render for real
        self.render(real=True)
        self._size = sz[0] + self.options['padding_x'] * 2, \
                     sz[1] + self.options['padding_y'] * 2

    def _get_text(self):
        return self._text

    def _set_text(self, text):
        if text == self._text:
            return
        # try to automaticly decode unicode
        try:
            self._text = text.decode('utf8')
        except:
            try:
                self._text = str(text)
            except:
                self._text = text
    text = property(_get_text, _set_text, doc='Get/Set the text')
    label = property(_get_text, _set_text, doc='Get/Set the text')

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
        '''Return an uniq id for all font parameters'''
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
    ('pil', 'text_pil', 'LabelPIL'),
))

# For the first initalization, register the default font
if 'KIVY_DOC' not in os.environ:
    Label.register('DroidSans',
        'data/fonts/DroidSans.ttf',
        'data/fonts/DroidSans-Italic.ttf',
        'data/fonts/DroidSans-Bold.ttf',
        'data/fonts/DroidSans-BoldItalic.ttf')

