import kivy
from kivy.base import runTouchApp
from kivy.core.window import Window
from kivy.graphics import Canvas, Rectangle


c = Canvas()

with c:
    Rectangle(size=[100, 100])


def draw():
    c.draw()

Window.bind(on_draw=draw)

runTouchApp()

