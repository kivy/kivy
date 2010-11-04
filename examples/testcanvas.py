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

with c:
    c.context.set('projection_mat', clip_matrix(0,Window.width,0,Window.height,-1,1))
    my_color = Color(1.0, 1.0, 1.0, 1.0)
    my_rect = Rectangle(pos=(100,100), size=(500,500))




my_color.update(1,0,0,1)

def change_something(*args, **kwargs):
    my_color.update(random(), random(), random(), random())

def change_something2(*args, **kwargs):
    my_rect.size = random() * 100, random() * 100
    my_rect.pos = random() * 100, random() * 100

Clock.schedule_interval(change_something, 2.0)
Clock.schedule_interval(change_something2, 0.33)


def draw():
    c.draw()

Window.bind(on_draw=draw)

runTouchApp()

