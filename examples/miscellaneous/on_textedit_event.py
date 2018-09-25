# -*- coding: utf-8 -*-

'''
on_textedit event sample.
'''
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.uix.textinput import TextInput
from kivy.base import EventLoop


class TextInputIME(TextInput):
    testtext = StringProperty()

    def __init__(self, **kwargs):
        super(TextInputIME, self).__init__(**kwargs)
        EventLoop.window.bind(on_textedit=self._on_textedit)

    def _on_textedit(self, window, text):
        self.testtext = text


class MainWidget(Widget):
    text = StringProperty()

    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.text = ''

    def confim(self):
        self.text = self.ids["text_box"].text

    def changeFont(self):
        try:
            LabelBase.register(DEFAULT_FONT, self.ids["text_font"].text)
        except Exception:
            self.ids["text_font"].text = "can't load font."


class TextEditTestApp(App):
    def __init__(self, **kwargs):
        super(TextEditTestApp, self).__init__(**kwargs)

    def build(self):
        return MainWidget()


if __name__ == '__main__':
    Builder.load_string('''
<MainWidget>:
    BoxLayout:
        orientation: 'vertical'
        size: root.size
        BoxLayout:
            Label:
                size_hint_x: 3
                text: "Multi language font file path"
            TextInput:
                id: text_font
                size_hint_x: 5
            Button:
                size_hint_x: 2
                text: "Change Font"
                on_press: root.changeFont()
        BoxLayout:
            Label:
                size_hint_x: 3
                text: "Text editing by IME"
            Label:
                size_hint_x: 7
                text:text_box.testtext
                canvas.before:
                    Color:
                        rgb: 0.5765 ,0.5765 ,0.5843
                    Rectangle:
                        pos: self.pos
                        size: self.size
        BoxLayout:
            Label:
                size_hint_x: 3
                text: "Enter text ->"
            TextInputIME:
                id: text_box
                size_hint_x: 7
                focus: True
        BoxLayout:
            Button:
                size_hint_x: 3
                text: "Confirm text property"
                on_press: root.confim()
            Label:
                size_hint_x: 7
                text: root.text
                canvas.before:
                    Color:
                        rgb: 0.5765 ,0.5765 ,0.5843
                    Rectangle:
                        pos: self.pos
                        size: self.size
    ''')
    TextEditTestApp().run()
