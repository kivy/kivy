class Rect:
    '''
    Rect
    ===================
    
    A rectangle implementation for getting bounds of objects::
        
        # Create a Rect
        pointA = Point(2,3)
        pointB = Point(4,5)
        rect = Rect(pointA, pointB)
    '''
    
    def __init__(self, p1, p2):
        ''' Initialize a Rectangle by using two points'''
        self.pt1 = p1.to_float()
        self.pt2 = p2.to_float()
        self.left = min(self.pt1.X, self.pt2.X)
        self.top = max(self.pt1.Y, self.pt2.Y)
        self.right = max(self.pt1.X, self.pt2.X)
        self.bottom = min(self.pt1.Y, self.pt2.Y)
        self.width = self.right - self.left
        self.height = self.top - self.bottom

    def contains(self, p):
        ''' Returns whether or not a point is inside the rectangle '''
        return (self.left <= p.X <= self.right and self.top <= p.Y <= self.bottom)