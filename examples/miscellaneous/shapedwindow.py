from kivy.config import Config
Config.set('graphics', 'shaped', 1)

from kivy.resources import resource_find
default_shape = Config.get('kivy', 'window_shape')
alpha_shape = resource_find('data/logo/kivy-icon-512.png')

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    BooleanProperty,
    StringProperty,
    ListProperty,
)


Builder.load_string('''
#:import win kivy.core.window.Window

<Root>:
    orientation: 'vertical'
    BoxLayout:
        Button:
            text: 'default_shape'
            on_release: app.shape_image = app.default_shape
        Button:
            text: 'alpha_shape'
            on_release: app.shape_image = app.alpha_shape

''')


class Root(BoxLayout):
    pass


class ShapedWindow(App):
    shape_image = StringProperty('', force_dispatch=True)

    def on_shape_image(self, instance, value):
        if 'kivy-icon' in value:
            Window.size = (512, 512)
            Window.shape_image = self.alpha_shape
        else:
            Window.size = (800, 600)
            Window.shape_image = self.default_shape

    def build(self):
        self.default_shape = default_shape
        self.alpha_shape = alpha_shape

        return Root()


if __name__ == '__main__':
    ShapedWindow().run()
