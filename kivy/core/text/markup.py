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
    reference will be available in :attr:`MarkupLabel.refs`
``[anchor=<str>]``
    Put an anchor in the text. You can get the position of your anchor within
    the text with :attr:`MarkupLabel.anchors`
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
from kivy.core.text.text_layout import layout_text
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
        self._internal_size = 0, 0

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
        self._cached_lines = lines = []
        self._refs = {}
        self._anchors = {}
        w = h = 0
        uw, uh = self.text_size
        spush = self._push_style
        spop = self._pop_style
        options = self.options
        options['_ref'] = None
        options['script'] = 'normal'
        uhh = None if uh is not None and options['valign'][-1] != 'p' else uh
        options['strip'] = options['strip'] or options['halign'][-1] == 'y'
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
                    x, y = lines[-1].x, lines[-1].y
                else:
                    x = y = 0
                self._anchors[ref] = x, y
            else:
                item = item.replace('&bl;', '[').replace(
                    '&br;', ']').replace('&amp;', '&')
                opts = copy(options)
                extents = self.get_cached_extents()
                opts['space_width'] = extents(' ')[0]
                w, h, clipped = layout_text(item, lines, (w, h), (uw, uhh),
                    opts, extents, True, False)

        if len(lines):  # remove any trailing spaces from the last line
            w, h, clipped = layout_text('', lines, (w, h), (uw, uhh),
                copy(options), self.get_cached_extents(), True, True)

        # when valign is not top, for markup we layout everything (text_size[1]
        # is temporarily set to None) and after layout cut to size if too tall
        if uh != uhh and h > uh and len(lines) > 1:
            if options['valign'][-1] == 'm':  # bottom
                i = 0
                while i < len(lines) - 1 and h > uh:
                    h -= lines[i].h
                    i += 1
                del lines[:i]
            else:  # middle
                i = 0
                top = int(h / 2. + uh / 2.)  # remove extra top portion
                while i < len(lines) - 1 and h > top:
                    h -= lines[i].h
                    i += 1
                del lines[:i]
                i = len(lines) - 1  # remove remaining bottom portion
                while i and h > uh:
                    h -= lines[i].h
                    i -= 1
                del lines[i + 1:]

        self._internal_size = w, h
        if uw:
            w = uw
        if uh:
            h = uh
        if h > 1 and w < 2:
            w = 2
        if w < 1:
            w = 1
        if h < 1:
            h = 1
        return w, h

    def _real_render(self):
        lines = self._cached_lines
        options = None
        for line in lines:
            if len(line.words):  # get opts from first line, first word
                options = line.words[0].options
                break
        if not options:  # there was no text to render
            self._render_begin()
            data = self._render_end()
            assert(data)
            if data is not None and data.width > 1:
                self.texture.blit_data(data)
            return

        old_opts = self.options
        render_text = self._render_text
        xpad, ypad = options['padding_x'], options['padding_y']
        x, y = xpad, ypad   # pos in the texture
        iw, ih = self._internal_size  # the real size of text, not texture
        w, h = self.size
        halign = options['halign']
        valign = options['valign']
        refs = self._refs
        self._render_begin()

        if valign == 'bottom':
            y = h - ih + ypad
        elif valign == 'middle':
            y = int((h - ih) / 2 + ypad)

        for layout_line in lines:  # for plain label each line has only one str
            lw, lh = layout_line.w, layout_line.h
            x = xpad
            if halign[0] == 'c':  # center
                x = int((w - lw) / 2.)
            elif halign[0] == 'r':  # right
                x = max(0, int(w - lw - xpad))
            layout_line.x = x
            layout_line.y = y
            psp = pph = 0
            for word in layout_line.words:
                options = self.options = word.options
                # calculate sub/super script pos
                if options['script'] == 'superscript':
                    script_pos = max(0, psp if psp else self.get_descent())
                    psp = script_pos
                    pph = word.lh
                elif options['script'] == 'subscript':
                    script_pos = min(lh - word.lh, ((psp + pph) - word.lh)
                                     if pph else (lh - word.lh))
                    pph = word.lh
                    psp = script_pos
                else:
                    script_pos = (lh - word.lh) / 1.25
                    psp = pph = 0
                render_text(word.text, x, y + script_pos)

                # should we record refs ?
                ref = options['_ref']
                if ref is not None:
                    if not ref in refs:
                        refs[ref] = []
                    refs[ref].append((x, y, x + word.lw, y + word.lh))
                x += word.lw
            y += lh

        # get data from provider
        data = self._render_end()
        assert(data)

        # If the text is 1px width, usually, the data is black.
        # Don't blit that kind of data, otherwise, you have a little black bar.
        if data is not None and data.width > 1:
            self.texture.blit_data(data)
