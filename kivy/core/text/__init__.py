'''
Text
====

Abstraction of text creation. Depending of the selected backend, the text
rendering can be more or less accurate.

.. versionadded::
    Starting to 1.0.7, the :class:`LabelBase` don't generate any texture is the
    text have a width <= 1.

.. versionadded::
    In 1.0.10, renderer implementation have been seperated from `LabelBase`.

'''

__all__ = ('Label', 'LabelRendererBase', 'LabelExcetion')

import re
import os
from kivy import kivy_data_dir
from kivy.graphics.texture import Texture
from kivy.core import core_register_libs

DEFAULT_FONT = 'Liberation Sans,Bitstream Vera Sans,Free Sans,Arial, Sans'

label_font_cache = {}


class LabelException(Exception):
    pass


class LabelRendererBase(object):
    '''(internal) Implementation of a label renderer.
    '''

    prefered_renderer = None
    fallback_renderer = None
    renderers = {}

    @staticmethod
    def register(name, renderer):
        '''(internal) Register a new renderer
        '''

        # the first renderer found will be the prefered one
        # assign it as the fallback is no other renderer can be found
        if LabelRendererBase.prefered_renderer is None:
            LabelRendererBase.prefered_renderer = renderer
            LabelRendererBase.fallback_renderer = renderer

        # if we found another renderer, use it as fallback
        elif LabelRendererBase.fallback_renderer is None or \
            LabelRendererBase.fallback_renderer == \
            LabelRendererBase.prefered_renderer:
            LabelRendererBase.fallback_renderer = renderer

        # really register.
        LabelRendererBase.renderers[name] = renderer

    @staticmethod
    def get(name):
        '''(internal) Get a renderer from a name
        '''
        renderers = LabelRendererBase.renderers
        if name is None or name not in renderers:
            return LabelRendererBase.prefered_renderer
        return renderers[name]

    def __init__(self, **kwargs):
        assert('label' in kwargs)
        super(LabelRendererBase, self).__init__()
        self.label = kwargs.get('label')

    def validate(self, text):
        '''Return True if the text can be renderer through this renderer.
        '''
        return True

    def get_extents(self, text):
        '''Return the extents of a text (width, height)
        '''
        raise NotImplementedError()

    def render_begin(self, width, height):
        '''Start the rendering, create the appropriate surface for (width,
        height)
        '''
        raise NotImplementedError()

    def render_text(self, text, x, y):
        '''Render a text at the position (x, y)
        '''
        raise NotImplementedError()

    def render_end(self):
        '''End the rendering, return the surface data
        '''
        raise NotImplementedError()


class Label(object):
    '''Core text label.

    .. warning::
        The core text label can't be changed at runtime, you must recreate one.

    .. versionadded::
        In 1.0.10, rendering have been moved out the LabelBase. `renderer`
        attribute have been added to select the renderer you want for a label.
        Depending of the renderer, you might not have a texture.

    .. versionadded::
        In 1.0.8, `size` have been deprecated and replaced with `text_size`

    .. versionadded::
        In 1.0.7, the valign is now respected. This wasn't the case before. You
        might have issue in your application if you never think about that
        before.

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
        `mipmap`: bool, default to False
            Create mipmap for the texture
        `renderer`: str, default to None
            Specify a renderer to use. Must be one of the registered renderer
            available in :data:`LabelRendererBase.renderers`. If None is
            provided, it will use the
            :data:`LabelRendererBase.prefered_renderer` first.
    '''

    __slots__ = ('options', 'texture', '_label', '_text_size', '_renderer',
            '_text', '_internal_height', '_size')

    _cache_glyphs = {}

    def __init__(self, **kwargs):
        super(Label, self).__init__()

        kwargs.setdefault('font_size', 12)
        kwargs.setdefault('font_name', DEFAULT_FONT)
        kwargs.setdefault('bold', False)
        kwargs.setdefault('italic', False)
        kwargs.setdefault('halign', 'left')
        kwargs.setdefault('valign', 'bottom')
        kwargs.setdefault('shorten', False)
        kwargs.setdefault('mipmap', False)

        # calculate padding
        padding_x, padding_y = kwargs.get('padding', (None, None))
        padding_x = kwargs.get('padding_x', None)
        padding_y = kwargs.get('padding_y', None)
        kwargs['padding_x'] = padding_x
        kwargs['padding_y'] = padding_y

        # calculate text bounding box
        self._text_size = (None, None)
        if 'text_size' in kwargs:
            self._text_size = kwargs['text_size']

        # correct size with padding
        uw, uh = self._text_size
        if uw is not None:
            self._text_size = uw - kwargs['padding_x'] * 2, uh

        # init internals.
        self._text = None
        self._internal_height = 0
        self.options = kwargs
        self.texture = None

        # check if the fontname is ok for us
        if 'font_name' in kwargs:
            fontname = kwargs['font_name']
            if fontname in label_font_cache:
                if label_font_cache[fontname] is not None:
                    kwargs['font_name'] = label_font_cache[fontname]
            else:
                filename = os.path.join(kivy_data_dir, fontname)
                if os.path.exists(filename):
                    label_font_cache[fontname] = filename
                    kwargs['font_name'] = filename
                else:
                    label_font_cache[fontname] = None

        # update and decode text if necessary
        self.text = text = kwargs.get('text', '')

        # create a renderer for this label (maybe we could not create it ?)
        self._renderer = renderer = LabelRendererBase.get(
            kwargs.get('renderer', None))(label=self)

        # validate if this text can be renderer though with renderer
        if not renderer.validate(text):
            # if it's already an instance of the prefered renderer, try to use
            # the fallback
            if isinstance(renderer, LabelRendererBase.prefered_renderer):
                renderer = LabelRendererBase.fallback_renderer()
            else:
                renderer = LabelRendererBase.prefered_renderer()
            if renderer is None:
                renderer = LabelRendererBase.fallback_renderer()

            validation = False
            if renderer:
                validation = renderer.validate(text)

            # if even the fallback renderer cant do it, raise an exception
            if not validation:
                raise LabelException('Cannot render %r using '
                    'fallback renderer %r' % (text, renderer))

    def get_extents(self, text):
        '''Return a tuple with (width, height) for a text
        '''
        return self._renderer.get_extents(text)

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
        renderer = self._renderer
        render_text = renderer.render_text
        uw, uh = self.text_size
        x = y = w = h = 0
        if real:
            renderer.render_begin(self.width, self.height)
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
        data = renderer.render_end()

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
                texture = Texture.create(
                    size=self.size, colorfmt='luminance_alpha',
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
        '''Force text rendering
        '''
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

    def _get_text_size(self):
        return self._text_size

    def _set_text_size(self, x):
        self._text_size = x

    text_size = property(_get_text_size, _set_text_size,
        doc='''Get/set the (width, height) of the contrained rendering box''')


core_register_libs('text', (
    ('pygame', 'text_pygame'),
    #('cairo', 'text_cairo'),
    #('pil', 'text_pil'),
))

