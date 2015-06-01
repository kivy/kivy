from kivy.properties import (NumericProperty, ListProperty, BooleanProperty, DictProperty)

class Stroke:
    
    '''Default Constructor'''
    def __init__(self, list_points=[], group_id=""):
        self.points = list_points
        self.color = ListProperty([1.,1.,1.])
        self.point_size = 1
        self.group_id = group_id
    
    def __eq__(self, other):
        '''Override default Equals behaviour'''
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False
    
    def __ne__(self, other):
        '''Define a non equality test'''
        return not self.__eq__(other)
    
    def __str__(self):
        '''String representation'''
        cad = "["
        for point in self.points:
            cad += "(%s, %s)," % (point.X, point.Y)
        return cad[:-1] + "]"
    
    def __repr__(self):
        '''print Point'''
        cad = "<%s> [" % (self.__class__.__name__)
        for point in self.points:
            cad += "(%r, %r)," % (point.X, point.Y)
        return cad[:-1] + "]"