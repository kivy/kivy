from kivy.app import App
from kivy.uix.slider import Slider
from kivy.lang import Builder

Builder.load_string('''
#:import window kivy.core.window.Window
<OpacitySlider>:
    min: 0.0
    max: 1.0
    value: window.opacity
    on_value: window.opacity = args[1]
''')


class OpacitySlider(Slider):
    pass


class OpacityWindowApp(App):

    def build(self):
        return OpacitySlider()


if __name__ == '__main__':
    OpacityWindowApp().run()
