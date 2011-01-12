'''
Vector
======

class to handle Vector operation.

For example, if you want to get length of a vector::

    >>> from kivy.vector import Vector
    >>> v = Vector(1, 5)
    >>> print v.length()

'''

__all__ = ('Vector', )

import math


class Vector(list):
    '''Represents a 2D vector.'''

    def __init__(self, *largs):
        if len(largs) == 1:
            super(Vector, self).__init__(largs[0])
        elif len(largs) == 2:
            super(Vector, self).__init__(largs)
        else:
            raise Exception('Invalid vector')

    def _get_x(self):
        return self[0]
    def _set_x(self, x):
        self[0] = x
    x = property(_get_x, _set_x)

    def _get_y(self):
        return self[1]
    def _set_y(self, y):
        self[1] = y
    y = property(_get_y, _set_y)

    def __getslice__(self, i, j):
        try:
            # use the list __getslice__ method and convert
            # result to vector
            return Vector(super(Vector, self).__getslice__(i, j))
        except Exception:
            raise TypeError('vector::FAILURE in __getslice__')

    def __add__(self, val):
        return Vector(map(lambda x, y: x + y, self, val))

    def __iadd__(self, val):
        if type(val) in (int, float):
            self.x += val
            self.y += val
        else:
            self.x += val.x
            self.y += val.y
        return self

    def __neg__(self):
        return Vector(map(lambda x: -x, self))

    def __sub__(self, val):
        return Vector(map(lambda x, y: x - y, self, val))

    def __isub__(self, val):
        if type(val) in (int, float):
            self.x -= val
            self.y -= val
        else:
            self.x -= val.x
            self.y -= val.y
        return self

    def __mul__(self, val):
        try:
            return Vector(map(lambda x, y: x * y, self, val))
        except Exception:
            return Vector(map(lambda x: x * val, self))

    def __imul__(self, val):
        if type(val) in (int, float):
            self.x *= val
            self.y *= val
        else:
            self.x *= val.x
            self.y *= val.y
        return self

    def __rmul__(self, val):
        return (self * val)

    def __truediv__(self, val):
        try:
            return Vector(map(lambda x, y: x / y, self, val))
        except Exception:
            return Vector(map(lambda x: x / val, self))

    def __div__(self, val):
        try:
            return Vector(map(lambda x, y: x / y, self, val))
        except Exception:
            return Vector(map(lambda x: x / val, self))

    def __rdiv__(self, val):
        try:
            return Vector(map(lambda x, y: x / y, other, val))
        except Exception:
            return Vector(map(lambda x: other / x, val))

    def __idiv__(self, val):
        if type(val) in (int, float):
            self.x /= val
            self.y /= val
        else:
            self.x /= val.x
            self.y /= val.y
        return self


    def length(self):
        '''Returns the length of a vector'''
        return math.sqrt(self[0] ** 2 + self[1] ** 2)

    def length2(self):
        '''Returns the length of a vector squared.'''
        return self[0] ** 2 + self[1] ** 2

    def distance(self, to):
        '''Returns the distance between two points.'''
        return math.sqrt((self[0] - to[0]) ** 2 + (self[1] - to[1]) ** 2)

    def distance2(self, to):
        '''Returns the distance between two points squared.'''
        return (self[0] - to[0]) ** 2 + (self[1] - to[1]) ** 2

    def normalize(self):
        '''Returns a new vector that has the same direction as vec,
        but has a length of one.'''
        if self[0] == 0. and self[1] == 0.:
            return Vector(0., 0.)
        return self / self.length()

    def dot(self, a):
        '''Computes the dot product of a and b'''
        return self[0] * a[0] + self[1] * a[1]

    def angle(self, a):
        '''Computes the angle between a and b'''
        angle = -(180/math.pi) * math.atan2(
            self[0] * a[1] - self[1] * a[0],
            self[0] * a[0] + self[1] * a[1])
        return angle

    def rotate(self, angle):
        '''Rotate the vector'''
        angle = math.radians(angle)
        return Vector((self[0] * math.cos(angle)) - (self[1] * math.sin(angle)),
                      (self[1] * math.cos(angle)) + (self[0] * math.sin(angle)))

    @staticmethod
    def line_intersection(v1, v2, v3, v4):
        '''
        Finds the intersection point between the lines (1)v1->v2 and (2)v3->v4
        and returns it as a vector object

        For math see: http://en.wikipedia.org/wiki/Line-line_intersection
        '''
        #linear algebar sucks...seriously!!
        x1, x2, x3, x4 = float(v1[0]), float(v2[0]), float(v3[0]), float(v4[0])
        y1, y2, y3, y4 = float(v1[1]), float(v2[1]), float(v3[1]), float(v4[1])

        u = (x1 * y2 - y1 * x2)
        v = (x3 * y4 - y3 * x4)
        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if denom == 0:
            return None

        px = (u * (x3 - x4) - (x1 - x2) * v) / denom
        py = (u * (y3 - y4) - (y1 - y2) * v) / denom

        return Vector(px, py)

    @staticmethod
    def in_bbox(point, a, b):
        '''Return a true if `point` is in bbox defined by `a` and `b`'''
        return ((point[0] <= a[0] and point[0] >= b[0] or
                 point[0] <= b[0] and point[0] >= a[0]) and
                (point[1] <= a[1] and point[1] >= b[1] or
                 point[1] <= b[1] and point[1] >= a[1]))

