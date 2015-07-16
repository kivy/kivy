# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.factory import Factory

TEXTURE = 'kiwi.jpg'
YELLOW = (1, .7, 0)
ORANGE = (1, .45, 0)
RED = (1, 0, 0)
WHITE = (1, 1, 1)


class RoundedRectangleWidget(Widget):
    def prepare(self):
        with self.canvas:
            Color(*WHITE)

            # Rectangle of default size 100x100
            Rectangle(pos=(50, 400))

            # RoundedRectangles of default size 100x100:

            # Textured:
            RoundedRectangle(
                pos=(175, 400), radius=[0, 50, 0, 50], source=TEXTURE)

            # Colored:
            Color(*YELLOW)
            RoundedRectangle(pos=(300, 400), radius=[0, 50, 0, 50])

            # Textured + Colored
            # Color(.3,.3,.3, 1)
            RoundedRectangle(
                pos=(425, 400), radius=[0, 50, 0, 50], source=TEXTURE)

            # Possible radius arguments:
            # 1) Same value for each corner
            Color(*ORANGE)

            # With same radius 20x20
            RoundedRectangle(pos=(50, 275), radius=[20])

            # With same radius dimensions 20x40
            RoundedRectangle(pos=(175, 275), radius=[(20, 40)])

            # 2) Different values for each corner
            Color(*RED)

            # With different radiuses NxN:
            RoundedRectangle(pos=(300, 275), radius=[10, 20, 30, 40])

            # With different radiuses:
            RoundedRectangle(
                pos=(425, 275), radius=[(10, 20), (20, 30), (30, 40), (40, 50)])

            # Default ellipses
            Color(*WHITE)
            Ellipse(pos=(50, 150))
            Ellipse(pos=(175, 150))
            Ellipse(pos=(300, 150))
            Ellipse(pos=(425, 150))

            # Radius dimensions can't be bigger than half of the figure side
            RoundedRectangle(pos=(175, 150), radius=[9000], source=TEXTURE)

            # Segments parameter defines how many segments each corner has.
            # More segments - more roundness
            Color(*RED)
            RoundedRectangle(pos=(300, 150), radius=[9000])
            RoundedRectangle(pos=(425, 150), radius=[9000], segments=15)

            Color(*ORANGE)
            RoundedRectangle(pos=(425, 150), radius=[9000], segments=2)

            Color(*YELLOW)
            RoundedRectangle(pos=(425, 150), radius=[9000], segments=1)

            # Various sizes
            # You can cut corners by setting segments to 1.
            # You can set different segment count to corners,
            # by using a list useful for lowering vertex count
            # by using small amount on small corners, while using
            # bigger amount on bigger corners.
            RoundedRectangle(
                pos=(50, 25),
                radius=[40],
                segments=[1, 1, 10, 10],
                size=(125, 100))

            # If radius dimension is 0, then the corner will be sharp
            # (90 degrees). It is also possible to mix tuple values
            # with numeric
            Color(*ORANGE)
            RoundedRectangle(
                pos=(200, 25),
                radius=[(40, 20),
                45.5, 45.5, 0],
                segments=[2, 3, 3, 1], size=(125, 100))

            Color(*RED)
            RoundedRectangle(
                pos=(350, 25),
                radius=[(40, 40), (40, 40), (20, 20), (20, 20)],
                segments=[2, 3, 3, 2],
                size=(150, 100))


class DrawRoundedRectanglesApp(App):
    def build(self):
        kv = '''
Widget:
    canvas:
        Color:
            rgba: 1, 1,1, 1

        RoundedRectangle:
            pos: 575, 400
            size: 100, 100
            radius: [0, 50, 0, 50]
            source: 'kiwi.jpg'

        Color:
            rgba: 0, 0.8, 0.8, 1

        RoundedRectangle:
            pos: 575, 275
            size: 100, 100
            radius: [(10, 20), (20, 30), (30, 40), (40, 50)]

        RoundedRectangle:
            pos: 575, 150
            size: 100, 100
            radius: [9000]
            segments: 15

        RoundedRectangle:
            pos: 550, 25
            size: 150, 100
            segments: [1, 2, 1, 3]
            radius: [30, 40, 30, 40]

'''
        widget = RoundedRectangleWidget()
        widget.prepare()
        kvrect = Builder.load_string(kv)
        widget.add_widget(kvrect)
        return widget

if __name__ == '__main__':
    DrawRoundedRectanglesApp().run()
