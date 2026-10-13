from kivy.app import App
from kivy.lang import Builder

kv = '''
#:import window kivy.core.window.Window

BoxLayout:
    orientation: 'vertical'
    Label:
        text: f'Window opacity: {window.opacity}'
        font_size: '25sp'
    Slider:
        size_hint_y: 4
        min: 0.0
        max: 1.0
        value: window.opacity
        on_value: window.opacity = args[1]
'''


class WindowOpacityApp(App):

    def build(self):
        return Builder.load_string(kv)


if __name__ == '__main__':
    WindowOpacityApp().run()
