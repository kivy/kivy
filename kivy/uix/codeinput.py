# -*- coding: utf-8 -*-
'''
Code Input
==========

.. versionadded:: 1.5.0

.. image:: images/codeinput.jpg


The :class:`CodeInput` provides a box of editable highlited text, like the ones
shown in the image.

It supports all the features supported by the :class:`~kivy.uix.textinput` and
Code highliting for `languages supported by pygments
<http://pygments.org/docs/lexers/>`_ along with `KivyLexer` for `KV Language`
highliting.

Usage example
-------------

To create a CodeInput with highliting for `KV language`::

    from kivy.uix.codeinput import CodeInput
    from kivy.extras.highlight import KivyLexer
    codeinput = CodeInput(lexer=KivyLexer)

To create a CodeInput with highliting for `Cython`::

    from kivy.uix.codeinput import CodeInput
    from pygments.lexers import CythonLexer
    codeinput = CodeInput(lexer=CythonLexer)

'''

__all__ = ('CodeInput', )

from pygments import highlight
from pygments import lexers
from kivy.extras.highlight import KivyLexer
from pygments.formatters import BBCodeFormatter

from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.cache import Cache
from kivy.properties import BooleanProperty, ObjectProperty

Cache_get = Cache.get
Cache_append = Cache.append

# TODO: fix empty line rendering
# TODO: color chooser for keywords/strings/...


class CodeInput(TextInput):
    '''CodeInput class, used for displaying highlited code.
    '''

    lexer = ObjectProperty(lexers.PythonLexer)
    '''This holds the selected Lexer used by pygments to highlite the code


    :data:`lexer` is a :class:`~kivy.properties.ObjectProperty` defaults to
    `PythonLexer`
    '''

    def __init__(self, **kwargs):
        super(CodeInput, self).__init__(**kwargs)
        self._line_options = kw = self._get_line_options()
        self._markup_label_cached = Label(**kw)
        self.formatter = BBCodeFormatter()
        text_color = kwargs.get('foreground_color')
        #use text_color as foreground color
        if text_color:
            self.text_color = (text_color[0], text_color[1], text_color[2],
                text_color[3])
        else:
            self.text_color = (0, 0, 0, 1)
        # set foreground to white to allow text colors to show
        # use text_color as the default color in bbcodes
        self.foreground_color = [1, 1, 1, 1]
        if not kwargs.get('background_color'):
            self.background_color = [.9, .92, .92, 1]

    def _create_line_label(self, text):
        # Create a label from a text, using line options
        ntext = text.replace('\n', '').replace('\t', ' ' * self.tab_width)
        if self.password:
            ntext = '*' * len(ntext)
        ntext = self._get_bbcode(ntext)
        kw = self._get_line_options()
        cid = '%s\0%s' % (ntext, str(kw))
        texture = Cache_get('textinput.label', cid)

        if not texture:
            # FIXME right now, we can't render very long line...
            # if we move on "VBO" version as fallback, we won't need to do this.
            # try to found the maximum text we can handle
            label = Label(text=ntext, **kw)
            if text.find('\n') > 0:
                label.text = ''
            else:
                label.text = ntext
            label.texture_update()

            # ok, we found it.
            texture = label.texture
            Cache_append('textinput.label', cid, texture)
            label.text = ''
        return texture

    def _get_line_options(self):
        kw = super(CodeInput, self)._get_line_options()
        kw['markup'] = True
        kw['valign'] = 'top'
        return kw

    def _get_bbcode(self, ntext):
        # get bbcoded text for python
        try:
            ntext[0]
            # replace brackets with special chars that aren't highlighted
            # by pygment. can't use &bl; ... cause & is highlighted
            # if at some time support for braille is added then replace these
            # characters with something else
            ntext = ntext.replace('[', u'⣿;').replace(']', u'⣾;')
            ntext = highlight(ntext, self.lexer(), self.formatter)
            ntext = ntext.replace(u'⣿;', '&bl;').replace(u'⣾;', '&br;')
            # replace special chars with &bl; and &br;
            ntext = ''.join(('[color=rgba', str(self.text_color), ']',
            ntext, '[/color]'))
            ntext = ntext.replace('\n', '')
            return ntext
        except IndexError:
            return ''

    # overriden to get accurate cursor position for markup text
    def _get_text_width(self, text, tab_width, label_cached):
        # fix cursor placement diff cause of markup
        kw = self._get_line_options()
        cid = '%s\0%s' % (text, str(kw))
        width = Cache_get('textinput.width', cid)
        if not width:
            _markup_label_cached = Label(**kw)
            if text == '\n' or text.find('\n') > 0:
                width = 0
            else:
                _markup_label_cached.text = self._get_bbcode(text)
                _markup_label_cached.texture_update()
                texture = _markup_label_cached.texture
                # use width of texture of '.' instead of ' ' in start of line
                # which is of 0 width in markup
                width = texture.width if texture else\
                    label_cached.get_extents('.')[0] * len(text)
            Cache.append('textinput.width', cid, width)
            _markup_label_cached.text = ''
        return width

    # overriden to prevent cursor position off screen
    def _cursor_offset(self):
        '''Get the cursor x offset on the current line
        '''
        offset = 0
        try:
            if self.cursor_col:
                offset = self._get_text_width(
                    self._lines[self.cursor_row][:self.cursor_col])
        except:
            pass
        finally:
            return offset
