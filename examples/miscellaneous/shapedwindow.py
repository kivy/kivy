from kivy.config import Config

Config.set("graphics", "shaped", 1)

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty

Window.clearcolor = (0, 0, 0, 0)

KV = '''
FloatLayout:
    size_hint: 1, 1
    canvas.before:
        Color:
            rgba: 0, 0, 0, 1
        Rectangle:
            size: self.size
            pos: self.pos
    Image:
        source: app.shaped_image_src
        size_hint: 0.5, 0.5
        pos_hint: {"center_x": 0.5, "center_y": 0.5}
    Button:
        text: "Next Shape"
        size_hint: 0.1, 0.1
        pos_hint: {"center_x": 0.5, "center_y": 0.5}
        on_press: app.next_shape()
'''

class ShapedWindowApp(App):
    shaped_image_src = StringProperty("")

    def build(self):
        self.image_paths = [
            "PNG_transparency_demonstration_1.png",
            "data/logo/kivy-icon-512.png",
        ]
        self.current_index = 0

        return Builder.load_string(KV)

    def next_shape(self):
        self.current_index = (self.current_index + 1) % len(self.image_paths)
        self.shaped_image_src = self.image_paths[self.current_index]
        Window.shape_image = self.image_paths[self.current_index]


if __name__ == "__main__":
    ShapedWindowApp().run()
