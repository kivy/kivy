class Point:
    '''Default Constructor'''
    def __init__(self, x, y):
        self.X = x
        self.Y = y
    
    def __eq__(self, other):
        '''Override default Equals behaviour'''
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False
    
    def __ne__(self, other):
        '''Define a non equality test'''
        return not self.__eq__(other)
    
    def __add__(self, p):
        '''Sum two points'''
        return Point(self.X + p.X, self.Y + p.Y)
    
    def __sub__(self, p):
        '''Substract two points'''
        return Point(self.X - p.X, self.Y - p.Y)
    
    def __mul__(self, scalar):
        '''Multiply a point to a scalar'''
        return Point(self.X*scalar, self.Y*scalar)
    
    def __div__(self, scalar):
        '''Divide a point to a scalar'''
        return Point(self.X/scalar, self.Y/scalar)
    
    def __str__(self):
        '''String representation'''
        return "(%s, %s)" % (self.X, self.Y)
    
    def __repr__(self):
        '''print Point'''
        return "%s(%r, %r)" % (self.__class__.__name__, self.X, self.Y)
    
    def clone(self):
        '''Return a copy of this point'''
        return Point(self.X, self.Y)