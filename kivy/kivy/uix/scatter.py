'''
Scatter
=======

.. image:: images/scatter.gif
    :align: right

:class:`Scatter` is used to build interactive widgets that can be translated,
rotated and scaled with two or more fingers on a multitouch system.

Scatter has its own matrix transformation: the modelview matrix is changed
before the children are drawn and the previous matrix is restored when the
drawing is finished. That makes it possible to perform rotation, scaling and
translation over the entire children tree without changing any widget
properties. That specific behavior makes the scatter unique, but there are some
advantages / constraints that you should consider:

#. The children are positioned relative to the scatter similarly to a
   :mod:`~kivy.uix.relativelayout.RelativeLayout`. So when dragging the
   scatter, the position of the children don't change, only the position of
   the scatter does.
#. The scatter size has no impact on the size of its children.
#. If you want to resize the scatter, use scale, not size (read #2). Scale
   transforms both the scatter and its children, but does not change size.
#. The scatter is not a layout. You must manage the size of the children
   yourself.

For touch events, the scatter converts from the parent matrix to the scatter
matrix automatically in on_touch_down/move/up events. If you are doing things
manually, you will need to use :meth:`~kivy.uix.widget.Widget.to_parent` and
:meth:`~kivy.uix.widget.Widget.to_local`.

Usage
-----

By default, the Scatter does not have a graphical representation: it is a
container only. The idea is to combine the Scatter with another widget, for
example an :class:`~kivy.uix.image.Image`::

    scatter = Scatter()
    image = Image(source='sun.jpg')
    scatter.add_widget(image)

Control Interactions
--------------------

By default, all interactions are enabled. You can selectively disable
them using the do_rotation, do_translation and do_scale properties.

Disable rotation::

    scatter = Scatter(do_rotation=False)

Allow only translation::

    scatter = Scatter(do_rotation=False, do_scale=False)

Allow only translation on x axis::

    scatter = Scatter(do_rotation=False, do_scale=False,
                      do_translation_y=False)


Automatic Bring to Front
------------------------

If the :attr:`Scatter.auto_bring_to_front` property is True, the scatter
widget will be removed and re-added to the parent when it is touched
(brought to front, above all other widgets in the parent). This is useful
when you are manipulating several scatter widgets and don't want the active
one to be partially hidden.

Scale Limitation
----------------

We are using a 32-bit matrix in double representation. That means we have
a limit for scaling. You cannot do infinite scaling down/up with our
implementation. Generally, you don't hit the minimum scale (because you don't
see it on the screen), but the maximum scale is 9.99506983235e+19 (2^66).

You can also limit the minimum and maximum scale allowed::

    scatter = Scatter(scale_min=.5, scale_max=3.)

Behavior
--------

.. versionchanged:: 1.1.0
    If no control interactions are enabled, then the touch handler will never
    return True.

'''

__all__ = ('Scatter', 'ScatterPlane')

from math import radians
from kivy.properties import BooleanProperty, AliasProperty, \
    NumericProperty, ObjectProperty, BoundedNumericProperty
from kivy.vector import Vector
from kivy.uix.widget import Widget
from kivy.graphics.transformation import Matrix


class Scatter(Widget):
    '''Scatter class. See module documentation for more information.

    :Events:
        `on_transform_with_touch`:
            Fired when the scatter has been transformed by user touch
            or multitouch, such as panning or zooming.
        `on_bring_to_front`:
            Fired when the scatter is brought to the front.

    .. versionchanged:: 1.9.0
        Event `on_bring_to_front` added.

    .. versionchanged:: 1.8.0
        Event `on_transform_with_touch` added.
    '''

    __events__ = ('on_transform_with_touch', 'on_bring_to_front')

    auto_bring_to_front = BooleanProperty(True)
    '''If True, the widget will be automatically pushed on the top of parent
    widget list for drawing.

    :attr:`auto_bring_to_front` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True.
    '''

    do_translation_x = BooleanProperty(True)
    '''Allow translation on the X axis.

    :attr:`do_translation_x` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    do_translation_y = BooleanProperty(True)
    '''Allow translation on Y axis.

    :attr:`do_translation_y` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    def _get_do_translation(self):
        return (self.do_translation_x, self.do_translation_y)

    def _set_do_translation(self, value):
        if type(value) in (list, tuple):
            self.do_translation_x, self.do_translation_y = value
        else:
            self.do_translation_x = self.do_translation_y = bool(value)

    do_translation = AliasProperty(_get_do_translation, _set_do_translation,
                                   bind=('do_translation_x',
                                         'do_translation_y'),
                                   cache=True)
    '''Allow translation on the X or Y axis.

    :attr:`do_translation` is an :class:`~kivy.properties.AliasProperty` of
    (:attr:`do_translation_x` + :attr:`do_translation_y`)
    '''

    translation_touches = BoundedNumericProperty(1, min=1)
    '''Determine whether translation was triggered by a single or multiple
    touches. This only has effect when :attr:`do_translation` = True.

    :attr:`translation_touches` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 1.

    .. versionadded:: 1.7.0
    '''

    do_rotation = BooleanProperty(True)
    '''Allow rotation.

    :attr:`do_rotation` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    do_scale = BooleanProperty(True)
    '''Allow scaling.

    :attr:`do_scale` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    do_collide_after_children = BooleanProperty(False)
    '''If True, the collision detection for limiting the touch inside the
    scatter will be done after dispaching the touch to the children.
    You can put children outside the bounding box of the scatter and still be
    able to touch them.

    :attr:`do_collide_after_children` is a
    :class:`~kivy.properties.BooleanProperty` and defaults to False.

    .. versionadded:: 1.3.0
    '''

    scale_min = NumericProperty(0.01)
    '''Minimum scaling factor allowed.

    :attr:`scale_min` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.01.
    '''

    scale_max = NumericProperty(1e20)
    '''Maximum scaling factor allowed.

    :attr:`scale_max` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1e20.
    '''

    transform = ObjectProperty(Matrix())
    '''Transformation matrix.

    :attr:`transform` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to the identity matrix.

    .. note::

        This matrix reflects the current state of the transformation matrix
        but setting it directly will erase previously applied
        transformations. To apply a transformation considering context,
        please use the :attr:`~Scatter.apply_transform` method.

    '''

    transform_inv = ObjectProperty(Matrix())
    '''Inverse of the transformation matrix.

    :attr:`transform_inv` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to the identity matrix.
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
        return (xmin, ymin), (xmax - xmin, ymax - ymin)

    bbox = AliasProperty(_get_bbox, bind=('transform', 'width', 'height'))
    '''Bounding box of the widget in parent space::

        ((x, y), (w, h))
        # x, y = lower left corner

    :attr:`bbox` is an :class:`~kivy.properties.AliasProperty`.
    '''

    def _get_rotation(self):
        v1 = Vector(0, 10)
        tp = self.to_parent
        v2 = Vector(*tp(*self.pos)) - tp(self.x, self.y + 10)
        return -1.0 * (v1.angle(v2) + 180) % 360

    def _set_rotation(self, rotation):
        angle_change = self.rotation - rotation
        r = Matrix().rotate(-radians(angle_change), 0, 0, 1)
        self.apply_transform(r, post_multiply=True,
                             anchor=self.to_local(*self.center))

    rotation = AliasProperty(_get_rotation, _set_rotation,
                             bind=('x', 'y', 'transform'))
    '''Rotation value of the scatter in degrees moving in a counterclockwise
    direction.

    :attr:`rotation` is an :class:`~kivy.properties.AliasProperty` and defaults
    to 0.0.
    '''

    def _get_scale(self):
        p1 = Vector(*self.to_parent(0, 0))
        p2 = Vector(*self.to_parent(1, 0))
        scale = p1.distance(p2)

        # XXX float calculation are not accurate, and then, scale can be
        # thrown again even with only the position change. So to
        # prevent anything wrong with scale, just avoid to dispatch it
        # if the scale "visually" didn't change. #947
        # Remove this ugly hack when we'll be Python 3 only.
        if hasattr(self, '_scale_p'):
            if str(scale) == str(self._scale_p):
                return self._scale_p

        self._scale_p = scale
        return scale

    def _set_scale(self, scale):
        rescale = scale * 1.0 / self.scale
        self.apply_transform(Matrix().scale(rescale, rescale, rescale),
                             post_multiply=True,
                             anchor=self.to_local(*self.center))

    scale = AliasProperty(_get_scale, _set_scale, bind=('x', 'y', 'transform'))
    '''Scale value of the scatter.

    :attr:`scale` is an :class:`~kivy.properties.AliasProperty` and defaults to
    1.0.
    '''

    def _get_center(self):
        return (self.bbox[0][0] + self.bbox[1][0] / 2.0,
                self.bbox[0][1] + self.bbox[1][1] / 2.0)

    def _set_center(self, center):
        if center == self.center:
            return False
        t = Vector(*center) - self.center
        trans = Matrix().translate(t.x, t.y, 0)
        self.apply_transform(trans)

    center = AliasProperty(_get_center, _set_center, bind=('bbox',))

    def _get_pos(self):
        return self.bbox[0]

    def _set_pos(self, pos):
        _pos = self.bbox[0]
        if pos == _pos:
            return
        t = Vector(*pos) - _pos
        trans = Matrix().translate(t.x, t.y, 0)
        self.apply_transform(trans)

    pos = AliasProperty(_get_pos, _set_pos, bind=('bbox',))

    def _get_x(self):
        return self.bbox[0][0]

    def _set_x(self, x):
        if x == self.bbox[0][0]:
            return False
        self.pos = (x, self.y)
        return True

    x = AliasProperty(_get_x, _set_x, bind=('bbox',))

    def _get_y(self):
        return self.bbox[0][1]

    def _set_y(self, y):
        if y == self.bbox[0][1]:
            return False
        self.pos = (self.x, y)
        return True

    y = AliasProperty(_get_y, _set_y, bind=('bbox',))

    def get_right(self):
        return self.x + self.bbox[1][0]

    def set_right(self, value):
        self.x = value - self.bbox[1][0]

    right = AliasProperty(get_right, set_right, bind=('x', 'bbox'))

    def get_top(self):
        return self.y + self.bbox[1][1]

    def set_top(self, value):
        self.y = value - self.bbox[1][1]

    top = AliasProperty(get_top, set_top, bind=('y', 'bbox'))

    def get_center_x(self):
        return self.x + self.bbox[1][0] / 2.

    def set_center_x(self, value):
        self.x = value - self.bbox[1][0] / 2.

    center_x = AliasProperty(get_center_x, set_center_x, bind=('x', 'bbox'))

    def get_center_y(self):
        return self.y + self.bbox[1][1] / 2.

    def set_center_y(self, value):
        self.y = value - self.bbox[1][1] / 2.

    center_y = AliasProperty(get_center_y, set_center_y, bind=('y', 'bbox'))

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

    def _apply_transform(self, m, pos=None):
        m = self.transform.multiply(m)
        return super(Scatter, self)._apply_transform(m, (0, 0))

    def apply_transform(self, trans, post_multiply=False, anchor=(0, 0)):
        '''
        Transforms the scatter by applying the "trans" transformation
        matrix (on top of its current transformation state). The resultant
        matrix can be found in the :attr:`~Scatter.transform` property.

        :Parameters:
            `trans`: :class:`~kivy.graphics.transformation.Matrix`.
                Transformation matrix to be applied to the scatter widget.
            `anchor`: tuple, defaults to (0, 0).
                The point to use as the origin of the transformation
                (uses local widget space).
            `post_multiply`: bool, defaults to False.
                If True, the transform matrix is post multiplied
                (as if applied before the current transform).

        Usage example::

            from kivy.graphics.transformation import Matrix
            mat = Matrix().scale(3, 3, 3)
            scatter_instance.apply_transform(mat)

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
        changed = False
        if len(self._touches) == self.translation_touches:
            # _last_touch_pos has last pos in correct parent space,
            # just like incoming touch
            dx = (touch.x - self._last_touch_pos[touch][0]) \
                * self.do_translation_x
            dy = (touch.y - self._last_touch_pos[touch][1]) \
                * self.do_translation_y
            dx = dx / self.translation_touches
            dy = dy / self.translation_touches
            self.apply_transform(Matrix().translate(dx, dy, 0))
            changed = True

        if len(self._touches) == 1:
            return changed

        # we have more than one touch... list of last known pos
        points = [Vector(self._last_touch_pos[t]) for t in self._touches
                  if t is not touch]
        # add current touch last
        points.append(Vector(touch.pos))

        # we only want to transform if the touch is part of the two touches
        # farthest apart! So first we find anchor, the point to transform
        # around as another touch farthest away from current touch's pos
        anchor = max(points[:-1], key=lambda p: p.distance(touch.pos))

        # now we find the touch farthest away from anchor, if its not the
        # same as touch. Touch is not one of the two touches used to transform
        farthest = max(points, key=anchor.distance)
        if farthest is not points[-1]:
            return changed

        # ok, so we have touch, and anchor, so we can actually compute the
        # transformation
        old_line = Vector(*touch.ppos) - anchor
        new_line = Vector(*touch.pos) - anchor
        if not old_line.length():   # div by zero
            return changed

        angle = radians(new_line.angle(old_line)) * self.do_rotation
        if angle:
            changed = True
        self.apply_transform(Matrix().rotate(angle, 0, 0, 1), anchor=anchor)

        if self.do_scale:
            scale = new_line.length() / old_line.length()
            new_scale = scale * self.scale
            if new_scale < self.scale_min:
                scale = self.scale_min / self.scale
            elif new_scale > self.scale_max:
                scale = self.scale_max / self.scale
            self.apply_transform(Matrix().scale(scale, scale, scale),
                                 anchor=anchor)
            changed = True
        return changed

    def _bring_to_front(self, touch):
        # auto bring to front
        if self.auto_bring_to_front and self.parent:
            parent = self.parent
            if parent.children[0] is self:
                return
            parent.remove_widget(self)
            parent.add_widget(self)
            self.dispatch('on_bring_to_front', touch)

    def on_motion(self, etype, me):
        if me.type_id in self.motion_filter and 'pos' in me.profile:
            me.push()
            me.apply_transform_2d(self.to_local)
            ret = super().on_motion(etype, me)
            me.pop()
            return ret
        return super().on_motion(etype, me)

    def on_touch_down(self, touch):
        x, y = touch.x, touch.y

        # if the touch isn't on the widget we do nothing
        if not self.do_collide_after_children:
            if not self.collide_point(x, y):
                return False

        # let the child widgets handle the event if they want
        touch.push()
        touch.apply_transform_2d(self.to_local)
        if super(Scatter, self).on_touch_down(touch):
            touch.pop()
            self._bring_to_front(touch)
            return True
        touch.pop()

        # if our child didn't do anything, and if we don't have any active
        # interaction control, then don't accept the touch.
        if not self.do_translation_x and \
                not self.do_translation_y and \
                not self.do_rotation and \
                not self.do_scale:
            return False

        if self.do_collide_after_children:
            if not self.collide_point(x, y):
                return False

        if 'multitouch_sim' in touch.profile:
            touch.multitouch_sim = True
        # grab the touch so we get all it later move events for sure
        self._bring_to_front(touch)
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
            if self.transform_with_touch(touch):
                self.dispatch('on_transform_with_touch', touch)
            self._last_touch_pos[touch] = touch.pos

        # stop propagating if its within our bounds
        if self.collide_point(x, y):
            return True

    def on_transform_with_touch(self, touch):
        '''
        Called when a touch event has transformed the scatter widget.
        By default this does nothing, but can be overridden by derived
        classes that need to react to transformations caused by user
        input.

        :Parameters:
            `touch`:
                The touch object which triggered the transformation.

        .. versionadded:: 1.8.0
        '''
        pass

    def on_bring_to_front(self, touch):
        '''
        Called when a touch event causes the scatter to be brought to the
        front of the parent (only if :attr:`auto_bring_to_front` is True)

        :Parameters:
            `touch`:
                The touch object which brought the scatter to front.

        .. versionadded:: 1.9.0
        '''
        pass

    def on_touch_up(self, touch):
        x, y = touch.x, touch.y
        # if the touch isn't on the widget we do nothing, just try children
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
    '''This is essentially an unbounded Scatter widget. It's a convenience
       class to make it easier to handle infinite planes.
    '''

    def __init__(self, **kwargs):
        if 'auto_bring_to_front' not in kwargs:
            self.auto_bring_to_front = False
        super(ScatterPlane, self).__init__(**kwargs)

    def collide_point(self, x, y):
        return True
