import kivy
from kivy.base import runTouchApp
from kivy.core.window import Window
from kivy.core.image import Image
from kivy.graphics import Canvas, Rectangle, BorderRectangle, SetColor
from kivy.lib.transformations import clip_matrix

img = Image('examples/border.png')
c = Canvas()

with c:
    c.context.set('projection_mat', clip_matrix(0,Window.width,0,Window.height,-1,1))
    SetColor(1.0, 0.0, 1.0, 0.5, blend=1)
    BorderRectangle(size=(400, 400), border=(20,20,20,20), texture=img.texture)


def draw():
    c.draw()

Window.bind(on_draw=draw)

runTouchApp()

