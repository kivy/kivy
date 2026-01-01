import os
# os.environ["KIVY_GL_BACKEND"] = "angle_sdl3"

# import random

# from kivy.app import App
# from kivy.clock import Clock
# from kivy.core.window import Window
# from kivy.lang import Builder
# from kivy.properties import ListProperty, ObjectProperty
# from kivy.uix.floatlayout import FloatLayout

# from kivy.core.skia.skia_graphics import SkiaSurface

# Window.clear = lambda: None


# class UI(FloatLayout):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.surface = SkiaSurface(*map(int, Window.size))

#         def _reset_surface(_):
#             width, height = map(int, Window.size)
#             self.surface = SkiaSurface(width, height)
#             print(f"Surface updated - new size: {width}x{height}")

#         Window.bind(on_draw=_reset_surface)

#         self.surface.clear_canvas(100, 0, 0, 255)

#         def clear_canvas_with_color(_):
#             r = random.randint(0, 255)
#             g = random.randint(0, 255)
#             b = random.randint(0, 255)

#             self.surface.clear_canvas(r, g, b, 255)
#             self.surface.draw_circle(
#                 random.randint(0, 500),  # x
#                 random.randint(0, 500),  # y
#                 200,  # width
#                 200,  # height
#                 0,  # segments
#                 0,  # angle_start
#                 360,  # angle_end
#             )  # basic circle

#             self.surface.flush_and_submit()
#             Window.flip()

#         Clock.schedule_interval(clear_canvas_with_color, 1 / 60)


# class MyApp(App):
#     def build(self):
#         return UI()


# if __name__ == "__main__":
#     MyApp().run()


# import sys
# from kivy.app import App
# from kivy.core.window import Window
# from kivy.uix.widget import Widget
# from kivy.lang import Builder


# from kivy.core.skia.graphics import SkiaCanvas, SkiaEllipse


# # Window.clearcolor = 1, 1, 1, 1


# class MainWidget(Widget):
#     Builder.load_string("""
# <MainWidget>:
#     # pos_hint :{'center_x': .5, 'center_y': .5}
#     on_touch_move:
#         self.center = args[1].pos
#     canvas:
#         # Color:
#         #     rgb: 0, 1, 0  # green color
#         SkiaEllipse:
#             pos: (self.center_x - 100, self.center_y - 100)
#             size: 200, 200
#             angle_start: 0
#             angle_end: 270
#             segments: 5
#     """)


#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.size_hint = (0.5, 0.5)

#         # self.canvas = SkiaCanvas()
#     #     with self.canvas:
#     #         self._elipse = SkiaEllipse()
#     #     self.bind(size=self._update_graphics)

#     # def _update_graphics(self, _, size):
#     #     # print("_update_graphics")
#     #     self._elipse.pos = self.center


# class EllipseApp(App):
#     def build(self):
#         return MainWidget()


# # EllipseApp().run()

# # sys.exit(0)


import os

os.environ["GRAPHICS_ENGINE"] = "skia"

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock

from kivy.graphics import Ellipse


class EllipseDemo(Widget):
    def __init__(self, **kwargs):
        super(EllipseDemo, self).__init__(**kwargs)
        self.ellipses = []
        self.scroll_y = 0
        self.direction = 1

        self.count = 500

        # Create x ellipses
        for i in range(self.count):
            # Position the ellipses on a 10x10 grid
            ellipse = Ellipse(
                size=(250, 250), angle_start=0, angle_end=180, segments=6
            )
            # ellipse.texture = r""
            self.ellipses.append(ellipse)
            self.canvas.add(ellipse)

        # Update the scroll every 1/120s
        Clock.schedule_interval(self.update_scroll, 1 / 120)

    def update_scroll(self, dt):
        if self.scroll_y >= self.height:
            self.direction = -20
        if self.scroll_y <= 0:
            self.direction = 20

        self.scroll_y += self.direction

        # Update the segments for all ellipses
        for i in range(self.count):
            pos = (
                (self.width / 20) * (i % 20),
                (self.height / 20) * (i // 20) + self.scroll_y,
            )
            self.ellipses[i].pos = pos

        print(f"FPS: {Clock.get_fps()}")


class EllipseDemoApp(App):
    def build(self):
        return EllipseDemo()


if __name__ == "__main__":
    EllipseDemoApp().run()
