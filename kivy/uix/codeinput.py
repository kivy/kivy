'''
Code Input
==========

.. versionadded:: 1.5.0

.. image:: images/codeinput.jpg


The :class:`CodeInput` provides a box of editable highlited text like the one
shown in the image.

It supports all the features provided by the :class:`~kivy.uix.textinput` as
well as code highliting for `languages supported by pygments
<http://pygments.org/docs/lexers/>`_ along with `KivyLexer` for
:mod:`kivy.lang` highliting.

Usage example
-------------

To create a CodeInput with highliting for `KV language`::

    from kivy.uix.codeinput import CodeInput
    from kivy.extras.highlight import KivyLexer
    codeinput = CodeInput(lexer=KivyLexer())

To create a CodeInput with highliting for `Cython`::

    from kivy.uix.codeinput import CodeInput
    from pygments.lexers import CythonLexer
    codeinput = CodeInput(lexer=CythonLexer())

'''

__all__ = ('CodeInput', )

from pygments import highlight
from pygments import lexers
from pygments.formatters import BBCodeFormatter

from kivy.uix.textinput import TextInput
from kivy.core.text.markup import MarkupLabel as Label
from kivy.cache import Cache
from kivy.properties import ObjectProperty
from kivy.utils import get_hex_from_color

Cache_get = Cache.get
Cache_append = Cache.append

# TODO: color chooser for keywords/strings/...


class CodeInput(TextInput):
    '''CodeInput class, used for displaying highlighted code.
    '''

    lexer = ObjectProperty(None)
    '''This holds the selected Lexer used by pygments to highlight the code.


    :data:`lexer` is an :class:`~kivy.properties.ObjectProperty` and defaults to
    `PythonLexer`.
    '''

    def __init__(self, **kwargs):
        self.formatter = BBCodeFormatter()
        self.lexer = lexers.PythonLexer()
        self.text_color = '#000000'
        self._label_cached = Label()
        self.use_text_color = True

        super(CodeInput, self).__init__(**kwargs)

        self._line_options = kw = self._get_line_options()
        self._label_cached = Label(**kw)
        # use text_color as foreground color
        text_color = kwargs.get('foreground_color')
        if text_color:
            self.text_color = get_hex_from_color(text_color)
        # set foreground to white to allow text colors to show
        # use text_color as the default color in bbcodes
        self.use_text_color = False
        self.foreground_color = [1, 1, 1, .999]
        if not kwargs.get('background_color'):
            self.background_color = [.9, .92, .92, 1]

    def _create_line_label(self, text, hint=False):
        # Create a label from a text, using line options
        ntext = text.replace(u'\n', u'').replace(u'\t', u' ' * self.tab_width)
        if self.password and not hint:  # Don't replace hint_text with *
            ntext = u'*' * len(ntext)
        ntext = self._get_bbcode(ntext)
        kw = self._get_line_options()
        cid = '%s\0%s' % (ntext, str(kw))
        texture = Cache_get('textinput.label', cid)

        if not texture:
            # FIXME right now, we can't render very long line...
            # if we move on "VBO" version as fallback, we won't need to do this.
            # try to found the maximum text we can handle
            label = Label(text=ntext, **kw)
            if text.find(u'\n') > 0:
                label.text = u''
            else:
                label.text = ntext
            try:
                label.refresh()
            except ValueError:
                return

            # ok, we found it.
            texture = label.texture
            Cache_append('textinput.label', cid, texture)
            label.text = ''
        return texture

    def _get_line_options(self):
        kw = super(CodeInput, self)._get_line_options()
        kw['markup'] = True
        kw['valign'] = 'top'
        kw['codeinput'] = True
        return kw

    def _get_text_width(self, text, tab_width, _label_cached):
        # Return the width of a text, according to the current line options
        width = Cache_get('textinput.width', text + u'_' + repr(self.lexer))
        if width:
            return width
        lbl = self._create_line_label(text)
        width = lbl.width if lbl else 0
        Cache_append(
                    'textinput.width',
                    text + u'_' + repr(self.lexer), width)
        return width

    def _get_bbcode(self, ntext):
        # get bbcoded text for python
        try:
            ntext[0]
            # replace brackets with special chars that aren't highlighted
            # by pygment. can't use &bl; ... cause & is highlighted
            ntext = ntext.replace(u'[', u'\x01;').replace(u']', u'\x02;')
            ntext = highlight(ntext, self.lexer, self.formatter)
            ntext = ntext.replace(u'\x01;', u'&bl;').replace(u'\x02;', u'&br;')
            # replace special chars with &bl; and &br;
            ntext = ''.join((u'[color=', str(self.text_color), u']',
                             ntext, u'[/color]'))
            ntext = ntext.replace(u'\n', u'')
            return ntext
        except IndexError:
            return ''

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

    def on_lexer(self, instance, value):
        self._trigger_refresh_text()

    def on_foreground_color(self, instance, text_color):
        if not self.use_text_color:
            self.use_text_color = True
            return
        self.text_color = get_hex_from_color(text_color)
        self.use_text_color = False
        self.foreground_color = (1, 1, 1, .999)
        self._trigger_refresh_text()


if __name__ == '__main__':
    from kivy.extras.highlight import KivyLexer
    from kivy.app import App

    class CodeInputTest(App):
        def build(self):
            return CodeInput(lexer=KivyLexer(),
                font_name='data/fonts/DroidSansMono.ttf', font_size=12,
                text='''
#:kivy 1.0

<YourWidget>:
    canvas:
        Color:
            rgb: .5, .5, .5
        Rectangle:
            pos: self.pos
            size: self.size''')

    CodeInputTest().run()
