import kivy
from kivy.base import runTouchApp
from kivy.core.window import Window
from kivy.core.image import Image
from kivy.graphics import *
from kivy.lib.transformations import clip_matrix

img = Image('examples/border.png')
c = Canvas()

with c:
    c.context.set('projection_mat', clip_matrix(0,Window.width,0,Window.height,-1,1))
    SetColor(1.0, 1.0, 1.0, 1.0)
    BorderRectangle(pos=(300,100) ,size=(200, 200), border=(20,20,20,20), texture=img.texture)
    # PathStart(200,200)
    # PathLineTo(400,400)
    # PathLineTo(500,200)
    # PathLineTo(400, 100)
    # PathLineTo(100, 500)
    # PathEnd()   

    
    #Rectangle(pos=(100,100), size=(50,50))
def draw():
    c.draw()

Window.bind(on_draw=draw)

runTouchApp()

