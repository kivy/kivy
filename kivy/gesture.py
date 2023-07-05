'''
Gesture recognition
===================

This class allows you to easily create new
gestures and compare them::

    from kivy.gesture import Gesture, GestureDatabase

    # Create a gesture
    g = Gesture()
    g.add_stroke(point_list=[(1,1), (3,4), (2,1)])
    g.normalize()

    # Add it to the database
    gdb = GestureDatabase()
    gdb.add_gesture(g)

    # And for the next gesture, try to find it!
    g2 = Gesture()
    # ...
    gdb.find(g2)

And now a more elaborate example that captures gestures from touch events
and emits events when the gesture is recognized::

    from kivy.gesture import Gesture, GestureDatabase
    from kivy.event import EventDispatcher

    class MyScreenManager(ScreenManager, EventDispatcher):
        _strokes = {
            # straight lines
            'right': 13,
            'left': 31,
            'down': 14,
            'up': 41,
            # triangles
            '3down': 7297,
            '3up': 1381,
            '3left': 1671,
            '3right': 3943,
            # squares
            'box-1': 13971,
            'box-3': 39713,
            'box-9': 97139,
            'box-7': 71397,
            'box-1-ccw': 17931,
            'box-3-ccw': 31793,
            'box-9-ccw': 93179,
            'box-7-ccw': 79317,
            # characters
            'V': 183,
            'V-inv': 729,
            'W': 17593,
            'M': 71539,
            'N': 7193,
            'Sigma': 31579
        }

        def __init__(self, **kwargs):
            self._gestureDb = GestureDatabase()
            for name, points in self._strokes.items():
                self._gestureDb.add_gesture(Gesture(name=name, \
point_list=points))
            self.register_event_type('on_gesture')
            super(MyScreenManager, self).__init__(**kwargs)

        def on_touch_down(self, touch):
            touch.ud['line'] = list()
            touch.ud['line'].append(touch.pos)
            return ScreenManager.on_touch_down(self, touch)

        def on_touch_move(self, touch):
            touch.ud['line'].append(touch.pos)
            return ScreenManager.on_touch_move(self, touch)

        def on_touch_up(self, touch):
            touch.ud['line'].append(touch.pos)
            stroke = self._gestureDb.find(Gesture(point_list = \
touch.ud['line']), 0.5, False)
            if stroke is not None:
                self.dispatch('on_gesture', stroke[1].name)
            ScreenManager.on_touch_up(self, touch)

        def on_gesture(self, *args):
            print('Gesture dispatched: {}'.format(args[0]))

    class MyApp(App):
        # ...
        # ...

.. note:: :meth:`~kivy.gesture.Gesture.normalize()` resizes and moves a stroke \
so that all points always fit in a box limited by (1, 1) and (-1, -1). \
As a consequence, after normalization ((1, 1), (-1, -1)) and \
((100, 100), (-100, -100)) represent the same strokes. \
Similarly ((1, 1), (1, 0)) and ((0, 1), (0, 0)) represent the same.

.. versionadded:: 2.3.0
:meth:`~kivy.gesture.Gesture.add_stroke` implements a shorthand to encode
strokes. This shorthand mimics a keypad from a phone: top-left is called '1',
top-center is '2', top-right is '3', ... bottom-right is '9'.
When encoding strokes, you can specify '123' or 123 for a three-point horizontal
stroke. '147' specifies a vertical stroke, '159' specifies a diagonal stroke.

'''

__all__ = ('Gesture', 'GestureDatabase', 'GesturePoint', 'GestureStroke')

import pickle
import base64
import zlib
import math

from kivy.vector import Vector

from io import BytesIO


def sqr(x):
    return x * x


class GestureDatabase(object):
    '''Class to handle a gesture database.'''

    def __init__(self):
        self.db = []

    def add_gesture(self, gesture):
        '''Add a new gesture to the database.'''
        self.db.append(gesture)

    def find(self, gesture, minscore=0.9, rotation_invariant=True):
        '''Find a matching gesture in the database.'''
        if not gesture.gesture_product:
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
        '''Convert a gesture into a unique string.'''
        io = BytesIO()
        p = pickle.Pickler(io)
        p.dump(gesture)
        data = base64.b64encode(zlib.compress(io.getvalue(), 9))
        return data

    def str_to_gesture(self, data):
        '''Convert a unique string to a gesture.'''
        io = BytesIO(zlib.decompress(base64.b64decode(data)))
        p = pickle.Unpickler(io)
        gesture = p.load()
        return gesture


class GesturePoint:

    def __init__(self, x, y):
        '''Stores the x,y coordinates of a point in the gesture.'''
        self.x = float(x)
        self.y = float(y)

    def scale(self, factor):
        ''' Scales the point by the given factor.'''
        self.x *= factor
        self.y *= factor
        return self

    def __repr__(self):
        return 'Mouse_point: %f,%f' % (self.x, self.y)


class GestureStroke:
    ''' Gestures can be made up of multiple strokes.'''

    def __init__(self):
        ''' A stroke in the gesture.'''
        self.points = list()
        self.screenpoints = list()

    # These return the min and max coordinates of the stroke
    @property
    def max_x(self):
        if len(self.points) == 0:
            return 0
        return max(self.points, key=lambda pt: pt.x).x

    @property
    def min_x(self):
        if len(self.points) == 0:
            return 0
        return min(self.points, key=lambda pt: pt.x).x

    @property
    def max_y(self):
        if len(self.points) == 0:
            return 0
        return max(self.points, key=lambda pt: pt.y).y

    @property
    def min_y(self):
        if len(self.points) == 0:
            return 0
        return min(self.points, key=lambda pt: pt.y).y

    def add_point(self, x, y):
        '''
        add_point(x=x_pos, y=y_pos)
        Adds a point to the stroke.
        '''
        self.points.append(GesturePoint(x, y))
        self.screenpoints.append((x, y))

    def scale_stroke(self, scale_factor):
        '''
        scale_stroke(scale_factor=float)
        Scales the stroke down by scale_factor.
        '''
        self.points = [pt.scale(scale_factor) for pt in self.points]

    def points_distance(self, point1, point2):
        '''
        points_distance(point1=GesturePoint, point2=GesturePoint)
        Returns the distance between two GesturePoints.
        '''
        x = point1.x - point2.x
        y = point1.y - point2.y
        return math.sqrt(x * x + y * y)

    def stroke_length(self, point_list=None):
        '''Finds the length of the stroke. If a point list is given,
           finds the length of that list.
        '''
        if point_list is None:
            point_list = self.points
        gesture_length = 0.0
        if len(point_list) <= 1:  # If there is only one point -> no length
            return gesture_length
        for i in range(len(point_list) - 1):
            gesture_length += self.points_distance(
                point_list[i], point_list[i + 1])
        return gesture_length

    def normalize_stroke(self, sample_points=32):
        '''Normalizes strokes so that every stroke has a standard number of
           points. Returns True if stroke is normalized, False if it can't be
           normalized. sample_points controls the resolution of the stroke.
        '''
        # If there is only one point or the length is 0, don't normalize
        if len(self.points) <= 1 or self.stroke_length(self.points) == 0.0:
            return False

        # Calculate how long each point should be in the stroke
        stepsize = \
            self.stroke_length(self.points) / float(sample_points - 1)

        new_points = list()

        # Copy the starting point as the first new point
        here = self.points[0]
        new_points.append(here)
        leg_index = 1
        next = self.points[leg_index]
        leg_size = self.points_distance(here, next)
        step = stepsize

        while True:
            if step < leg_size:
                x_dir = next.x - here.x
                y_dir = next.y - here.y
                ratio = step / self.points_distance(here, next)
                to_x = x_dir * ratio + here.x
                to_y = y_dir * ratio + here.y
                here = GesturePoint(to_x, to_y)
                new_points.append(here)
                leg_size -= step
                step = stepsize
            else:
                step -= leg_size
                leg_index += 1
                if leg_index == len(self.points):
                    break
                here = next
                next = self.points[leg_index]
                leg_size = self.points_distance(here, next)

        if len(new_points) < sample_points:
            new_points.append(next)

        self.points = new_points
        return True

    def center_stroke(self, offset_x, offset_y):
        '''Centers the stroke by offsetting the points.'''
        for point in self.points:
            point.x -= offset_x
            point.y -= offset_y


class Gesture:
    '''Creates a new gesture with an optional matching `tolerance` value.
    In case `name` is specified, the Gesture will create an atttribute with
    that name. In case `point_list` is specified, a stroke will be created
    from this point list and will be added to the Gesture. This stroke will
    be normalized.

    A python implementation of a gesture recognition algorithm by
    Oleg Dopertchouk: http://www.gamedev.net/reference/articles/article2039.asp

    Implemented by Jeiel Aranal (chemikhazi@gmail.com),
    released into the public domain.

    .. versionadded:: 2.3.0
    The :meth:`~kivy.gesture.Gesture.__init__()` method was extended with the
    `name` and the `point_list` parameters. When supplied, the stroke in
    `point_list` will be normalized.
    '''

    # Tolerance for evaluation using the '==' operator
    DEFAULT_TOLERANCE = 0.1

    def __init__(self, tolerance=None, name=None, point_list=None):
        '''
        Gesture([tolerance=float], name=None, point_list=None)
        '''
        self.width = 0.
        self.height = 0.
        self.gesture_product = 0.
        self.strokes = list()
        if tolerance is None:
            self.tolerance = Gesture.DEFAULT_TOLERANCE
        else:
            self.tolerance = tolerance

        if name is not None:
            self.name = name
        if point_list is not None:
            self.add_stroke(point_list=point_list)
            self.normalize()

    def _scale_gesture(self):
        ''' Scales down the gesture to a unit of 1.'''
        # map() creates a list of min/max coordinates of the strokes
        # in the gesture and min()/max() pulls the lowest/highest value
        min_x = min([stroke.min_x for stroke in self.strokes])
        max_x = max([stroke.max_x for stroke in self.strokes])
        min_y = min([stroke.min_y for stroke in self.strokes])
        max_y = max([stroke.max_y for stroke in self.strokes])
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
        ''' Centers the Gesture.points of the gesture.'''
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

    ''' Define shorthand for gesture reference points as if it were a keypad
        of a phone. Assume a 3 x 3 grid, labeled '1', '2', '3' etc
    '''
    _keypad = {'1': (-1, 1), '2': (0, 1), '3': (1, 1),
       '4': (-1, 0), '5': (0, 0), '6': (1, 0),
       '7': (-1, -1), '8': (0, -1), '9': (1, -1)
    }

    def add_stroke(self, point_list=None):
        '''Adds a stroke to the gesture and returns the Stroke instance.
           Optional `point_list` argument is a list of the mouse points for
           the stroke. `point_list` can be a list of points, a string with
           characters 1...9 or an integer.
        '''
        if isinstance(point_list, int):
            point_list = str(point_list)
        if isinstance(point_list, str):
            point_list = list(map(lambda x: self._keypad[x], str(point_list)))

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
                    raise TypeError("The point list should either be "
                                    "tuples of x and y or a list of "
                                    "GesturePoint objects")
        elif point_list is not None:
            raise ValueError("point_list should be a tuple/list")
        return self.strokes[-1]

    def normalize(self, stroke_samples=32):
        '''Runs the gesture normalization algorithm and calculates the dot
        product with self.
        '''
        if not self._scale_gesture():
            self.gesture_product = False
            return False
        for stroke in self.strokes:
            stroke.normalize_stroke(stroke_samples)
        self._center_gesture()
        self.gesture_product = self.dot_product(self)

    def get_rigid_rotation(self, dstpts):
        '''
        Extract the rotation to apply to a group of points to minimize the
        distance to a second group of points. The two groups of points are
        assumed to be centered. This is a simple version that just picks
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
        ''' Calculates the dot product of the gesture with another gesture.'''
        if len(comparison_gesture.strokes) != len(self.strokes):
            return -1
        if getattr(comparison_gesture, 'gesture_product', True) is False or \
           getattr(self, 'gesture_product', True) is False:
            return -1
        dot_product = 0.0
        for stroke_index, (my_stroke, cmp_stroke) in enumerate(
                list(zip(self.strokes, comparison_gesture.strokes))):
            for pt_index, (my_point, cmp_point) in enumerate(
                    list(zip(my_stroke.points, cmp_stroke.points))):
                dot_product += (my_point.x * cmp_point.x +
                                my_point.y * cmp_point.y)
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
        ''' Returns the matching score of the gesture against another gesture.
        '''
        if len(comparison_gesture.strokes) != len(self.strokes):
            raise Exception('Gestures not the same size. Try normalization.')

        if isinstance(comparison_gesture, Gesture):
            if rotation_invariant:
                # get orientation
                angle = self.get_rigid_rotation(comparison_gesture)

                # rotate the gesture to be in the same frame.
                comparison_gesture = comparison_gesture.rotate(angle)

            # this is the normal "orientation" code.
            score = 0.0
            for i in range(len(comparison_gesture.strokes)):
                if len(comparison_gesture.strokes[i].points) != \
                    len(self.strokes[i].points):
                    raise Exception('Strokes not the same size')
                for j in range(len(comparison_gesture.strokes[i].points)):
                    score += sqr(comparison_gesture.strokes[i].points[j].x -
                                  self.strokes[i].points[j].x)
                    score += sqr(comparison_gesture.strokes[i].points[j].y -
                                  self.strokes[i].points[j].y)
            return 1.0 - score

    def __eq__(self, comparison_gesture):
        ''' Allows easy comparisons between gesture instances.'''
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
