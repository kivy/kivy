'''
Gesture recognition
===================

You can easily use these class to create
new gesture, and compare them::

    from kivy.gesture import Gesture, GestureDatabase

    # Create a gesture
    g = Gesture()
    g.add_stroke(point_list=[(1,1), (3,4), (2,1)])
    g.normalize()

    # Add him to database
    gdb = GestureDatabase()
    gdb.add_gesture(g)

    # And for the next gesture, try to find him !
    g2 = Gesture()
    # ...
    gdb.find(g2)

'''

__all__ = ('Gesture', 'GestureDatabase', 'GesturePoint', 'GestureStroke')

import pickle
import base64
import zlib
import math
from cStringIO import StringIO

from kivy.vector import Vector


class GestureDatabase(object):
    '''Class to handle a gesture database.'''

    def __init__(self):
        self.db = []

    def add_gesture(self, gesture):
        '''Add a new gesture in database'''
        self.db.append(gesture)

    def find(self, gesture, minscore=0.9, rotation_invariant=True):
        '''Find current gesture in database'''
        if not gesture:
            return

        best = None
        bestscore = minscore
        for g in self.db:
            score = g.get_score(gesture, rotation_invariant)
            if score < bestscore:
                continue
            bestscore = score
            best = g
        if not best:
            return
        return (bestscore, best)

    def gesture_to_str(self, gesture):
        '''Convert a gesture into a unique string'''
        io = StringIO()
        p = pickle.Pickler(io)
        p.dump(gesture)
        data = base64.b64encode(zlib.compress(io.getvalue(), 9))
        return data

    def str_to_gesture(self, data):
        '''Convert a unique string to a gesture'''
        io = StringIO(zlib.decompress(base64.b64decode(data)))
        p = pickle.Unpickler(io)
        gesture = p.load()
        return gesture


class GesturePoint:

    def __init__(self, x, y):
        '''Stores the x,y coordinates of a point in the gesture'''
        self.x = float(x)
        self.y = float(y)

    def scale(self, factor):
        ''' Scales the point by the given factor '''
        self.x *= factor
        self.y *= factor
        return self

    def __repr__(self):
        return 'Mouse_point: %f,%f' % (self.x, self.y)


class GestureStroke:
    ''' Gestures can be made up of multiple strokes '''

    def __init__(self):
        ''' A stroke in the gesture '''
        self.points = list()
        self.screenpoints = list()

    # These return the min and max coordinates of the stroke
    @property
    def max_x(self):
        if len(self.points) == 0:
            return 0
        return max(self.points, key = lambda pt: pt.x).x

    @property
    def min_x(self):
        if len(self.points) == 0:
            return 0
        return min(self.points, key = lambda pt: pt.x).x

    @property
    def max_y(self):
        if len(self.points) == 0:
            return 0
        return max(self.points, key = lambda pt: pt.y).y

    @property
    def min_y(self):
        if len(self.points) == 0:
            return 0
        return min(self.points, key = lambda pt: pt.y).y

    def add_point(self, x, y):
        '''
        add_point(x=x_pos, y=y_pos)
        Adds a point to the stroke
        '''
        self.points.append(GesturePoint(x, y))
        self.screenpoints.append((x, y))

    def scale_stroke(self, scale_factor):
        '''
        scale_stroke(scale_factor=float)
        Scales the stroke down by scale_factor
        '''
        self.points = map(lambda pt: pt.scale(scale_factor), self.points)

    def points_distance(self, point1, point2):
        '''
        points_distance(point1=GesturePoint, point2=GesturePoint)
        Returns the distance between two GesturePoint
        '''
        x = point1.x - point2.x
        y = point1.y - point2.y
        return math.sqrt(x*x + y*y)

    def stroke_length(self, point_list=None):
        '''Finds the length of the stroke. If a point list is given,
           finds the length of that list.
        '''
        if point_list is None:
            point_list = self.points
        gesture_length = 0.0
        if len(point_list) <= 1: # If there is only one point -> no length
            return gesture_length
        for i in xrange(len(point_list)-1):
            gesture_length += self.points_distance(
                point_list[i], point_list[i+1])
        return gesture_length

    def normalize_stroke(self, sample_points = 32):
        '''Normalizes strokes so that every stroke has a standard number of
           points. Returns True if stroke is normalized, False if it can't be
           normalized. sample_points control the resolution of the stroke.
        '''
        # If there is only one point or the length is 0, don't normalize
        if len(self.points) <= 1 or self.stroke_length(self.points) == 0.0:
            return False

        # Calculate how long each point should be in the stroke
        target_stroke_size = self.stroke_length(self.points) / \
                             float(sample_points)
        new_points = list()
        new_points.append(self.points[0])

        # We loop on the points
        prev = self.points[0]
        src_distance = 0.0
        dst_distance = target_stroke_size
        for curr in self.points[1:]:
            d = self.points_distance(prev, curr)
            if d > 0:
                prev = curr
                src_distance = src_distance+d

                # The new point need to be inserted into the
                # segment [prev, curr]
                while dst_distance < src_distance:
                    x_dir = curr.x - prev.x
                    y_dir = curr.y - prev.y
                    ratio = (src_distance-dst_distance)/d
                    to_x = x_dir * ratio + prev.x
                    to_y = y_dir * ratio + prev.y
                    new_points.append(GesturePoint(to_x, to_y))
                    dst_distance = self.stroke_length(self.points) / \
                            float(sample_points) * len(new_points)

        # If this happens, we are into troubles...
        if not len(new_points) == sample_points:
            raise ValueError('Invalid number of strokes points; got '
                             '%d while it should be %d' %
                             (len(new_points), sample_points))

        self.points = new_points
        return True

    def center_stroke(self, offset_x, offset_y):
        '''Centers the stroke by offseting the points'''
        for point in self.points:
            point.x -= offset_x
            point.y -= offset_y


class Gesture:
    '''A python implementation of a gesture recognition algorithm by
    Oleg Dopertchouk: http://www.gamedev.net/reference/articles/article2039.asp

    Implemented by Jeiel Aranal (chemikhazi@gmail.com),
    released into the public domain.
    '''

    # Tolerance for evaluation using the '==' operator
    DEFAULT_TOLERANCE = 0.1

    def __init__(self, tolerance=None):
        '''
        Gesture([tolerance=float])
        Creates a new gesture with an optional matching tolerance value
        '''
        self.width = 0.
        self.height = 0.
        self.gesture_product = 0.
        self.strokes = list()
        if tolerance is None:
            self.tolerance = Gesture.DEFAULT_TOLERANCE
        else:
            self.tolerance = tolerance

    def _scale_gesture(self):
        ''' Scales down the gesture to a unit of 1 '''
        # map() creates a list of min/max coordinates of the strokes
        # in the gesture and min()/max() pulls the lowest/highest value
        min_x = min(map(lambda stroke: stroke.min_x, self.strokes))
        max_x = max(map(lambda stroke: stroke.max_x, self.strokes))
        min_y = min(map(lambda stroke: stroke.min_y, self.strokes))
        max_y = max(map(lambda stroke: stroke.max_y, self.strokes))
        x_len = max_x - min_x
        self.width = x_len
        y_len = max_y - min_y
        self.height = y_len
        scale_factor = max(x_len, y_len)
        if scale_factor <= 0.0:
            return False
        scale_factor = 1.0 / scale_factor
        for stroke in self.strokes:
            stroke.scale_stroke(scale_factor)
        return True

    def _center_gesture(self):
        ''' Centers the Gesture,Point of the gesture '''
        total_x = 0.0
        total_y = 0.0
        total_points = 0

        for stroke in self.strokes:
            # adds up all the points inside the stroke
            stroke_y = sum([pt.y for pt in stroke.points])
            stroke_x = sum([pt.x for pt in stroke.points])
            total_y += stroke_y
            total_x += stroke_x
            total_points += len(stroke.points)
        if total_points == 0:
            return False
        # Average to get the offset
        total_x /= total_points
        total_y /= total_points
        # Apply the offset to the strokes
        for stroke in self.strokes:
            stroke.center_stroke(total_x, total_y)
        return True

    def add_stroke(self, point_list=None):
        '''Adds a stroke to the gesture and returns the Stroke instance.
           Optional point_list argument is a list of the mouse points for
           the stroke.
        '''
        self.strokes.append(GestureStroke())
        if isinstance(point_list, list) or isinstance(point_list, tuple):
            for point in point_list:
                if isinstance(point, GesturePoint):
                    self.strokes[-1].points.append(point)
                elif isinstance(point, list) or isinstance(point, tuple):
                    if len(point) != 2:
                        raise ValueError("Stroke entry must have 2 values max")
                    self.strokes[-1].add_point(point[0], point[1])
                else:
                    raise TypeError("The point list should either be " + \
                        " tuples of x and y or a list of GesturePoint objects")
        elif point_list is not None:
            raise ValueError("point_list should be a tuple/list")
        return self.strokes[-1]

    def normalize(self, stroke_samples=32):
        '''Runs the gesture normalization algorithm and calculates the dot
           product with self
        '''
        if not self._scale_gesture() or not self._center_gesture():
            self.gesture_product = False
            return False
        for stroke in self.strokes:
            stroke.normalize_stroke(stroke_samples)
        self.gesture_product = self.dot_product(self)

    def get_rigid_rotation(self, dstpts):
        '''
        Extract the rotation to apply to a group of points to minimize the
        distance to a second group of points. The two groups of points are
        assumed to be centered. This is a simple version that just pick
        an angle based on the first point of the gesture.
        '''
        if len(self.strokes) < 1 or len(self.strokes[0].points) < 1:
            return 0
        if len(dstpts.strokes) < 1 or len(dstpts.strokes[0].points) < 1:
            return 0
        p = dstpts.strokes[0].points[0]
        target = Vector([p.x, p.y])
        source = Vector([p.x, p.y])
        return source.angle(target)

    def dot_product(self, comparison_gesture):
        ''' Calculates the dot product of the gesture with another gesture '''
        if len(comparison_gesture.strokes) != len(self.strokes):
            return -1
        if getattr(comparison_gesture, 'gesture_product', True) is False or \
           getattr(self, 'gesture_product', True) is False:
            return -1
        dot_product = 0.0
        for stroke_index, (my_stroke, cmp_stroke) in enumerate(
                zip(self.strokes, comparison_gesture.strokes)):
            for pt_index, (my_point, cmp_point) in enumerate(
                    zip(my_stroke.points, cmp_stroke.points)):
                dot_product += my_point.x * cmp_point.x +\
                               my_point.y * cmp_point.y
        return dot_product

    def rotate(self, angle):
        g = Gesture()
        for stroke in self.strokes:
            tmp = []
            for j in stroke.points:
                v = Vector([j.x, j.y]).rotate(angle)
                tmp.append(v)
            g.add_stroke(tmp)
        g.gesture_product = g.dot_product(g)
        return g

    def get_score(self, comparison_gesture, rotation_invariant=True):
        ''' Returns the matching score of the gesture against another gesture
        '''
        if isinstance(comparison_gesture, Gesture):
            if rotation_invariant:
                # get orientation
                angle = self.get_rigid_rotation(comparison_gesture)

                # rotate the gesture to be in the same frame.
                comparison_gesture = comparison_gesture.rotate(angle)

            # this is the normal "orientation" code.
            score = self.dot_product(comparison_gesture)
            if score <= 0:
                return score
            score /= math.sqrt(
                    self.gesture_product * comparison_gesture.gesture_product)
            return score

    def __eq__(self, comparison_gesture):
        ''' Allows easy comparisons between gesture instances '''
        if isinstance(comparison_gesture, Gesture):
            # If the gestures don't have the same number of strokes, its
            # definitely not the same gesture
            score = self.get_score(comparison_gesture)
            if (score > (1.0 - self.tolerance) and
                score < (1.0 + self.tolerance)):
                return True
            else:
                return False
        else:
            return NotImplemented

    def __ne__(self, comparison_gesture):
        result = self.__eq__(comparison_gesture)
        if result is NotImplemented:
            return result
        else:
            return not result

    def __lt__(self, comparison_gesture):
        raise TypeError("Gesture cannot be evaluated with <")

    def __gt__(self, comparison_gesture):
        raise TypeError("Gesture cannot be evaluated with >")

    def __le__(self, comparison_gesture):
        raise TypeError("Gesture cannot be evaluated with <=")

    def __ge__(self, comparison_gesture):
        raise TypeError("Gesture cannot be evaluated with >=")

