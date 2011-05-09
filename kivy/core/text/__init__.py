'''
Text
====

Abstraction of text creation. Depending of the selected backend, the text
rendering can be more or less accurate.
'''

__all__ = ('LabelBase', 'Label')

import re
import os
from kivy import kivy_data_dir
from kivy.graphics.texture import Texture
from kivy.core import core_select_lib

DEFAULT_FONT = 'Liberation Sans,Bitstream Vera Sans,Free Sans,Arial, Sans'

label_font_cache = {}


class LabelBase(object):
    '''Core text label.
    This is the abstract class used for different backend to render text.

    .. warning::
        The core text label can't be changed at runtime, you must recreate one.

    :Parameters:
        `font_size`: int, default to 12
            Font size of the text
        `font_name`: str, default to DEFAULT_FONT
            Font name of the text
        `bold`: bool, default to False
            Activate "bold" text style
        `italic`: bool, default to False
            Activate "italic" text style
        `size`: list, default to (None, None)
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
    '''

    __slots__ = ('options', 'texture', '_label', 'usersize')

    _cache_glyphs = {}

    def __init__(self, **kwargs):
        kwargs.setdefault('font_size', 12)
        kwargs.setdefault('font_name', DEFAULT_FONT)
        kwargs.setdefault('bold', False)
        kwargs.setdefault('italic', False)
        kwargs.setdefault('size', (None, None))
        kwargs.setdefault('halign', 'left')
        kwargs.setdefault('valign', 'bottom')
        kwargs.setdefault('padding', None)
        kwargs.setdefault('padding_x', None)
        kwargs.setdefault('padding_y', None)
        kwargs.setdefault('shorten', False)

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

        uw, uh = kwargs['size']
        if uw is not None:
            kwargs['size'] = uw - kwargs['padding_x'] * 2, uh

        super(LabelBase, self).__init__()

        self._text = None

        self.usersize = kwargs.get('size')
        self.options = kwargs
        self.texture = None

        if 'font_name' in self.options:
            fontname = self.options['font_name']
            if fontname in label_font_cache:
                if label_font_cache[fontname] is not None:
                    self.options['font_name'] = label_font_cache[fontname]
            else:
                filename = os.path.join(kivy_data_dir, fontname)
                if os.path.exists(filename):
                    label_font_cache[fontname] = filename
                    self.options['font_name'] = filename
                else:
                    label_font_cache[fontname] = None

        self.text = kwargs.get('text', '')

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
        while width > self.usersize[0]:
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

        uw, uh = self.usersize
        w, h = 0, 0
        x, y = 0, 0
        if real:
            self._render_begin()

        # no width specified, faster method
        if uw is None:
            for line in self.text.split('\n'):
                lw, lh = self.get_extents(line)
                if real:
                    x = 0
                    if self.options['halign'] == 'center':
                        x = int((self.width - lw) / 2.)
                    elif self.options['halign'] == 'right':
                        x = int(self.width - lw)
                    self._render_text(line, x, y)
                    y += int(lh)
                else:
                    w = max(w, int(lw))
                    h += int(lh)

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
            if self.options['shorten'] and self.get_extents(text)[0] > uw:
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
                    if word == '\n':
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
                h = sum([size[1] for size, glyphs in lines])
                w = uw
            else:
                # really render now.
                y = 0
                for size, glyphs in lines:
                    x = 0
                    if self.options['halign'] == 'center':
                        x = int((self.width - size[0]) / 2.)
                    elif self.options['halign'] == 'right':
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

        # create texture is necessary
        texture = self.texture
        if texture is None:
            texture = Texture.create(size=self.size, colorfmt='luminance_alpha')
            texture.flip_vertical()
        elif self.width > texture.width or self.height > texture.height:
            texture = Texture.create(size=self.size, colorfmt='luminance_alpha')
            texture.flip_vertical()
        else:
            texture = texture.get_region(
                0, 0, self.width, self.height)

        self.texture = texture

        # update texture
        # If the text is 1px width, usually, the data is black.
        # Don't blit that kind of data, otherwise, you have a little black bar.
        if data.width > 1:
            texture.blit_data(data)

    def refresh(self):
        '''Force re-rendering of the text'''
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
            'font_size', 'font_name', 'bold', 'italic')])

# Load the appropriate provider
Label = core_select_lib('text', (
    ('pygame', 'text_pygame', 'LabelPygame'),
    ('cairo', 'text_cairo', 'LabelCairo'),
    ('pil', 'text_pil', 'LabelPIL'),
))

