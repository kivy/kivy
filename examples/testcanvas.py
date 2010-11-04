import kivy
from kivy.base import runTouchApp
from kivy.core.window import Window
from kivy.core.image import Image
from kivy.graphics import Canvas, Rectangle, BorderRectangle
from kivy.lib.transformations import clip_matrix

img = Image('examples/test.png')
c = Canvas()

with c:
    c.context.set('color', (1,1,1,1))
    c.context.set('projection_mat', clip_matrix(0,Window.width,0,Window.height,-1,1))
    Rectangle(size=[100, 100], texture=img.texture)


def draw():
    c.draw()

Window.bind(on_draw=draw)

runTouchApp()

