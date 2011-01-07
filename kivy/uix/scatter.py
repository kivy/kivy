'''
Scatter
=======

.. todo::

    - Fix center_x / center_y attributes
    - Ensure top and right are good

'''

__all__ = ('Scatter', )

from math import radians
from kivy.properties import BooleanProperty, AliasProperty, \
        NumericProperty, ObjectProperty
from kivy.vector import Vector
from kivy.uix.widget import Widget
from kivy.graphics.transformation import matrix_multiply, matrix_identity, \
        matrix_translation, matrix_rotation, matrix_scale, matrix_inverse, \
        matrix_transform_point

class Scatter(Widget):
    '''Scatter implementation as a Widget.
    '''

    do_translation_x = BooleanProperty(True)
    '''Allow translation on X axis

    :data:`do_translation_x` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''

    do_translation_y = BooleanProperty(True)
    '''Allow translation on Y axis

    :data:`do_translation_y` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''

    def _get_do_translation(self):
        return (self.do_translation_x, self.do_translation_y)
    def _set_do_translation(self, value):
        if type(value) in (list, tuple):
            self.do_translation_x, self.do_translation_y = value
        else:
            self.do_translation_x = self.do_translation_y = bool(value)
    do_translation = AliasProperty(_get_do_translation, _set_do_translation,
                                   bind=('do_translation_x', 'do_translation_y'))
    '''Allow translation on X or Y axis

    :data:`do_translation` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`do_translation_x` + :data:`do_translation_y`)
    '''


    do_rotation = BooleanProperty(True)
    '''Allow rotation

    :data:`do_rotation` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''

    do_scale = BooleanProperty(True)
    '''Allow scaling

    :data:`do_scale` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''

    scale_min = NumericProperty(0.01)
    '''Minimum scaling factor allowed

    :data:`scale_min` is a :class:`~kivy.properties.NumericProperty`, default to
    0.01
    '''

    scale_max = NumericProperty(1e20)
    '''Maximum scaling factor allowed

    :data:`scale_max` is a :class:`~kivy.properties.NumericProperty`, default to
    1e20
    '''

    transform = ObjectProperty(matrix_identity())
    '''Transformation matrix

    :data:`transform` is a :class:`~kivy.properties.ObjectProperty`, default to
    the identity matrix.
    '''

    transform_inv = ObjectProperty(matrix_identity())
    '''Inverse of the transformation matrix

    :data:`transform_inv` is a :class:`~kivy.properties.ObjectProperty`, default
    to the identity matrix.
    '''

    def _get_bbox(self):
        xmin, ymin = xmax, ymax = self.to_parent(0, 0)
        for point in [(self.width, 0), (0, self.height), self.size]:
            x, y = self.to_parent(*point)
            if x < xmin:
                xmin = x
            if y < ymin:
                ymin = y
            if x > xmax:
                xmax = x
            if y > ymax:
                ymax = y
        return (xmin, ymin), (xmax-xmin, ymax-ymin)
    bbox = AliasProperty(_get_bbox, None, bind=(
        'transform', 'width', 'height'))
    '''Bounding box of the widget in parent space ::

        ((x, y), (w, h))
        # x, y = lower left corner

    :data:`bbox` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_rotation(self):
        v1 = Vector(0, 10)
        v2 = Vector(*self.to_parent(*self.pos)) - self.to_parent(self.x, self.y + 10)
        return -1.0 *(v1.angle(v2) + 180) % 360
    def _set_rotation(self, rotation):
        angle_change = self.rotation - rotation
        r = matrix_rotation(-radians(angle_change), 0, 0, 1)
        self.apply_transform(r, post_multiply=True, anchor=self.to_local(*self.center))
    rotation = AliasProperty(_get_rotation, _set_rotation, bind=(
        'x', 'y', 'transform'))
    '''Rotation value of the scatter

    :data:`rotation` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_scale(self):
        p1 = Vector(*self.to_parent(0, 0))
        p2 = Vector(*self.to_parent(1, 0))
        scale = p1.distance(p2)
        return float(scale)
    def _set_scale(self, scale):
        rescale = scale * 1.0 / self.scale
        self.apply_transform(matrix_scale(rescale, rescale, rescale),
                             post_multiply=True, anchor=self.to_local(*self.center))
    scale = AliasProperty(_get_scale, _set_scale, bind=('x', 'y', 'transform'))
    '''Scale value of the scatter

    :data:`scale` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_center(self):
        return (self.bbox[0][0] + self.bbox[1][0]/2.0,
                self.bbox[0][1] + self.bbox[1][1]/2.0)
    def _set_center(self, center):
        if center == self.center:
            return False
        t = Vector(*center) - self.center
        trans = matrix_translation(t.x, t.y, 0)
        self.apply_transform(trans)
    center = AliasProperty(_get_center, _set_center, bind=('bbox', ))

    def _get_pos(self):
        return self.bbox[0]
    def _set_pos(self, pos):
        _pos = self.bbox[0]
        if pos == _pos:
            return
        t = Vector(*pos) - _pos
        trans = matrix_translation(t.x, t.y, 0)
        self.apply_transform(trans)
    pos = AliasProperty(_get_pos, _set_pos, bind=('bbox', ))

    def _get_x(self):
        return self.bbox[0][0]
    def _set_x(self, x):
        if x == self.bbox[0][0]:
            return False
        self.pos = (x, self.y)
        return True
    x = AliasProperty(_get_x, _set_x, bind=('bbox', ))

    def _get_y(self):
        return self.bbox[0][1]
    def _set_y(self, y):
        if y == self.bbox[0][1]:
            return False
        self.pos = (self.x, y)
        return True
    y = AliasProperty(_get_y, _set_y, bind=('bbox', ))

    def __init__(self, **kwargs):
        self._touches = []
        self._last_touch_pos = {}
        super(Scatter, self).__init__(**kwargs)

    def on_transform(self, instance, value):
        self.transform_inv = matrix_inverse(value)

    def collide_point(self, x, y):
        x, y = self.to_local(x, y)
        return 0 <= x <= self.width and 0 <= y <= self.height

    def to_parent(self, x, y, **k):
        p = matrix_transform_point(self.transform, x, y, 0)
        return (p[0], p[1])

    def to_local(self, x, y, **k):
        p = matrix_transform_point(self.transform_inv, x, y, 0)
        return (p[0], p[1])

    def apply_angle_scale_trans(self, angle, scale, trans, point=Vector(0, 0)):
        '''Update matrix transformation by adding new angle, scale and translate.

        :Parameters:
            `angle` : float
                Rotation angle to add
            `scale` : float
                Scaling value to add
            `trans` : Vector
                Vector translation to add
            `point` : Vector, default to (0, 0)
                Point to apply transformation
        '''
        old_scale = self.scale
        new_scale = old_scale * scale
        if new_scale < self.scale_min or old_scale > self.scale_max:
            scale = 1.

        t = matrix_translation(
            trans[0] * self.do_translation_x,
            trans[1] * self.do_translation_y,
            0
        )
        t = matrix_multiply(t, matrix_translation(point[0], point[1], 0))
        t = matrix_multiply(t, matrix_rotation(angle, 0, 0, 1))
        t = matrix_multiply(t, matrix_scale(scale, scale, scale))
        t = matrix_multiply(t, matrix_translation(-point[0], -point[1], 0))
        self.apply_transform(t)

    def apply_transform(self, trans, post_multiply=False, anchor=(0, 0)):
        '''
        Transforms scatter by trans (on top of its current transformation state)

        :Parameters:
            `trans`: transformation matrix from transformation lib.
                Transformation to be applied to the scatter widget
            `anchor`: tuple, default to (0, 0)
                The point to use as the origin of the transformation
                (uses local widget space)
            `post_multiply`: bool, default to False
                If true the transform matrix is post multiplied
                (as if applied before the current transform)
        '''
        t = matrix_translation(anchor[0], anchor[1], 0)
        t = matrix_multiply(t, trans)
        t = matrix_multiply(t, matrix_translation(-anchor[0], -anchor[1], 0))

        if post_multiply:
            self.transform = matrix_multiply(self.transform, t)
        else:
            self.transform = matrix_multiply(t, self.transform)

    def transform_with_touch(self, touch):
        # just do a simple one finger drag
        if len(self._touches) == 1:
            # _last_touch_pos has last pos in correct parent space, just liek incoming touch
            dx = (touch.x - self._last_touch_pos[touch][0]) * self.do_translation_x
            dy = (touch.y - self._last_touch_pos[touch][1]) * self.do_translation_y
            self.apply_transform(matrix_translation(dx, dy, 0))
            return

        # we have more than one touch...
        points = [Vector(*self._last_touch_pos[t]) for t in self._touches]

        # we only want to transform if the touch is part of the two touches
        # furthest apart! So first we find anchor, the point to transform
        # around as the touch farthest away from touch
        anchor  = max(points, key=lambda p: p.distance(touch.pos))

        # now we find the touch farthest away from anchor, if its not the
        # same as touch. Touch is not one of the two touches used to transform
        farthest = max(points, key=anchor.distance)
        if points.index(farthest) != self._touches.index(touch):
            return

        # ok, so we have touch, and anchor, so we can actually compute the
        # transformation        
        old_line = Vector(*touch.dpos) - anchor
        new_line = Vector(*touch.pos) - anchor

        angle = radians( new_line.angle(old_line) ) * self.do_rotation
        scale = new_line.length() / old_line.length()
        new_scale = scale * self.scale
        if new_scale < self.scale_min or new_scale > self.scale_max:
            scale = 1.0

        self.apply_transform(matrix_rotation(angle, 0, 0, 1), anchor=anchor)
        self.apply_transform(matrix_scale(scale, scale, scale), anchor=anchor)

    def on_touch_down(self, touch):
        x, y = touch.x, touch.y

        # if the touch isnt on the widget we do nothing
        if not self.collide_point(x, y):
            return False

        # let the child widgets handle the event if they want
        touch.push()
        touch.apply_transform_2d(self.to_local)
        if super(Scatter, self).on_touch_down(touch):
            touch.pop()
            return True
        touch.pop()

        # grab the touch so we get all it later move events for sure
        touch.grab(self)
        self._last_touch_pos[touch] = touch.pos
        self._touches.append(touch)

        return True

    def on_touch_move(self, touch):
        x, y = touch.x, touch.y
        # let the child widgets handle the event if they want
        if self.collide_point(x, y) and not touch.grab_current == self:
            touch.push()
            touch.apply_transform_2d(self.to_local)
            if super(Scatter, self).on_touch_move(touch):
                touch.pop()
                return True
            touch.pop()

        # rotate/scale/translate
        if touch in self._touches and touch.grab_current == self:
            self.transform_with_touch(touch)
            self._last_touch_pos[touch] = touch.pos

        # stop porpagating if its within our bounds
        if self.collide_point(x, y):
            return True

    def on_touch_up(self, touch):
        x, y = touch.x, touch.y
        # if the touch isnt on the widget we do nothing, just try children
        if not touch.grab_current == self:
            touch.push()
            touch.apply_transform_2d(self.to_local)
            if super(Scatter, self).on_touch_up(touch):
                touch.pop()
                return True
            touch.pop()

        # remove it from our saved touches
        if touch in self._touches and touch.grab_state:
            touch.ungrab(self)
            del self._last_touch_pos[touch]
            self._touches.remove(touch)

        # stop porpagating if its within our bounds
        if self.collide_point(x, y):
            return True

