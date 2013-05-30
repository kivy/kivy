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
``[sub][/sub]``
    Display the text at a subscript position relative to the text before it.
``[sup][/sup]``
    Display the text at a superscript position relative to the text before it.

If you need to escape the markup from the current text, use
:func:`kivy.utils.escape_markup`.
'''

__all__ = ('MarkupLabel', )

import re
from kivy.properties import dpi2px
from kivy.parser import parse_color
from kivy.logger import Logger
from kivy.core.text import Label, LabelBase
from copy import copy
from math import ceil

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
        if k not in self._style_stack or len(self._style_stack[k]) == 0:
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
        options['script'] = 'normal'
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
                item = item[6:-1]
                try:
                    if item[-2:] in ('px', 'pt', 'in', 'cm', 'mm', 'dp', 'sp'):
                        size = dpi2px(item[:-2], item[-2:])
                    else:
                        size = int(item)
                except ValueError:
                    raise
                    size = options['font_size']
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
            elif item[:5] == '[sub]':
                spush('font_size')
                spush('script')
                options['font_size'] = options['font_size'] * .5
                options['script'] = 'subscript'
            elif item == '[/sub]':
                spop('font_size')
                spop('script')
            elif item[:5] == '[sup]':
                spush('font_size')
                spush('script')
                options['font_size'] = options['font_size'] * .5
                options['script'] = 'superscript'
            elif item == '[/sup]':
                spop('font_size')
                spop('script')
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
        if h is None or h < 0:
            h = None
        if w is None or w < 0:
            w = None
        if w is None:
            if not lines:
                w = 1
            else:
                w = max([line[0] for line in lines])
        if h is None:
            if not lines:
                h = 1
            else:
                h = sum([line[1] for line in lines])
        return int(ceil(w)), int(ceil(h))

    def _pre_render_label(self, word, options, lines):
        # precalculate id/name
        if not self.fontid in self._cache_glyphs:
            self._cache_glyphs[self.fontid] = {}
        cache = self._cache_glyphs[self.fontid]

        # verify that each glyph have size
        glyphs = list(set(word))
        glyphs.append(' ')
        get_extents = self.get_extents
        for glyph in glyphs:
            if not glyph in cache:
                cache[glyph] = get_extents(glyph)

        # get last line information
        if len(lines):
            line = lines[-1]
        else:
            # line-> line width, line height, is_last_line, is_first_line, words
            # words -> (w, h, word)...
            line = [0, 0, 0, 1, []]
            lines.append(line)

        # extract user limitation
        uw, uh = self.text_size

        # split the word
        default_line_height = get_extents(' ')[1] * self.options['line_height']
        for part in re.split(r'( |\n)', word):

            if part == '':
                continue

            if part == '\n':
                # put a new line!
                line = [0, default_line_height, 0, 1, []]
                # skip last line for justification.
                if lines:
                    lines[-1][2] = 1
                    lines[-1]
                lines.append(line)
                continue

            # get current line information
            lw, lh = line[:2]

            # calculate the size of the part
            # (extract all extents of the part,
            # calculate width through extents due to kerning
            # and get the maximum height)
            pg = [cache[g] for g in part]
            pw = get_extents(part)[0]
            ph = max([g[1] for g in pg])
            ph = ph * self.options['line_height']
            options = copy(options)

            # check if the part can be put in the line
            if uw is None or lw + pw < uw:
                # no limitation or part can be contained in the line
                # then append the part to the line
                line[4].append((pw, ph, part, options))
                # and update the line size
                line[0] += pw
                line[1] = max(line[1], ph)
            else:
                # part can't be put in the line, do a new one...
                line = [pw, ph, 0, 0, [(pw, ph, part, options)]]
                lines.append(line)
        # set last_line to be skipped for justification
        lines[-1][2] = 1

    def _real_render(self):
        # use the lines to do the rendering !
        self._render_begin()

        r = self._render_text

        # convert halign/valign to int, faster comparison
        av = {'top': 0, 'middle': 1, 'bottom': 2}[self.options['valign']]
        ah = {'left': 0, 'center': 1, 'right': 2,
                'justify': 3, }[self.options['halign']]

        y = 0
        w, h = self._size
        refs = self._refs
        _lines = self._lines
        txt_height = sum(line[1] for line in _lines)

        for line in _lines:
            lh = line[1]
            lw = line[0]
            last_line = line[2]
            first_line = line[3]

            # horizontal alignement
            if ah in (0, 3):
                # left
                x = 0
            elif ah == 1:
                # center
                x = int((w - lw) / 2)
            else:
                x = w - lw

            # vertical alignment
            if y == 0:
                if av == 1:
                    # center
                    y = int((h - txt_height) / 2)
                elif av == 2:
                    # bottom
                    y = h - (txt_height)

             # justification
            just_space = 0
            first_space = 0
            if ah > 2:
                # justified
                if line[4] and not last_line:
                    last_word = line[4][-1][2]

                    x = first_space = last_space = space_width = _spaces = 0
                    for pw, ph, word, options in line[4]:
                        _spaces += 1 if word == ' ' else 0

                    if word == ' ':
                        last_space = 1
                        space_width = pw
                    if line[4][0][2][0] == ' ':
                        first_space = 1
                        space_width += pw
                    _spaces -= last_space + first_space

                    # divide left over space between `spaces`
                    if _spaces:
                        just_space = (((w - lw + space_width) * 1.)
                                    / (_spaces * 1.))

            # previous part height/pos = 0
            psp = pph = 0
            for pw, ph, part, options in line[4]:
                self.options = options
                if not first_line and first_space:
                    first_line = 1
                    continue
                if part == ' ':
                    x += just_space

                # calculate sub/super script pos
                if options['script'] == 'superscript':
                    script_pos = max(0,
                                    psp
                                    if psp else
                                    self.get_descent())
                    psp = script_pos
                    pph = ph
                elif options['script'] == 'subscript':
                    script_pos = min(lh - ph,
                                    ((psp + pph) - ph)
                                    if pph else
                                    (lh - ph))
                    pph = ph
                    psp = script_pos
                else:
                    script_pos = (lh - ph) / 1.25
                    psp = pph = 0
                r(part, x, y + script_pos)

                # should we record refs ?
                ref = options['_ref']
                if ref is not None:
                    if not ref in refs:
                        refs[ref] = []
                    refs[ref].append((x, y, x + pw, y + ph))

                x += pw
            y += line[1]

        # get data from provider
        data = self._render_end()
        assert(data)

        # update texture
        # If the text is 1px width, usually, the data is black.
        # Don't blit that kind of data, otherwise, you have a little black bar.
        if data is not None and data.width > 1:
            self.texture.blit_data(data)

