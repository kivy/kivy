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
    Color(0,0,1,1)
    Ellipse(pos=(100,100), size=(200,100), segments = 32)
    '''
    PathStart(100,100)
    PathLineTo(200,200)
    PathLineTo(300,200)
    PathLineTo(300,400)
    PathLineTo(200,250)
    PathLineTo(100,300)
    PathLineTo(150,250)
    PathClose()
    PathEnd()
    '''
def draw(*args):
    c.draw()

Window.bind(on_draw=draw)

runTouchApp()

