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
        self._internal_size = 0, 0
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

    def layout_text(self, text, lines, size, options, get_extents,
                    pos_cache=None):
        '''if start of line and space, if trip it's removed
        the last line, unless it ends with a new line won't be stripped on
        right
        lines is list of [line1, line2, ...]. Each line:
        [[x, y, width, height], is_last_line, [word1, word2, ...]]
        where each word is (opts, (lw, lh), text)
        note that lh is the actual height of the line, while height is the
        height of the line including multiplied by 'line_height'.

        options must contain 'space_width'. This is in case we have to walk
        back to prev lines with different options.

        size, takes the previous size and increments by the text added
        height be larger than text_size, or smaller. width is always <=.
        size includes padding
        Note, this is not part of the external API and may change in the
        future.
        '''

        uw, uh = options['text_size']
        xpad, ypad = options['padding_x'], options['padding_y']
        max_lines = int(options.get('max_lines', 0))
        line_height = options['line_height']
        strip = options['strip'] or options['halign'][-1] == 'y'
        w, h = size   # width and height of the texture so far
        if not text:
            return size

        if not h:
            h = ypad * 2
        new_lines = text.split('\n')
        n = len(new_lines) - 1

        # no width specified, find max width. For height, if not specified,
        # do everything, otherwise stop when reached specified height
        if uw is None:
            s = 0
            # there's a last line to which the first new line must be appended
            if lines:
                s = 1
                line_size, words = lines[-1][0], lines[-1][2]
                val = new_lines[0]
                if strip:
                    if not line_size[2]:  # prev width is zero, strip leading
                        val = val.lstrip()
                    if len(new_lines) > 1:  # ends this line so right strip
                        val = val.rstrip()
                lw, lh = get_extents(val)
                lh = int(lh * line_height)

                # when adding to existing line, don't check uh
                words.append((options, (lw, lh), val))
                old_lh = line_size[3]
                line_size[2] += lw
                line_size[3] = max(lh, line_size[3])
                w = max(w, line_size[2])
                h += line_size[3] - old_lh

            # now do the remaining lines
            for i in range(s, len(new_lines)):
                # always compute first line, even if it won't be displayed
                if (max_lines > 0 and len(lines) + i + 1 > max_lines or
                    uh is not None and h > uh and i):
                    i -= 1
                    break
                line = new_lines[i]
                # the last line is only stripped from left
                if strip:
                    if i < n:
                        line = line.strip()
                    else:
                        line = line.lstrip()
                lw, lh = get_extents(line)
                lh = int(lh * line_height)
                if uh is not None and h + lh > uh and i:  # too high
                    break
                w = max(w, int(lw + 2 * xpad))
                h += lh
                new_lines[i] = [[0, 0, lw, lh], True,
                                (options, (lw, lh), line)]
            lines.extend(new_lines[s:i + 1])
            return w, h

        # constraint width ############################################
        uw = max(0, uw - xpad * 2)  # actual w, h allowed for rendering
        bare_size = get_extents('')

        def add_line(text, lw, lh):
            ''' Adds to the current _line the text, increases that line's w/h
            by required amount, increases global h by required amount and
            returns new empty line and global w, h.
            '''
            _line[2].append((options, (lw, lh), text))
            _line[0][3] = max(int(_line[2][-1][1][1] * line_height), isize[1])
            _line[0][2] += _line[2][-1][1][0]
            lines.append(_line)
            hh = h + _line[0][3] - isize[1]
            isize[0] = isize[1] = 0  # after first new line, it's always zero
            return [[0, 0, 0, 0], False, []], max(w, _line[0][2]), hh

        # split into lines and find how many real lines each line requires
        for i in range(len(new_lines)):
            if (max_lines > 0 and len(lines) > max_lines or uh is not None and
                h > uh and len(lines) > 1):
                break

            # for the first new line, we have to append to last passed in line
            if i or not len(lines):
                _line = [[0, 0, 0, 0], False, []]
            else:
                _line = lines.pop()
            isize = _line[0][2:]  # initial size of line in case we appending
            line = new_lines[i]
            if strip:
                if i:
                    line = line.lstrip()
                if i < n:
                    line = line.rstrip()
            if line == '':  # just add empty line if empty
                _line[1] = True
                _line, w, h = add_line('', *bare_size)
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
                if lwe + isize[0] > uw:  # too wide
                    _do_last_line = False
                    if s != m:
                        # theres already some text, commit and go next line
                        # make sure there are no trailing spaces on prev line,
                        # may occur if spaces is followed by word not fitting
                        ln = line[s:m]
                        if strip and ln[-1] == ' ':
                            ln = ln.rstrip()
                            if ln:
                                _line, w, h = add_line(ln, *get_extents(ln))
                            else:
                                _do_last_line = isize[0]  # used as bool
                        else:
                            _line, w, h = add_line(line[s:m], lw, lh)
                        s = m
                    elif isize[0]:
                        _do_last_line = True

                    if _do_last_line:
                        ''' still need to check if the line ended in spaces
                        from before (e.g. line was broken with diff opts, some
                        ending in spaces) so walk back the words of this line
                        until it doesn't end in space. Still, nothing else can
                        be appended to this line anymore.
                        '''
                        while (_line[2] and (_line[2][-1][2].endswith(' ') or
                               _line[2][-1][2] == '')):
                            last_word = _line[2].pop()

                            if last_word[2] == '':  # empty str, pop it
                                _line[0][2] -= last_word[1][0]  # likely 0
                                continue

                            stripped = last_word[2].rstrip()  # ends with space
                            # subtract ending space length
                            diff = ((len(last_word[2]) - stripped) *
                                    last_word[0]['space_width'])
                            _line[0][2] = max(0, _line[0][2] - diff)  # line w
                            _line[2].append((   # re-add last word
                            last_word[0],
                            (max(0, last_word[1][0] - diff), last_word[1][1]),
                            stripped))
                        # now add the line to lines
                        lines.append(_line)
                        h += _line[0][3] - isize[1]
                        w = max(w, _line[0][2])
                        isize[0] = isize[1] = 0
                        _line = [[0, 0, 0, 0], False, []]

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
                        if lwe + isize[0] <= uw:
                            m = e
                            break
                        # if not, fit as much as possible into this line
                        while (m != e and
                               get_extents(line[s:m + 1])[0] + isize[0] <= uw):
                            m += 1
                        # not enough room for even single char, skip it
                        if m == s:
                            s += 1
                        else:
                            _line[1] = m == len(line)  # is last line?
                            _line, w, h = add_line(line[s:m],
                                                   *get_extents(line[s:m]))
                            s = m
                        m = s
                    m = s  # done with long word, go back to normal

                else:   # the word fits
                    # don't allow leading spaces on empty lines
                    if strip and m == s and line[s:e] == ' ' and not isize[0]:
                        s = m = e
                        continue
                    m = e

                if m == len(line):  # we're done
                    if s != len(line):
                        _line[1] = True  # line end
                        _line, w, h = add_line(line[s:], lwe, lhe)
                    break
                lw, lh = lwe, lhe  # save current lw/lh, then fit more in line

        # ensure the number of lines is not more than the user asked
        # above, we might have gone a few lines over
        if max_lines > 0:
            del lines[max_lines:]
        # now make sure we don't have lines outside specified height
        if uh is not None and h > uh:
            h, i = ypad * 2, 0
            while i < len(lines) and h + lines[i][0][3] <= uh:
                h += lines[i][0][3]
                i += 1
            del lines[max(1, i):]

        w += xpad * 2
        return w, h

    def _render_real(self):
        lines = self._cached_lines
        if not lines:
            self._render_begin()
            data = self._render_end()
            assert(data)
            if data is not None and data.width > 1:
                self.texture.blit_data(data)
            return

        options = lines[0][2][0][0]  # first options, first line, first word
        render_text = self._render_text
        get_extents = self.get_extents
        uw, uh = options['text_size']
        xpad, ypad = options['padding_x'], options['padding_y']
        x, y = xpad, ypad   # pos in the texture
        iw, ih = self._internal_size
        w, h = self.size
        contentw = iw - 2 * xpad
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

        for line_size, is_last_line, ((_, (lw, lh), line),) in\
            self._cached_lines:  # for plain label, each line is only one str
            x = xpad
            if halign[0] == 'c':  # center
                x = int((w - lw) / 2.)
            elif halign[0] == 'r':  # right
                x = int(w - lw - xpad)

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
                line_size[:2] = x, y
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

        options = dict(self.options)
        options.update({'space_width': self.get_extents(' ')[0]})
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

        w, h = self.layout_text(text, lines, (0, 0), options, self.get_extents)
        self._internal_size = w, h
        if uw:
            w = uw
        if uh:
            h = uh
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
