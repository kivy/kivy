'''
Motion Event Shape
==================

Represent the shape of the :class:`~kivy.input.motionevent.MotionEvent`
'''

__all__ = ('Shape', 'ShapeRect')


class Shape(object):
    '''Abstract class for all implementations of a shape'''
    pass


class ShapeRect(Shape):
    '''Class for the representation of a rectangle.'''
    __slots__ = ('width', 'height')

    def __init__(self):
        super(ShapeRect, self).__init__()

        #: Width of the rect
        self.width = 0

        #: Height of the rect
        self.height = 0
