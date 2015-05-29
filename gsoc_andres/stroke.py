from kivy.properties import (NumericProperty, ListProperty, BooleanProperty, DictProperty)

class Stroke:
    
    '''Default Constructor'''
    def __init__(self, list_points=[]):
        self.points = list_points
        self.color = ListProperty([1.,1.,1.])
        self.point_size = 1
    
    def __eq__(self, other):
        '''Override default Equals behaviour'''
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False
    
    def __ne__(self, other):
        '''Define a non equality test'''
        return not self.__eq__(other)