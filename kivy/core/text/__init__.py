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

This is the backend layer for getting text out of different text providers,
you should only be using this directly if your needs aren't fulfilled by
:class:`~kivy.uix.label.Label`.

Usage example::

    from kivy.core.label import Label as CoreLabel
    
    ...
    ...
    my_label = CoreLabel()
    my_label.text = 'hello'
    # label is usully not drawn till absolutely needed, force it to draw.
    my_label.refresh()
    # Now access the texture of the label and use it where ever,
    # however you may please.
    hello_texture = my_label.texture

'''

__all__ = ('LabelBase', 'Label')

import re
import os
from kivy import kivy_data_dir
from kivy.graphics.texture import Texture
from kivy.core import core_select_lib
from kivy.resources import resource_find
from kivy.compat import PY2
from kivy.config import Config

DEFAULT_FONT = Config.get('kivy', 'default_font')

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

        self._text_size = options['text_size']
        self._text = options['text']
        self._internal_width = self._internal_height = 0
        self._cached_lines = []
        self._cached_text_size = self._cached_padding = (0, 0)
        self._cached_options = {}

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
        options = self._cached_options
        render_text = self._render_text
        get_extents = self.get_extents
        uw, uh = self._cached_text_size
        xpad, ypad = self._cached_padding
        x, y = xpad, ypad   # pos in the texture
        contentw = self._internal_width - 2 * xpad
        split = re.split
        pat = re.compile('( +)')
        self._render_begin()

        sw = get_extents(' ')[0]
        halign = options['halign']
        valign = options['valign']
        if valign == 'bottom':
            y = self.height - self._internal_height + ypad
        elif valign == 'middle':
            y = int((self.height - self._internal_height) / 2 + ypad)

        for line, (lw, lh), is_last_line in self._cached_lines:
            x = xpad
            if halign[0] == 'c':  # center
                x = int((self.width - lw) / 2.)
            elif halign[0] == 'r':  # right
                x = int(self.width - lw - xpad)

            # right left justify
            # divide left over space between `spaces`
            # TODO implement a better method of stretching glyphs?
            if halign[-1] == 'y' and line and not is_last_line:
                # number spaces needed to fill, and remainder
                n, rem = divmod(contentw - lw, sw)
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
                        # render the last word at the edge
                        render_text(words[-1], x + contentw -
                                    get_extents(words[-1])[0], y)
                        line = ''.join(words[:-2])
                    else:
                        line = ''.join(words)

            if len(line):
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

        self._cached_options = options = dict(self.options)
        render_text = self._render_text
        get_extents = self.get_extents
        uw, uh = self.text_size
        xpad, ypad = options['padding_x'], options['padding_y']
        max_lines = int(options.get('max_lines', 0))
        strip = options['strip'] or options['halign'][-1] == 'y'
        w, h = 0, 0   # width and height of the texture
        x, y = xpad, ypad   # pos in the texture
        # don't allow them to change before rendering for real
        self._cached_padding = xpad, ypad
        self._cached_text_size = uw, uh
        text = self.text
        if strip:
            text = text.strip()
        if not text:
            self._cached_lines = []
            return 0, 0

        # no width specified, find max width. For height, if not specified,
        # do everything, otherwise stop when reached specified height
        if uw is None:
            h = ypad * 2
            lines = text.split('\n')
            for i in range(len(lines)):
                if (max_lines > 0 and i + 1 > max_lines or uh is not None
                    and h > uh):
                    i -= 1
                    break
                line = lines[i].strip() if strip else lines[i]
                lw, lh = get_extents(line)
                lh = int(lh * options['line_height'])
                if uh is not None and h + lh > uh:  # too high
                    break
                w = max(w, int(lw + 2 * xpad))
                h += lh
                lines[i] = (line, (lw, lh), True)  # True == its line end
            self._internal_height = h
            self._cached_lines = lines[:i + 1]
            if uh is not None:  # texture size must be requested text_size
                h = uh

        else:  # constraint width
            uw = max(0, uw - xpad * 2)  # actual w, h allowed for rendering
            if uh is not None:
                uh = max(0, uh - ypad * 2)
            bare_size = get_extents('')

            # Shorten the text that we actually display
            if (options['shorten'] and get_extents(text)[0] > uw):
                text = self.shorten(text)
                lw, lh = get_extents(text)
                self._cached_lines = [(text, (lw + 2 * xpad, lh + 2 * ypad),
                                       True)] if text else []
                self._internal_width = uw + xpad * 2
                self._internal_height = lh + 2 * ypad
                # height must always be the requested size, if specified
                h = self._internal_height if uh is None else lh + 2 * ypad
                return self._internal_width, h

            lines = []
            h = 0
            # split into lines and find how many real lines each line requires
            for line in text.split('\n'):
                if (uh is not None and h > uh or max_lines > 0 and
                    len(lines) > max_lines):
                    break

                if strip:
                    line = line.strip()
                if line == '':  # just add empty line if empty
                    lines.append(('', bare_size, True))
                    h += lines[-1][1][1] * options['line_height']
                    continue

                # what we do is given the current text in this real line
                # (starts empty), if we can fit another word, add it. Otherwise
                # add it to a new line. But if a single word doen't fit on a
                # single line, just split the word itself into multiple lines

                # s is idx in line of start of this actual line, e is idx of
                # next space, m is idx after s that still fits on this line
                s = m = e = 0
                while s != len(line):
                    # find next space or end, if end don't keep checking
                    if e != len(line):
                        e = line.find(' ', m + 1)
                        if e is -1:
                            e = len(line)

                    lwe, lhe = get_extents(line[s:e])  # does next word fit?
                    if lwe > uw:  # too wide
                        if s != m:
                            # theres already some text, commit and go next line
                            # make sure there are no trailing spaces, may occur
                            # if many spaces is followed by word not fitting
                            ln = line[s:m]
                            if strip and ln[-1] == ' ':
                                ln = ln.rstrip()
                                lines.append((ln, get_extents(ln), False))
                            else:
                                lines.append((line[s:m], (lw, lh), False))
                            h += lh * options['line_height']
                            s = m

                        # try to fit word on new line, if it doesn't fit we'll
                        # have to break the word into as many lines needed
                        if strip:
                            s = e - len(line[s:e].lstrip())
                        if s == e:  # if it was only a stripped space, move on
                            m = s
                            continue

                        # now break single word into as many lines needed
                        m = s
                        while s != e:
                            # does remainder fit in single line?
                            lwe, lhe = get_extents(line[s:e])
                            if lwe <= uw:
                                m = e
                                break
                            # if not, fit as much as possible into this line
                            while (m != e and
                                   get_extents(line[s:m + 1])[0] <= uw):
                                m += 1
                            # not enough room for even single char, skip it
                            if m == s:
                                s += 1
                            else:
                                lines.append((line[s:m],
                                get_extents(line[s:m]), m == len(line)))
                                h += lines[-1][1][1] * options['line_height']
                                s = m
                            m = s
                        m = s  # done with long word, go back to normal

                    else:   # the word fits
                        # don't allow leading spaces on empty lines
                        if strip and m == s and line[s:e] == ' ':
                            s = m = e
                            continue
                        m = e

                    if m == len(line):  # we're done
                        if s != len(line):
                            lines.append((line[s:], (lwe, lhe), True))
                            h += lhe * options['line_height']
                        break
                    lw, lh = lwe, lhe

            # ensure the number of lines is not more than the user asked
            # above, we might have gone a few lines over
            if max_lines > 0:
                lines = lines[:max_lines]
            # now make sure we don't have lines outside specified height
            if uh is not None:
                lh = options['line_height']
                i = h = 0
                while i < len(lines) and h + lines[i][1][1] * lh <= uh:
                    h += lines[i][1][1] * lh
                    i += 1
                lines = lines[:i]

            self._internal_height = h + ypad * 2
            # height must always be the requested size, if specified
            h = self._internal_height if uh is None else uh + ypad * 2
            w = uw + xpad * 2
            self._cached_lines = lines

        # was only the first pass
        # return with/height
        w = int(max(w, 1))
        self._internal_width = w
        h = int(max(h, 1))
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

# If the font was not overriden in Config, register the default
if DEFAULT_FONT == 'DroidSans':
    Label.register('DroidSans',
                   'data/fonts/DroidSans.ttf',
                   'data/fonts/DroidSans-Italic.ttf',
                   'data/fonts/DroidSans-Bold.ttf',
                   'data/fonts/DroidSans-BoldItalic.ttf')
