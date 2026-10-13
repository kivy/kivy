from kivy.config import Config

# Enable shaped window
Config.set("graphics", "shaped", 1)
Config.set("kivy", "window_shape", "./shaped_window_images/shape1.png")

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty

# Set the window background color to transparent
Window.clearcolor = (0, 0, 0, 0)

# Define the KV layout
kv_layout = '''
FloatLayout:
    size_hint: 1, 1
    canvas.before:
        Color:
            rgba: 0, 0, 0, 1
        Rectangle:
            size: self.size
            pos: self.pos
    ScatterLayout:
        BoxLayout:
            size_hint: 0.5, 0.5
            pos_hint: {"center_x": 0.5, "center_y": 0.5}
            Button:
                text: "Next Shape"
                on_press: app.next_shape()
'''


class ShapedWindowApp(App):
    shaped_image_src = StringProperty("")

    def build(self):
        # List of image paths to cycle through
        self.image_paths = [
            "./shaped_window_images/shape1.png",
            "./shaped_window_images/shape2.png",
            "./shaped_window_images/shape3.png",
            "./shaped_window_images/shape4.png",
            "./shaped_window_images/shape5.png",
        ]
        self.current_index = 0

        return Builder.load_string(kv_layout)

    def next_shape(self):
        # Move to the next image in the list
        self.current_index = (self.current_index + 1) % len(self.image_paths)
        Window.shape_image = self.image_paths[self.current_index]


if __name__ == "__main__":
    ShapedWindowApp().run()
