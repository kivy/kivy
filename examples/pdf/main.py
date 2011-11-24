#!/usr/bin/env python
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.properties import StringProperty

class PDFReader(BoxLayout):
    filename = StringProperty('')

    def __init__(self, **kwargs):
        super(PDFReader, self).__init__(**kwargs)
        b = Button(text='<')
        b.size_hint = None, None
        b.size = 100, 100
        b.bind(on_release=self.prececent)
        self.add_widget(b)

        self.pdf = Image(source=self.filename)
        self.add_widget(self.pdf)

        b = Button(text='>')
        b.size_hint = None, None
        b.size = 100, 100
        b.bind(on_release=self.next)
        self.add_widget(b)

    def next(self, *_):
        try:
            self.pdf.page += 1
        except:
            self.pdf.page = 0

    def prececent(self, *_):
        self.pdf.page -= 1

class MyApp(App):
    def build(self):
        return PDFReader(filename='evaluation software engeener.pdf')

if __name__ == '__main__':
    MyApp().run()

