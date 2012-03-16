'''
Text Markup
===========

.. versionadded:: 1.1.0

We provide a simple text-markup for inline text styling. The syntax look the
same as the `BBCode <http://en.wikipedia.org/wiki/BBCode>`_.

A tag is defined as ``[tag]``, and might have a closed tag associated:
``[/tag]``. Example of a markup text::

    [b]Hello [color=ff0000]world[/b][/color]

The following tags are availables:

``[b][/b]``
    Activate bold text
``[i][/i]``
    Activate italic text
``[font=<str>][/font]``
    Change the font
``[size=<integer>][/size]``
    Change the font size
``[color=#<color>][/color]``
    Change the text color
``[ref=<str>][/ref]``
    Add an interactive zone. The reference + all the word box inside the
    reference will be available in :data:`MarkupLabel.refs`
``[anchor=<str>]``
    Put an anchor in the text. You can get the position of your anchor within
    the text with :data:`MarkupLabel.anchors`
'''

__all__ = ('MarkupLabel', )

from kivy.graphics.texture import Texture
from kivy.utils import platform
from kivy.parser import parse_color
from kivy.logger import Logger
import re
from . import Label, LabelBase
from copy import copy

# We need to do this trick when documentation is generated
MarkupLabelBase = Label
if Label is None:
    MarkupLabelBase = LabelBase


class MarkupLabel(MarkupLabelBase):
    '''Markup text label.

    See module documentation for more informations.
    '''

    def __init__(self, *largs, **kwargs):
        self._style_stack = {}
        self._refs = {}
        super(MarkupLabel, self).__init__(*largs, **kwargs)

    @property
    def refs(self):
        '''Get the bounding box of all the ``[ref=...]``::

            { 'refA': ((x1, y1, x2, y2), (x1, y1, x2, y2)), ... }
        '''
        return self._refs

    @property
    def anchors(self):
        '''Get the position of all the ``[anchor=...]``::

            { 'anchorA': (x, y), 'anchorB': (x, y), ... }
        '''
        return self._anchors

    @property
    def markup(self):
        '''Return the text with all the markup splitted::

            >>> MarkupLabel('[b]Hello world[/b]').markup
            >>> ('[b]', 'Hello world', '[/b]')

        '''
        s = re.split('(\[.*?\])', self.label)
        s = [x for x in s if x != '']
        return s

    def _push_style(self, k):
        if not k in self._style_stack:
            self._style_stack[k] = []
        self._style_stack[k].append(self.options[k])

    def _pop_style(self, k):
        if len(self._style_stack[k]) == 0:
            Logger.warning('Label: pop style stack without push')
            return
        v = self._style_stack[k].pop()
        self.options[k] = v

    def render(self, real=False):
        options = copy(self.options)
        if not real:
            ret = self._pre_render()
        else:
            ret = self._real_render()
        self.options = options
        return ret

    def _pre_render(self):
        # split markup, words, and lines
        # result: list of word with position and width/height
        # during the first pass, we don't care about h/valign
        self._lines = lines = []
        self._refs = {}
        self._anchors = {}
        spush = self._push_style
        spop = self._pop_style
        options = self.options
        options['_ref'] = None
        for item in self.markup:
            if item == '[b]':
                spush('bold')
                options['bold'] = True
                self.resolve_font_name()
            elif item == '[/b]':
                spop('bold')
                self.resolve_font_name()
            elif item == '[i]':
                spush('italic')
                options['italic'] = True
                self.resolve_font_name()
            elif item == '[/i]':
                spop('italic')
                self.resolve_font_name()
            elif item[:6] == '[size=':
                size = int(item[6:-1])
                spush('font_size')
                options['font_size'] = size
            elif item == '[/size]':
                spop('font_size')
            elif item[:7] == '[color=':
                color = parse_color(item[7:-1])
                spush('color')
                options['color'] = color
            elif item == '[/color]':
                spop('color')
            elif item[:6] == '[font=':
                fontname = item[6:-1]
                spush('font_name')
                options['font_name'] = fontname
                self.resolve_font_name()
            elif item == '[/font]':
                spop('font_name')
                self.resolve_font_name()
            elif item[:5] == '[ref=':
                ref = item[5:-1]
                spush('_ref')
                options['_ref'] = ref
            elif item == '[/ref]':
                spop('_ref')
            elif item[:8] == '[anchor=':
                ref = item[8:-1]
                if len(lines):
                    x, y = lines[-1][0:2]
                else:
                    x = y = 0
                self._anchors[ref] = x, y
            else:
                item = item.replace('&bl;', '[').replace(
                        '&br;', ']').replace('&amp;', '&')
                self._pre_render_label(item, options, lines)

        # calculate the texture size
        w, h = self.text_size
        if h < 0:
            h = None
        if w < 0:
            w = None
        if w is None:
            w = max([line[0] for line in lines])
        if h is None:
            h = sum([line[1] for line in lines])
        return w, h

    def _pre_render_label(self, word, options, lines):
        # precalculate id/name
        if not self.fontid in self._cache_glyphs:
            self._cache_glyphs[self.fontid] = {}
        cache = self._cache_glyphs[self.fontid]

        # verify that each glyph have size
        glyphs = list(set(word))
        get_extents = self.get_extents
        for glyph in glyphs:
            if not glyph in cache:
                cache[glyph] = get_extents(glyph)

        # get last line information
        if len(lines):
            line = lines[-1]
        else:
            # line-> line width, line height, words
            # words -> (w, h, word)...
            line = [0, 0, []]
            lines.append(line)

        # extract user limitation
        uw, uh = self.text_size

        # split the word
        for part in re.split(r'( |\n)', word):

            if part == '':
                continue

            if part == '\n':
                # put a new line!
                line = [0, 0, []]
                lines.append(line)
                continue

            # get current line information
            lw, lh = line[:2]

            # calculate the size of the part
            # (extract all extents of the part,
            # sum the width, and get the maximum height)
            pg = [cache[g] for g in part]
            pw = sum([g[0] for g in pg])
            ph = max([g[1] for g in pg])

            options = copy(options)

            # check if the part can be put in the line
            if uw is None or lw + pw < uw:
                # no limitation or part can be contained in the line
                # then append the part to the line
                line[2].append((pw, ph, part, options))
                # and update the line size
                line[0] += pw
                line[1] = max(line[1], ph)
            else:
                # part can't be put in the line, do a new one...
                line = [pw, ph, [(pw, ph, part, options)]]
                lines.append(line)

    def _real_render(self):
        # use the lines to do the rendering !
        self._render_begin()

        r = self._render_text

        # convert halign/valign to int, faster comparaison
        #av = {'top': 0, 'middle': 1, 'bottom': 2}[self.options['valign']]
        ah = {'left': 0, 'center': 1, 'right': 2}[self.options['halign']]

        y = 0
        w, h = self._size
        refs = self._refs
        for line in self._lines:
            lh = line[1]

            # horizontal alignement
            if ah == 0:
                x = 0
            elif ah == 1:
                x = int((w - line[0]) / 2)
            else:
                x = w - line[0]

            for pw, ph, part, options in line[2]:
                self.options = options
                r(part, x, y + (lh - ph) / 1.25)

                # should we record refs ?
                ref = options['_ref']
                if ref is not None:
                    if not ref in refs:
                        refs[ref] = []
                    refs[ref].append((x, y, x + pw, y + ph))

                #print 'render', repr(part), x, y, (lh, ph), options
                x += pw
            y += line[1]

        # get data from provider
        data = self._render_end()
        assert(data)

        # create texture is necessary
        texture = self.texture
        mipmap = self.options['mipmap']
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

        # update texture
        self.texture = texture
        self.texture.blit_data(data)

