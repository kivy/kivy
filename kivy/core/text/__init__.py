'''
Text
====

Abstraction of text creation. Depending of the selected backend, the text
rendering can be more or less accurate.

.. versionadded::
    Starting to 1.0.7, the :class:`LabelBase` don't generate any texture is the
    text have a width <= 1.
'''

__all__ = ('LabelBase', 'Label')

import re
import os
from kivy import kivy_data_dir
from kivy.graphics.texture import Texture
from kivy.core import core_select_lib
from kivy.utils import platform
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
        `text_size`: list, default to (None, None)
            Add constraint to render the text (inside a bounding box)
            If no size is given, the label size will be set to the text size.
        `padding`: int, default to None
            If it's a integer, it will set padding_x and padding_y
        `padding_x`: int, default to 0
            Left/right padding
        `padding_y`: int, default to 0
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

    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', 12)
        kwargs.setdefault('font_name', DEFAULT_FONT)
        kwargs.setdefault('bold', False)
        kwargs.setdefault('italic', False)
        kwargs.setdefault('halign', 'left')
        kwargs.setdefault('valign', 'bottom')
        kwargs.setdefault('padding', None)
        kwargs.setdefault('padding_x', None)
        kwargs.setdefault('padding_y', None)
        kwargs.setdefault('shorten', False)
        kwargs.setdefault('mipmap', False)
        kwargs.setdefault('color', (1, 1, 1, 1))

        padding = kwargs.get('padding', None)
        if not kwargs.get('padding_x', None):
            if type(padding) in (tuple, list):
                kwargs['padding_x'] = float(padding[0])
            elif padding is not None:
                kwargs['padding_x'] = float(padding)
            else:
                kwargs['padding_x'] = 0
        if not kwargs.get('padding_y', None):
            if type(padding) in (tuple, list):
                kwargs['padding_y'] = float(padding[1])
            elif padding is not None:
                kwargs['padding_y'] = float(padding)
            else:
                kwargs['padding_y'] = 0

        self._text_size = (None, None)
        if 'text_size' in kwargs:
            self._text_size = kwargs['text_size']
        elif 'size' in kwargs:
            self._text_size = kwargs['size']

        uw, uh = self._text_size
        if uw is not None:
            self._text_size = uw - kwargs['padding_x'] * 2, uh

        super(LabelBase, self).__init__()

        self._text = None
        self._internal_height = 0

        self.options = kwargs
        self.texture = None
        self.resolve_font_name()
        self.text = kwargs.get('text', '')

    @staticmethod
    def register(name, fn_regular, fn_italic=None, fn_bold=None,
            fn_bolditalic=None):
        '''Register an alias for a Font.

        .. versionadded:: 1.1.0

        If you're using directly a ttf, you might not be able to use bold/italic
        of the ttf version. If the font is delivered with different version of
        it (one regular, one italic and one bold), then you need to register it
        and use the alias instead.

        All the fn_regular/fn_italic/fn_bold parameters are resolved with
        :func:`kivy.resources.resource_find`. If fn_italic/fn_bold are None,
        fn_regular will be used instead.
        '''
        _fn_regular = resource_find(fn_regular)
        if _fn_regular is None:
            raise IOError('File %r not found' % fn_regular)
        if fn_italic is None:
            _fn_italic = _fn_regular
        else:
            _fn_italic = resource_find(fn_italic)
            if _fn_italic is None:
                raise IOError('File %r not found' % fn_italic)
        if fn_bold is None:
            _fn_bold = _fn_regular
        else:
            _fn_bold = resource_find(fn_bold)
            if _fn_bold is None:
                raise IOError('File %r not found' % fn_bold)
        if fn_bolditalic is None:
            _fn_bolditalic = _fn_regular
        else:
            _fn_bolditalic = resource_find(fn_bolditalic)
            if _fn_bolditalic is None:
                raise IOError('Label: File %r not found' % fn_bolditalic)
        LabelBase._fonts[name] = (_fn_regular, _fn_italic, _fn_bold,
                _fn_bolditalic)

    def resolve_font_name(self):
        options = self.options
        if 'font_name' not in options:
            return
        fontname = options['font_name']
        fonts = self._fonts
        fontscache = self._fonts_cache

        # is the font is registered ?
        if fontname in fonts:
            # return the prefered font for the current bold/italic combinaison
            bold = options['bold']
            italic = options['italic']
            font = fonts[fontname]
            if not bold and not italic:
                options['font_name_r'] = font[FONT_REGULAR]
            elif bold and italic:
                options['font_name_r'] = font[FONT_BOLDITALIC]
            elif bold:
                options['font_name_r'] = font[FONT_BOLD]
            else:
                options['font_name'] = font[FONT_ITALIC]

        elif fontname in fontscache:
            options['font_name_r'] = fontscache[fontname]
        else:
            filename = resource_find(fontname)
            if filename is None:
                # XXX for compatibility, check directly in the data dir
                filename = os.path.join(kivy_data_dir, fontname)
                if not os.path.exists(filename):
                    filename = None
            if filename is None:
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

    def shorten(self, text):
        # Just a tiny shortcut
        textwidth = lambda txt: self.get_extents(txt)[0]
        mid = len(text)/2
        begin = text[:mid].strip()
        end = text[mid:].strip()
        steps = 1
        middle = '...'
        width = textwidth(begin+end) + textwidth(middle)
        last_width = width
        while width > self.text_size[0]:
            begin = text[:mid - steps].strip()
            end = text[mid + steps:].strip()
            steps += 1
            width = textwidth(begin+end) + textwidth(middle)
            if width == last_width:
                # No more shortening possible. This is the best we can
                # do. :-( -- Prevent infinite while loop.
                break
            last_width = width
        return begin + middle + end

    def render(self, real=False):
        '''Return a tuple(width, height) to create the image
        with the user constraints.

        2 differents methods are used:
          * if user don't set width, splitting line
            and calculate max width + height
          * if user set a width, blit per glyph
        '''

        options = self.options
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
                lw, lh = self.get_extents(line)
                if real:
                    x = 0
                    if halign == 'center':
                        x = int((self.width - lw) / 2.)
                    elif halign == 'right':
                        x = int(self.width - lw)
                    self._render_text(line, x, y)
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
                        cache[glyph] = self.get_extents(glyph)

            # Shorten the text that we actually display
            text = self.text
            if options['shorten'] and self.get_extents(text)[0] > uw:
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
                        if glyph != '\n':
                            self._render_text(glyph, x, y)
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
        if texture is None:
            if data is None:
                if platform() in ('android', 'ios'):
                    colorfmt = 'rgba'
                else:
                    colorfmt = 'luminance_alpha'
                texture = Texture.create(
                        size=self.size, colorfmt=colorfmt,
                        mipmap=mipmap)
            else:
                texture = Texture.create_from_data(data, mipmap=mipmap)
            texture.flip_vertical()
        elif self.width != texture.width or self.height != texture.height:
            if data is None:
                texture = Texture.create(size=self.size, mipmap=mipmap)
            else:
                texture = Texture.create_from_data(data, mipmap=mipmap)
            texture.flip_vertical()
        '''
        # Avoid that for the moment.
        # The thing is, as soon as we got a region, the blitting is not going in
        # the right position cause of previous flip_vertical
        # In addition, as soon as we have a region, we are not testing from the
        # original texture. Mean we'll have region of region of region.
        # Take more time to implement a fix for it, if it's needed.
        else:
            print 'get region ??', self, self.width, self.height
            texture = texture.get_region(
                0, 0, self.width, self.height)
        '''

        self.texture = texture

        # update texture
        # If the text is 1px width, usually, the data is black.
        # Don't blit that kind of data, otherwise, you have a little black bar.
        if data is not None and data.width > 1:
            texture.blit_data(data)

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

