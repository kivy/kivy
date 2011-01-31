from kivy.app import App
from kivy.uix.button import Button

class TestApp(App):
    def build(self):
        return Button(text='hello world')

if __name__ == '__main__':
    TestApp().run()
