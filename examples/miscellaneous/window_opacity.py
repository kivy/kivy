from kivy.base import runTouchApp
from kivy.core.window import Window
from kivy.uix.slider import Slider

opacity_slider = Slider(
    min=0.0,
    max=1.0,
    value=0.6,
    value_track=True,
    value_track_color=[1, 0, 0, 1])


def change_opacity(instance, value):
    Window.opacity = value


opacity_slider.bind(value=change_opacity)

runTouchApp(opacity_slider)
