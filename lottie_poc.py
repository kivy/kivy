"""
Usage Note:
You can navigate between Lottie animations using the < and > keys on your keyboard.
"""

import os

os.environ["GRAPHICS_ENGINE"] = "skia"
os.environ["KIVY_GL_BACKEND"] = "angle_sdl3"

import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout

from kivy.core.skia.skia_graphics import Surface

Window.clear = lambda: None


def _reset_skia_surface(_):
    width, height = map(int, Window.size)
    Window.skia_surface = Surface(width, height)
    print(f"Surface updated - new size: {width}x{height}")


Window.bind(on_draw=_reset_skia_surface)
Window.skia_surface = Surface(*map(int, Window.size))


class UI(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.lottie_files = [
            "confetti.json",
            "lego_loader.json",
            "anim_1.json",
            "anim_2.json",
            "anim_3.json",
            "anim_4.json",
        ]
        self.current_index = 1  # "lego_loader.json"
        self.t = 0

        self.load_lottie()

        Clock.schedule_interval(self._update_lottie_pos_size, 1)
        Clock.schedule_interval(self._update_lottie_anim, 1 / 60)

        Window.bind(on_key_down=self.on_key_down)

    def load_lottie(self):
        filename = os.path.join(
            "kivy/core/skia/assets/lottie/",
            self.lottie_files[self.current_index],
        )
        Window.skia_surface.draw_lottie(filename)
        print(f"Loaded Lottie: {filename}")

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        if key == 275:
            self.current_index = (self.current_index + 1) % len(
                self.lottie_files
            )
            self.load_lottie()
        elif key == 276:
            self.current_index = (self.current_index - 1) % len(
                self.lottie_files
            )
            self.load_lottie()

    def _update_lottie_pos_size(self, dt):
        Window.skia_surface.update_lottie_pos_and_size(
            random.randint(0, 300),
            random.randint(0, 300),
            *[random.randint(100, 500)] * 2,
        )

    def _update_lottie_anim(self, dt):
        self.t += 1 / 300
        if self.t >= 1:
            self.t = 0

        Window.skia_surface.clear_canvas(0, 0, 100, 255)
        Window.skia_surface.lottie_seek(self.t)
        Window.skia_surface.flush_and_submit()
        Window.flip()


class MyApp(App):
    def build(self):
        return UI()


if __name__ == "__main__":
    MyApp().run()
