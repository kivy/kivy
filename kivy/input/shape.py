'''
Touch Shape: Represent the shape of the touch
'''

__all__ = ('TouchShape', 'TouchShapeRect')

class TouchShape(object):
    '''Abstract class for all implementation of a shape'''
    pass

class TouchShapeRect(TouchShape):
    '''Represent a rectangle shape.'''
    __slots__ = ['width', 'height']

    def __init__(self):
        super(TouchShapeRect, self).__init__()
        self.width = 0
        self.height = 0

