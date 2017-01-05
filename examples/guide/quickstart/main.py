import kivy

from kivy.app import App
from kivy.uix.button import Button
kivy.require('1.0.6')  # replace with your current kivy version !


class MyApp(App):

    def build(self):
        return Button(text='Hello World')


if __name__ == '__main__':
    MyApp().run()
