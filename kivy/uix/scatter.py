'''
Scatter
=======

:class:`Scatter` is used to build interactive widgets that can be translated,
rotated and scaled with two or more fingers on a multitouch system.

The Scatter have its own matrix transformation: the modelview matrix are
changing before the childs draw, and the previous matrix is restored when the
drawing is finished. That make possible the rotation / scale / translate of its
whole children tree, without changing them.

That specific behavior make the scatter unique, and their is some advantages /
constraint that you should care about:

#. The children are positionned relative to the 0, 0. The scatter position have
   no impact of the children position. This applies to the size too.
#. If you want to resize the scatter, use scale, not size. (read #1.)
#. The scatter is not a layout, you must take care of the children size
   yourself.

For touch events, the scatter convert from the parent matrix to scatter matrix
automatically in on_touch_down/move/up event. If you are doing all the things
manually, you will need to use :func:`~kivy.uix.widget.Widget.to_parent`,
:func:`~kivy.uix.widget.Widget.to_local`.

Usage
-----

By default, the widget doesn't have any graphical representation, it is a
container only. The idea is to combine Scatter with another widget, for
example :class:`~kivy.uix.image.Image` ::

    scatter = Scatter()
    image = Image(source='sun.jpg')
    scatter.add_widget(image)

Control interactions
--------------------

By default, all interactions are enabled. You can selectively disable
them using the do_{rotation, translation, scale} properties.

Disable rotation ::

    scatter = Scatter(do_rotation=False)

Allow only translation ::

    scatter = Scatter(do_rotation=False, do_scale=False)

Allow only translation on x axis ::

    scatter = Scatter(do_rotation=False, do_scale=False,
                      do_translation_y=False)


Automatic bring to front
------------------------

If the :data:`Scatter.auto_bring_to_front` property is True, the scatter
widget will be removed and re-added to the parent when it is touched
(brought to front, above all other widgets). This is useful when you are
manipulating several scatter widgets and don't want the active to be
partially hidden.

Scale limitation
----------------

We are using a 32-bit matrix in double representation. That means we have
a limit for scaling, you cannot do infinite scale down/up with our
implementation. Generally, you don't hit the minimum scale (because you don't
see it on the screen), but the maximum scale is 9.99506983235e+19 (2^66)

You can also limit the minimum and maximum scale allowed. ::

    scatter = Scatter(scale_min=.5, scale_max=3.)

Behaviors
---------

.. versionchanged:: 1.1.0

    If no control interactions are enabled, then touch handler will never return
    True.

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

    def get_right(self):
        return self.x + self.bbox[1][0]

    def set_right(self, value):
        self.x = value - self.bbox[1][0]

    right = AliasProperty(get_right, set_right, bind=('x', 'width'))

    def get_top(self):
        return self.y + self.bbox[1][1]

    def set_top(self, value):
        self.y = value - self.bbox[1][1]

    top = AliasProperty(get_top, set_top, bind=('y', 'height'))

    def get_center_x(self):
        return self.x + self.bbox[1][0] / 2.

    def set_center_x(self, value):
        self.x = value - self.bbox[1][0] / 2.
    center_x = AliasProperty(get_center_x, set_center_x, bind=('x', 'width'))

    def get_center_y(self):
        return self.y + self.bbox[1][1] / 2.

    def set_center_y(self, value):
        self.y = value - self.bbox[1][1] / 2.
    center_y = AliasProperty(get_center_y, set_center_y, bind=('y', 'height'))

    def __init__(self, **kwargs):
        self._touches = []
        self._last_touch_pos = {}
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
            # just like incoming touch
            dx = (touch.x - self._last_touch_pos[touch][0]) \
                    * self.do_translation_x
            dy = (touch.y - self._last_touch_pos[touch][1]) \
                    * self.do_translation_y
            self.apply_transform(Matrix().translate(dx, dy, 0))
            return

        # we have more than one touch...
        points = [Vector(self._last_touch_pos[t]) for t in self._touches]

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
        self.apply_transform(Matrix().rotate(angle, 0, 0, 1), anchor=anchor)

        if self.do_scale:
            scale = new_line.length() / old_line.length()
            new_scale = scale * self.scale
            if new_scale < self.scale_min or new_scale > self.scale_max:
                scale = 1.0
            self.apply_transform(Matrix().scale(scale, scale, scale),
                                 anchor=anchor)

    def _bring_to_front(self):
        # auto bring to front
        if self.auto_bring_to_front and self.parent:
            parent = self.parent
            parent.remove_widget(self)
            parent.add_widget(self)

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
            self._bring_to_front()
            return True
        touch.pop()

        # if our child didn't do anything, and if we don't have any active
        # interaction control, then don't accept the touch.
        if not self.do_translation_x and \
            not self.do_translation_y and \
            not self.do_rotation and \
            not self.do_scale:
            return False

        # grab the touch so we get all it later move events for sure
        self._bring_to_front()
        touch.grab(self)
        self._touches.append(touch)
        self._last_touch_pos[touch] = touch.pos

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

        # stop propagating if its within our bounds
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

        # stop propagating if its within our bounds
        if self.collide_point(x, y):
            return True


class ScatterPlane(Scatter):

    def __init__(self, **kwargs):
        kwargs.setdefault('auto_bring_to_front', False)
        super(ScatterPlane, self).__init__(**kwargs)

    def collide_point(self, x, y):
        return True
