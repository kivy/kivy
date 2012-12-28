'''
Custom shape & collide widget
=============================

This is a Triangle widget with a triangle shape based on 3 points (p1, p2, p3),
plus a custom collision function.

The p1, p2, p3 are automatically calculated from the position and the size of
the Widget bounding box. We are using them to draw the triangle shape.
(Please note in the kv the special case for Scatter.)

Then, we need to setup a new collision function to collide only on the triangle.
We are using a external method that will check if a point is inside a polygon
(we consider our triangle as a polygon).
'''


import kivy
kivy.require('1.0.8')

from kivy.uix.scatter import Scatter
from kivy.properties import ListProperty
from kivy.lang import Builder


Builder.load_string('''
<Triangle>:
    # example for doing a triangle
    # this will automatically recalculate pX from pos/size
    p1: 0, 0
    p2: self.width, 0
    p3: self.width / 2, self.height

    # If you use a Widget instead of Scatter as base class, you need that:
    #p1: self.pos
    #p2: self.right, self.y
    #p3: self.center_x, self.top

    # draw something
    canvas:
        Color:
            rgb: 1, 0, 0
        Triangle:
            points: self.p1 + self.p2 + self.p3
''')


def point_inside_polygon(x, y, poly):
    '''Taken from http://www.ariel.com.au/a/python-point-int-poly.html
    '''
    n = len(poly)
    inside = False
    p1x = poly[0]
    p1y = poly[1]
    for i in range(0, n + 2, 2):
        p2x = poly[i % n]
        p2y = poly[(i + 1) % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


class Triangle(Scatter):
    p1 = ListProperty([0, 0])
    p2 = ListProperty([0, 0])
    p3 = ListProperty([0, 0])

    def collide_point(self, x, y):
        x, y = self.to_local(x, y)
        return point_inside_polygon(x, y,
                self.p1 + self.p2 + self.p3)

if __name__ == '__main__':
    from kivy.base import runTouchApp
    runTouchApp(Triangle(size_hint=(None, None)))
