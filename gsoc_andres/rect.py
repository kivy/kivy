class Rect:
    '''
    Rect
    ===================
    
    A rectangle implementation for getting bounds of objects::
        
        # Create a Rectangle
        pointA = Point(2,3)
        pointB = Point(4,5)
        rect = Rectangle(pointA, pointB)        
        distance = pointA.distance_to(pointB)
    '''
    
    def __init__(self, p1, p2):
        ''' Initialize a Rectangle by using two points'''
        self.pt1 = p1
        self.pt2 = p2