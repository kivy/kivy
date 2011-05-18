import kivy
kivy.require('1.0.5')

from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty


class Controller(FloatLayout):
    '''Create a controler that can receive custom widget from kv lang
    + add action to be called from kv lang
    '''
    label_wid = ObjectProperty(None)
    info = StringProperty('')

    def do_action(self):
        self.label_wid.text = 'My label after button press'
        self.info = 'New info text'


class ControllerApp(App):

    def build(self):
        return Controller(info='Hello world')

if __name__ in ('__android__', '__main__'):
    ControllerApp().run()
