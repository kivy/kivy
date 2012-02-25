'''
Vector
======

The :class:`Vector` represent a 2D vector (x, y).
Our implementation is made in top of a Python list.

Exemple for constructing a Vector::

    >>> # Construct a point at 82,34
    >>> v = Vector(82, 34)
    >>> v[0]
    82
    >>> v.x
    82
    >>> v[1]
    34
    >>> v.y
    34

    >>> # Construct by giving a list of 2 values
    >>> pos = (93, 45)
    >>> v = Vector(pos)
    >>> v[0]
    93
    >>> v.x
    93
    >>> v[1]
    45
    >>> v.y
    45


Optimized usage
---------------

Most of time, you can use a list for arguments, instead of using a Vector. For
example, if you want to have the distance between 2 points::

    a = (10, 10)
    b = (87, 34)

    # optimized method
    print 'distance between a and b:', Vector(a).distance(b)

    # non-optimized method
    va = Vector(a)
    vb = Vector(b)
    print 'distance between a and b:', va.distance(vb)


Vector operators
----------------

The :class:`Vector` support some numeric operator like +, -, /::

    >>> Vector(1, 1) + Vector(9, 5)
    [10, 6]

    >>> Vector(9, 5) - Vector(5, 5)
    [4, 0]

    >>> Vector(10, 10) / Vector(2., 4.)
    [5.0, 2.5]

    >>> Vector(10, 10) / 5.
    [2.0, 2.0]


You can also do in-place operations::

    >>> v = Vector(1, 1)
    >>> v += 2
    >>> v
    [3, 3]
    >>> v *= 5
    [15, 15]
    >>> v /= 2.
    [7.5, 7.5]

'''

__all__ = ('Vector', )

import math


class Vector(list):
    '''Vector class. See module documentation for more information.
    '''

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
    ''':data:`x` represent the first element in the list.

    >>> v = Vector(12, 23)
    >>> v[0]
    12
    >>> v.x
    12
    '''

    def _get_y(self):
        return self[1]

    def _set_y(self, y):
        self[1] = y

    y = property(_get_y, _set_y)
    ''':data:`y` represent the second element in the list.

    >>> v = Vector(12, 23)
    >>> v[1]
    23
    >>> v.y
    23

    '''

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
            return Vector(map(lambda x, y: x / y, self, val))
        except Exception:
            return Vector(map(lambda x: self / x, val))

    def __idiv__(self, val):
        if type(val) in (int, float):
            self.x /= val
            self.y /= val
        else:
            self.x /= val.x
            self.y /= val.y
        return self

    def length(self):
        '''Returns the length of a vector.

        >>> Vector(10, 10).length()
        14.142135623730951
        >>> pos = (10, 10)
        >>> Vector(pos).length()
        14.142135623730951

        '''
        return math.sqrt(self[0] ** 2 + self[1] ** 2)

    def length2(self):
        '''Returns the length of a vector squared.

        >>> Vector(10, 10).length2()
        200
        >>> pos = (10, 10)
        >>> Vector(pos).length2()
        200

        '''
        return self[0] ** 2 + self[1] ** 2

    def distance(self, to):
        '''Returns the distance between two points.

        >>> Vector(10, 10).distance((5, 10))
        5.
        >>> a = (90, 33)
        >>> b = (76, 34)
        >>> Vector(a).distance(b)
        14.035668847618199

        '''
        return math.sqrt((self[0] - to[0]) ** 2 + (self[1] - to[1]) ** 2)

    def distance2(self, to):
        '''Returns the distance between two points squared.

        >>> Vector(10, 10).distance2((5, 10))
        25

        '''
        return (self[0] - to[0]) ** 2 + (self[1] - to[1]) ** 2

    def normalize(self):
        '''Returns a new vector that has the same direction as vec,
        but has a length of one.

        >>> v = Vector(88, 33).normalize()
        >>> v
        [0.93632917756904444, 0.3511234415883917]
        >>> v.length()
        1.0

        '''
        if self[0] == 0. and self[1] == 0.:
            return Vector(0., 0.)
        return self / self.length()

    def dot(self, a):
        '''Computes the dot product of a and b.

        >>> Vector(2, 4).dot((2, 2))
        12

        '''
        return self[0] * a[0] + self[1] * a[1]

    def angle(self, a):
        '''Computes the angle between a and b, and return the angle in
        degrees.

        >>> Vector(100, 0).angle((0, 100))
        -90.0
        >>> Vector(87, 23).angle((-77, 10))
        -157.7920283010705

        '''
        angle = -(180/math.pi) * math.atan2(
            self[0] * a[1] - self[1] * a[0],
            self[0] * a[0] + self[1] * a[1])
        return angle

    def rotate(self, angle):
        '''Rotate the vector with an angle in degrees.

        >>> v = Vector(100, 0)
        >>> v.rotate(45)
        >>> v
        [70.710678118654755, 70.710678118654741]

        '''
        angle = math.radians(angle)
        return Vector((self[0] * math.cos(angle)) - (self[1] * math.sin(angle)),
                      (self[1] * math.cos(angle)) + (self[0] * math.sin(angle)))

    @staticmethod
    def line_intersection(v1, v2, v3, v4):
        '''
        Finds the intersection point between the lines (1)v1->v2 and (2)v3->v4
        and returns it as a vector object.

        >>> a = (98, 28)
        >>> b = (72, 33)
        >>> c = (10, -5)
        >>> d = (20, 88)
        >>> Vector.line_intersection(a, b, c, d)
        [15.25931928687196, 43.911669367909241]

        .. warning::

            This is a line intersection method, not a segment intersection.

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
        '''Return a true if `point` is in bbox defined by `a` and `b`.

        >>> bmin = (0, 0)
        >>> bmax = (100, 100)
        >>> Vector.in_bbox((50, 50), bmin, bmax)
        True
        >>> Vector.in_bbox((647, -10), bmin, bmax)
        False

        '''
        return ((point[0] <= a[0] and point[0] >= b[0] or
                 point[0] <= b[0] and point[0] >= a[0]) and
                (point[1] <= a[1] and point[1] >= b[1] or
                 point[1] <= b[1] and point[1] >= a[1]))

