import kivy
from kivy.base import runTouchApp, Clock
from kivy.core.window import Window
from kivy.core.image import Image
from kivy.graphics import *
from kivy.lib.transformations import clip_matrix

from random import random

img = Image('examples/border.png')
c = Canvas()

my_color = None
t1 = None
with c:
    c.context.set('projection_mat', clip_matrix(0,Window.width,0,Window.height,-1,1))
    PushMatrix()
    t1= Translate(200,0,0)
    my_color = Color(1.0, 1.0, 1.0, 1.0)
    my_rect = Rectangle(pos=(100,100), size=(100,100))
    PushMatrix()


def draw(*args):
    t1.x = t1.x - .1
    c.draw()

Window.bind(on_draw=draw)

runTouchApp()

