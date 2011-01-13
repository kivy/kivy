'''
MarkupLabel: Handle drawing of text with markup
'''

__all__ = ('MarkupLabel', )

import kivy
from kivy.parser import parse_color
from kivy.logger import Logger
import re
from . import Label, LabelBase

# We need to do this trick when documentation is generated
MarkupLabelBase = Label
if Label is None:
    MarkupLabelBase = LabelBase


class MarkupLabel(MarkupLabelBase):
    '''Markup text label.

    Markup is defined as tag with []. Example of markup text :

        [b]Hello [color=ff0000]world[/b][/color]

    Available markups tags :
        * [b][/b] : bold
        * [i][/i] : italic
        * [font=<str>][/font] : font name
        * [size=<integer>][/size] : size
        * [color=#<color>][/color] : text color
    '''

    def __init__(self, *largs, **kwargs):
        self._style_stack = {}
        super(MarkupLabel, self).__init__(*largs, **kwargs)

    @property
    def markup(self):
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
        w, h = 0, 0
        x, y = 0, 0
        lw, lh = 0, 0
        nl = False
        if real:
            self._render_begin()

        for item in self.markup:
            if item == '[b]':
                self._push_style('bold')
                self.options['bold'] = True
            elif item == '[/b]':
                self._pop_style('bold')
            elif item == '[i]':
                self._push_style('italic')
                self.options['italic'] = True
            elif item == '[/i]':
                self._pop_style('italic')
            elif item.startswith('[size='):
                size = int(item[6:-1])
                self._push_style('font_size')
                self.options['font_size'] = size
            elif item == '[/size]':
                self._pop_style('font_size')
            elif item.startswith('[color='):
                color = parse_color(item[7:-1])
                self._push_style('color')
                self.options['color'] = color
            elif item == '[/color]':
                self._pop_style('color')
            elif item.startswith('[font='):
                fontname = item[6:-1]
                self._push_style('font_name')
                self.options['font_name'] = fontname
            elif item == '[/font]':
                self._pop_style('font_name')
            else:
                args = x, y, w, h, lw, lh, nl
                args = self.render_label(real, item, args)
                x, y, w, h, lw, lh, nl = args

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
        w = self.texture.width
        h = self.texture.height
        if self.texture is None:
            self.texture = kivy.Texture.create(size=self.size)
            self.texture.flip_vertical()
        elif self.width > w or self.height > h:
            self.texture = kivy.Texture.create(size=self.size)
            self.texture.flip_vertical()
        else:
            self.texture = self.texture.get_region(
                0, 0, self.width, self.height)

        # update texture
        self.texture.blit_data(data)

    def render_label(self, real, label, args):
        x, y, w, h, lw, lh, nl = args
        uw, uh = self.usersize

        # precalculate id/name
        if not self.fontid in self._cache_glyphs:
            self._cache_glyphs[self.fontid] = {}
        cache = self._cache_glyphs[self.fontid]

        if not real:
            # verify that each glyph have size
            glyphs = list(set(label))
            for glyph in glyphs:
                if not glyph in cache:
                    cache[glyph] = self.get_extents(glyph)

        # first, split lines
        glyphs = []
        lines = []
        _x, _y = x, y
        for word in re.split(r'( |\n)', label):

            if word == '':
                continue

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
            x, y = _x, _y
            for i in xrange(len(lines)):
                size, glyphs = lines[i]
                for glyph in glyphs:
                    lw, lh = cache[glyph]
                    self._render_text(glyph, x, y)
                    x += lw
                if i < len(lines) - 1:
                    y += size[1]
                    x = 0

        return (x, y, w, h, lw, lh, nl)

