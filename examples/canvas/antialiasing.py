'''
Antialiasing Example
====================

Kivy 2.3.0 introduced several vertex instructions with antialiasing:
SmoothRectangle, SmoothEllipse, SmoothRoundedRectangle, SmoothQuad and
SmoothTriangle. This demo script shows the difference between 'standard'
(non-antialiased) and antialiased graphics.

'''

from kivy.app import App
from kivy.lang import Builder

kv = '''
GridLayout:
    rows: 6
    columns: 2
    spacing: [2]
    Label:
        height: '50sp'
        size_hint_y: None
        font_size: '25sp'
        text: "Standard"
    Label:
        height: '50sp'
        size_hint_y: None
        font_size: '25sp'
        text: "Antialiased"
    Widget:
        canvas:
            Color:
                rgb: 1.0, 0.0, 0.0
            RoundedRectangle:
                pos: self.pos
                size: self.size
                segments: 50
                radius: [(200, 200), (100, 50), (250, 250),(100, 250),]
    Widget:
        canvas:
            SmoothRoundedRectangle:
                pos: self.pos
                size: self.size
                segments: 50
                radius: [(200, 200), (100, 50), (250, 250),(100, 250),]
    Widget:
        canvas:
            Color:
                rgb: 0.0, 1.0, 0.0
            Triangle:
                points: [self.x, self.y + self.height, self.x + self.width, \
                            self.y + self.height / 2, self.x + 150, self.y]
    Widget:
        canvas:
            SmoothTriangle:
                points: [self.x, self.y + self.height, self.x + self.width, \
                            self.y + self.height / 2, self.x + 150, self.y]
    Widget:
        canvas:
            Color:
                rgb: 0.0, 0.0, 1.0
            Ellipse:
                pos: self.pos
                size: self.size
                angle_start: 20
                angle_end: 300
    Widget:
        canvas:
            SmoothEllipse:
                pos: self.pos
                size: self.size
                angle_start: 20
                angle_end: 300
'''


class AntialiasDemoApp(App):

    def build(self):
        return Builder.load_string(kv)


if __name__ == '__main__':
    AntialiasDemoApp().run()
