from kivy.app import App
from kivy.extras.highlight import KivyLexer
from kivy.factory import Factory
import pygments

example_text = '''
---------------------Python----------------------------------
import kivy
kivy.require('1.0.6') # replace with your current kivy version !
from kivy.app import App
from kivy.uix.button import Button

class MyApp(App):
    def build(self):
        return Button(text='Hello World')

if __name__ == '__main__':
    MyApp().run()
----------------------Java------------------------------------

public static byte toUnsignedByte(int intVal) {
    byte byteVal;
    return (byte)(intVal & 0xFF);
}
---------------------kv lang-------------------------
#:kivy 1.0

<YourWidget>:
    canvas:
        Color:
            rgb: .5, .5, .5
        Rectangle:
            pos: self.pos
            size: self.size
-----------------HTML-----------------------------
<!-- Place this tag where you want the +1 button to render. -->
<div class="g-plusone" data-annotation="inline" data-width="300"></div>

<!-- Place this tag after the last +1 button tag. -->
<script type="text/javascript">
  (function() {
    var po = document.createElement('script'); po.type = 'text/javascript'; po.async = true;
    po.src = 'https://apis.google.com/js/plusone.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(po, s);
  })();
</script>
'''


class CodeInputTest(App):
    def build(self):
        b = Factory.BoxLayout(orientation='vertical')
        languages = Factory.Spinner(
            text='language',
            values=sorted(['KvLexer', ] + pygments.lexers.LEXERS.keys()),
            size_hint_y=None,
            height='30pt')

        languages.bind(text=self.change_lang)
        b.add_widget(languages)

        self.codeinput = Factory.CodeInput(
            lexer=KivyLexer(),
            font_name='data/fonts/DroidSansMono.ttf', font_size=12,
            text=example_text)

        b.add_widget(self.codeinput)

        return b

    def change_lang(self, instance, l):
        if l == 'KvLexer':
            lx = KivyLexer()

        else:
            lx = pygments.lexers.get_lexer_by_name(
                pygments.lexers.LEXERS[l][2][0])

        self.codeinput.lexer = lx


CodeInputTest().run()
