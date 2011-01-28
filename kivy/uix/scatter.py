'''
Scatter
=======

Scatter is a widget that you can translate, rotate and scale, with two or more
fingers. This is the famous widget as you can see on many multitouch demo.

Usage
-----

By default, the widget itself don't have any graphical representation. The idea
is to combine Scatter widget with other widget, like
:class:`~kivy.uix.image.Image` widget.

    scatter = Scatter()
    image = Image(source='sun.jpg')
    scatter.add_widget(image)

Control interactions
--------------------

You can also avoid some interaction, like rotation. ::

    scatter = Scatter(do_rotation=False)

Or allow only translation. ::

    scatter = Scatter(do_rotation=False, do_scale=False)

Automatic bring to front
------------------------

If you add and manipulate multiple scatter, you can have trouble if the scatter
is behind another scatter. We have a property named
:data:`Scatter.auto_bring_to_front` that remove and re-add the scatter in his
parent. The scatter will be on top as soon as you touch it.

Scale limitation
----------------

We are using 32 bits matrix, in double representation. That's mean, we have
limitation for scaling. You cannot do infite scale down/up with our
implementation. Generally, you don't hit the minimum scale (because you don't
see it on the screen), but the maximum scale : 9.99506983235e+19 (2^66)

You can also limit the minimum and maximum zoom allowed. ::

    scatter = Scatter(scale_min=.5, scale_max=3.)

'''

__all__ = ('Scatter', 'ScatterPlane')

from math import radians
from kivy.properties import BooleanProperty, AliasProperty, \
        NumericProperty, ObjectProperty
from kivy.vector import Vector
from kivy.uix.widget import Widget
from kivy.graphics.transformation import Matrix


class Scatter(Widget):
    '''Scatter class. See module documentation for more information.
    '''

    auto_bring_to_front = BooleanProperty(True)
    '''If True, the widget will be automatically pushed on the top of parent
    widget list for drawing.

    :data:`auto_bring_to_front` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
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

    transform = ObjectProperty(Matrix())
    '''Transformation matrix

    :data:`transform` is a :class:`~kivy.properties.ObjectProperty`, default to
    the identity matrix.
    '''

    transform_inv = ObjectProperty(Matrix())
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
        tp = self.to_parent
        v2 = Vector(*tp(*self.pos)) - tp(self.x, self.y + 10)
        return -1.0 *(v1.angle(v2) + 180) % 360

    def _set_rotation(self, rotation):
        angle_change = self.rotation - rotation
        r = Matrix().rotate(-radians(angle_change), 0, 0, 1)
        self.apply_transform(r, post_multiply=True,
                            anchor=self.to_local(*self.center))
    rotation = AliasProperty(_get_rotation, _set_rotation, bind=(
        'x', 'y', 'transform'))
    '''Rotation value of the scatter

    :data:`rotation` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_scale(self):
        p1 = Vector(*self.to_parent(0, 0))
        p2 = Vector(*self.to_parent(1, 0))
        scale = p1.distance(p2)
        print 'scale', scale
        return float(scale)

    def _set_scale(self, scale):
        rescale = scale * 1.0 / self.scale
        self.apply_transform(Matrix().scale(rescale, rescale, rescale),
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
        trans = Matrix().translate(t.x, t.y, 0)
        self.apply_transform(trans)
    center = AliasProperty(_get_center, _set_center, bind=('bbox', ))

    def _get_pos(self):
        return self.bbox[0]

    def _set_pos(self, pos):
        _pos = self.bbox[0]
        if pos == _pos:
            return
        t = Vector(*pos) - _pos
        trans = Matrix().translate(t.x, t.y, 0)
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
        super(Scatter, self).__init__(**kwargs)

    def on_transform(self, instance, value):
        self.transform_inv = value.inverse()

    def collide_point(self, x, y):
        x, y = self.to_local(x, y)
        return 0 <= x <= self.width and 0 <= y <= self.height

    def to_parent(self, x, y, **k):
        p = self.transform.transform_point(x, y, 0)
        return (p[0], p[1])

    def to_local(self, x, y, **k):
        p = self.transform_inv.transform_point(x, y, 0)
        return (p[0], p[1])

    def apply_angle_scale_trans(self, angle, scale, trans, point=Vector(0, 0)):
        '''Update matrix transformation by adding new angle,
           scale and translate.

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

        t = Matrix().translate(
            trans[0] * self.do_translation_x,
            trans[1] * self.do_translation_y,
            0)
        t = t.multiply(Matrix().translate(point[0], point[1], 0))
        t = t.multiply(Matrix().rotate(angle, 0, 0, 1))
        t = t.multiply(Matrix().scale(scale, scale, scale))
        t = t.multiply(Matrix().translate(-point[0], -point[1], 0))
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
        t = Matrix().translate(anchor[0], anchor[1], 0)
        t = t.multiply(trans)
        t = t.multiply(Matrix().translate(-anchor[0], -anchor[1], 0))

        if post_multiply:
            self.transform = self.transform.multiply(t)
        else:
            self.transform = t.multiply(self.transform)

    def transform_with_touch(self, touch):
        # just do a simple one finger drag
        if len(self._touches) == 1:
            # _last_touch_pos has last pos in correct parent space,
            # just liek incoming touch
            dx = touch.dx * self.do_translation_x
            dy = touch.dy * self.do_translation_y
            self.apply_transform(Matrix().translate(dx, dy, 0))
            return

        # we have more than one touch...
        points = [Vector(t.px, t.py) for t in self._touches]

        # we only want to transform if the touch is part of the two touches
        # furthest apart! So first we find anchor, the point to transform
        # around as the touch farthest away from touch
        anchor = max(points, key=lambda p: p.distance(touch.pos))

        # now we find the touch farthest away from anchor, if its not the
        # same as touch. Touch is not one of the two touches used to transform
        farthest = max(points, key=anchor.distance)
        if points.index(farthest) != self._touches.index(touch):
            return

        # ok, so we have touch, and anchor, so we can actually compute the
        # transformation
        old_line = Vector(*touch.ppos) - anchor
        new_line = Vector(*touch.pos) - anchor

        angle = radians(new_line.angle(old_line)) * self.do_rotation
        scale = new_line.length() / old_line.length()
        new_scale = scale * self.scale
        if new_scale < self.scale_min or new_scale > self.scale_max:
            scale = 1.0

        self.apply_transform(Matrix().rotate(angle, 0, 0, 1), anchor=anchor)
        self.apply_transform(Matrix().scale(scale, scale, scale), anchor=anchor)

    def on_touch_down(self, touch):
        x, y = touch.x, touch.y

        # if the touch isnt on the widget we do nothing
        if not self.collide_point(x, y):
            return False

        # auto bring to front
        if self.auto_bring_to_front and self.parent:
            parent = self.parent
            parent.remove_widget(self)
            parent.add_widget(self)

        # let the child widgets handle the event if they want
        touch.push()
        touch.apply_transform_2d(self.to_local)
        if super(Scatter, self).on_touch_down(touch):
            touch.pop()
            return True
        touch.pop()

        # grab the touch so we get all it later move events for sure
        touch.grab(self)
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
            self._touches.remove(touch)

        # stop porpagating if its within our bounds
        if self.collide_point(x, y):
            return True


class ScatterPlane(Scatter):

    def __init__(self, **kwargs):
        kwargs.setdefault('auto_bring_to_front', False)
        super(ScatterPlane, self).__init__(**kwargs)

    def collide_point(self, x, y):
        return True
