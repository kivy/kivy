from kivy.app import App
from kivy.extras.highlight import KivyLexer
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.codeinput import CodeInput
from kivy.uix.popup import Popup
from kivy.properties import ListProperty
from kivy.core.window import Window
from pygments import lexers
from pygame import font as fonts
import codecs, os

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
----------------------Java-----------------------------------

public static byte toUnsignedByte(int intVal) {
    byte byteVal;
    return (byte)(intVal & 0xFF);
}
---------------------kv lang---------------------------------
#:kivy 1.0

<YourWidget>:
    canvas:
        Color:
            rgb: .5, .5, .5
        Rectangle:
            pos: self.pos
            size: self.size
---------------------HTML------------------------------------
<!-- Place this tag where you want the +1 button to render. -->
<div class="g-plusone" data-annotation="inline" data-width="300"></div>

<!-- Place this tag after the last +1 button tag. -->
<script type="text/javascript">
  (function() {
    var po = document.createElement('script');
    po.type = 'text/javascript';
    po.async = true;
    po.src = 'https://apis.google.com/js/plusone.js';
    var s = document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(po, s);
  })();
</script>
'''


class Fnt_SpinnerOption(SpinnerOption):
    pass


class LoadDialog(Popup):

    def load(self, path, selection):
        self.choosen_file = [None, ]
        self.choosen_file = selection
        Window.title = selection[0][selection[0].rfind(os.sep)+1:]
        self.dismiss()

    def cancel(self):
        self.dismiss()


class SaveDialog(Popup):

    def save(self, path, selection):
        _file = codecs.open(selection, 'w', encoding='utf8')
        _file.write(self.text)
        Window.title = selection[selection.rfind(os.sep)+1:]
        _file.close()
        self.dismiss()

    def cancel(self):
        self.dismiss()


class CodeInputTest(App):

    files = ListProperty([None, ])

    def build(self):
        b = BoxLayout(orientation='vertical')
        languages = Spinner(
            text='language',
            values=sorted(['KvLexer', ] + lexers.LEXERS.keys()))

        languages.bind(text=self.change_lang)

        menu = BoxLayout(
            size_hint_y=None,
            height='30pt')
        fnt_size = Spinner(
            text='12',
            values=map(str, range(5, 40)))
        fnt_size.bind(text=self._update_size)
        fnt_name = Spinner(
            text='DroidSansMono',
            option_cls=Fnt_SpinnerOption,
            values=sorted(map(str, fonts.get_fonts())))
        fnt_name.bind(text=self._update_font)
        mnu_file = Spinner(
            text='File',
            values=('Open', 'SaveAs', 'Save', 'Close'))
        mnu_file.bind(text=self._file_menu_selected)

        menu.add_widget(mnu_file)
        menu.add_widget(fnt_size)
        menu.add_widget(fnt_name)
        menu.add_widget(languages)
        b.add_widget(menu)

        self.codeinput = CodeInput(
            lexer=KivyLexer(),
            font_name='data/fonts/DroidSansMono.ttf', font_size=12,
            text=example_text)

        b.add_widget(self.codeinput)

        return b

    def _update_size(self, instance, size):
        self.codeinput.font_size = float(size)

    def _update_font(self, instance, fnt_name):
        instance.font_name = self.codeinput.font_name =\
            fonts.match_font(fnt_name)

    def _file_menu_selected(self, instance, value):
        if value == 'File':
            return
        instance.text = 'File'
        if value == 'Open':
            if not hasattr(self, 'load_dialog'):
                self.load_dialog = LoadDialog()
            self.load_dialog.open()
            self.load_dialog.bind(choosen_file=self.setter('files'))
        elif value == 'SaveAs':
            if not hasattr(self, 'saveas_dialog'):
                self.saveas_dialog = SaveDialog()
            self.saveas_dialog.text = self.codeinput.text
            self.saveas_dialog.open()
        elif value == 'Save':
            if self.files[0]:
                _file = codecs.open(self.files[0], 'w', encoding='utf8')
                _file.write(self.codeinput.text)
                _file.close()
        elif value == 'Close':
            if self.files[0]:
                self.codeinput.text = ''
                Window.title = 'untitled'

    def on_files(self, instance, values):
        if not values[0]:
            return
        _file = codecs.open(values[0], 'r', encoding='utf8')
        self.codeinput.text = _file.read()
        _file.close()

    def change_lang(self, instance, l):
        if l == 'KvLexer':
            lx = KivyLexer()
        else:
            lx = lexers.get_lexer_by_name(lexers.LEXERS[l][2][0])
        self.codeinput.lexer = lx

if __name__ == '__main__':
    CodeInputTest().run()
