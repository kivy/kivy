from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

Builder.load_string('''
<WindowOpacity>:
    orientation: 'vertical'
    Label:
        text: 'Window Opacity'
        size_hint_y: 0.2
        font_size : '30sp'
    Label:
        id: set_opacity_label
        size_hint_y: 0.1
        font_size : '20sp'
    Slider:
        id: opacity_slider
        size_hint_y: 0.5
        min: 0.0
        max: 1.0
        value: 0.6
        value_track: True
        value_track_color: [1, 0, 0, 1]
        on_value: root.opacity_change(self.value)
    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: 0.2
        Button:
            text: "Get Window Opacity"
            on_press: root.get_window_opacity()
        Label:
            id: get_opacity_label
            font_size : '20sp'
''')


class WindowOpacity(BoxLayout):
    opacity_label = ObjectProperty()

    def __init__(self, **kwargs):
        super(WindowOpacity, self).__init__(**kwargs)
        self.opacity_change(self.ids['opacity_slider'].value)

    def opacity_change(self, value):
        Window.opacity = value
        self.ids['set_opacity_label'].text = 'Opacity: ' + '%.2f' % value

    def get_window_opacity(self):
        self.ids['get_opacity_label'].text = \
            'Opacity: ' + '%.2f' % Window.opacity


class WindowOpacityApp(App):
    def build(self):
        return WindowOpacity()


if __name__ == '__main__':
    WindowOpacityApp().run()
