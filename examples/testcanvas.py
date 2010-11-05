from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import *


class TestApp(App):
    def build(self):
        a = Widget()
        tex = Image('examples/kivy.jpg').texture
        tex2 = Image('examples/test.png').texture
        with a.canvas:

            Color(1,1,1,1)
            Ellipse(pos=(300,100), size=(200,100), texture=tex2)
            Color(1,0,0,1)
            Rectangle(texture=tex2)
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
        return a

TestApp().run()
