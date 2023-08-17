from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

Builder.load_string('''
#:import window kivy.core.window.Window
<Layout>:
    orientation: 'vertical'
    Label:
        text: f'Window opacity: {window.opacity}'
        font_size: 25
    Slider:
        size_hint_y: 4
        min: 0.0
        max: 1.0
        value: window.opacity
        on_value: window.opacity = args[1]
''')


class Layout(BoxLayout):
    pass


class OpacityWindowApp(App):

    def build(self):
        return Layout()


if __name__ == '__main__':
    OpacityWindowApp().run()
