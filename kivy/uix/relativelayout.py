'''
Relative Layout
===============

.. versionadded:: 1.4.0


This layout allows you to set relative coordinates for children. If you want
absolute positioning, use the :class:`~kivy.uix.floatlayout.FloatLayout`.

The :class:`RelativeLayout` class behaves just like the regular
:class:`FloatLayout` except that its child widgets are positioned relative to
the layout.

When a widget with position = (0,0) is added to a RelativeLayout,
the child widget will also move when the position of the RelativeLayout
is changed. The child widgets coordinates remain (0,0) as they are
always relative to the parent layout.

Coordinate Systems
------------------

Window coordinates
~~~~~~~~~~~~~~~~~~

By default, there's only one coordinate system that defines the position of
widgets and touch events dispatched to them: the window coordinate system,
which places (0, 0) at the bottom left corner of the window.
Although there are other coordinate systems defined, e.g. local
and parent coordinates, these coordinate systems are identical to the window
coordinate system as long as a relative layout type widget is not in the
widget's parent stack. When widget.pos is read or a touch is received,
the coordinate values are in parent coordinates. But as mentioned, these are
identical to window coordinates, even in complex widget stacks as long as
there's no relative layout type widget in the widget's parent stack.

For example:

.. code-block:: kv

    BoxLayout:
        Label:
            text: 'Left'
        Button:
            text: 'Middle'
            on_touch_down: print('Middle: {}'.format(args[1].pos))
        BoxLayout:
            on_touch_down: print('Box: {}'.format(args[1].pos))
            Button:
                text: 'Right'
                on_touch_down: print('Right: {}'.format(args[1].pos))

When the middle button is clicked and the touch propagates through the
different parent coordinate systems, it prints the following::

    >>> Box: (430.0, 282.0)
    >>> Right: (430.0, 282.0)
    >>> Middle: (430.0, 282.0)

As claimed, the touch has identical coordinates to the window coordinates
in every coordinate system. :meth:`~kivy.uix.widget.Widget.collide_point`
for example, takes the point in window coordinates.

Parent coordinates
~~~~~~~~~~~~~~~~~~

Other :class:`RelativeLayout` type widgets are
:class:`~kivy.uix.scatter.Scatter`,
:class:`~kivy.uix.scatterlayout.ScatterLayout`,
and :class:`~kivy.uix.scrollview.ScrollView`. If such a special widget is in
the parent stack, only then does the parent and local coordinate system
diverge from the window coordinate system. For each such widget in the stack,
a coordinate system with (0, 0) of that coordinate system being at the bottom
left corner of that widget is created. **Position and touch coordinates
received and read by a widget are in the coordinate system of the most
recent special widget in its parent stack (not including itself) or in window
coordinates if there are none** (as in the first example). We call these
coordinates parent coordinates.


For example:

.. code-block:: kv

    BoxLayout:
        Label:
            text: 'Left'
        Button:
            text: 'Middle'
            on_touch_down: print('Middle: {}'.format(args[1].pos))
        RelativeLayout:
            on_touch_down: print('Relative: {}'.format(args[1].pos))
            Button:
                text: 'Right'
                on_touch_down: print('Right: {}'.format(args[1].pos))

Clicking on the middle button prints::

    >>> Relative: (396.0, 298.0)
    >>> Right: (-137.33, 298.0)
    >>> Middle: (396.0, 298.0)

As the touch propagates through the widgets, for each widget, the
touch is received in parent coordinates. Because both the relative and middle
widgets don't have these special widgets in their parent stack, the touch is
the same as window coordinates. Only the right widget, which has a
RelativeLayout in its parent stack, receives the touch in coordinates relative
to that RelativeLayout which is different than window coordinates.

Local and Widget coordinates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When expressed in parent coordinates, the position is expressed in the
coordinates of the most recent special widget in its parent stack, not
including itself. When expressed in local or widget coordinates, the widgets
themselves are also included.

Changing the above example to transform the parent coordinates into local
coordinates:

.. code-block:: kv

    BoxLayout:
        Label:
            text: 'Left'
        Button:
            text: 'Middle'
            on_touch_down: print('Middle: {}'.format(\
self.to_local(*args[1].pos)))
        RelativeLayout:
            on_touch_down: print('Relative: {}'.format(\
self.to_local(*args[1].pos)))
            Button:
                text: 'Right'
                on_touch_down: print('Right: {}'.format(\
self.to_local(*args[1].pos)))

Now, clicking on the middle button prints::

    >>> Relative: (-135.33, 301.0)
    >>> Right: (-135.33, 301.0)
    >>> Middle: (398.0, 301.0)

This is because now the relative widget also expresses the coordinates
relative to itself.

.. note::

    Although all widgets including :class:`RelativeLayout` receive their touch
    events in ``on_touch_xxx`` in parent coordinates, these special widgets
    will transform the touch position to be in local coordinates before it
    calls ``super``. This may only be noticeable in a complex inheritance
    class.

Coordinate transformations
~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`~kivy.uix.widget.Widget` provides 4 functions to transform coordinates
between the various coordinate systems. For now, we assume that the `relative`
keyword of these functions is `False`.
:meth:`~kivy.uix.widget.Widget.to_widget` takes the coordinates expressed in
window coordinates and returns them in local (widget) coordinates.
:meth:`~kivy.uix.widget.Widget.to_window` takes the coordinates expressed in
local coordinates and returns them in window coordinates.
:meth:`~kivy.uix.widget.Widget.to_parent` takes the coordinates expressed in
local coordinates and returns them in parent coordinates.
:meth:`~kivy.uix.widget.Widget.to_local` takes the coordinates expressed in
parent coordinates and returns them in local coordinates.

Each of the 4 transformation functions take a `relative` parameter. When the
relative parameter is True, the coordinates are returned or originate in
true relative coordinates - relative to a coordinate system with its (0, 0) at
the bottom left corner of the widget in question.

.. _kivy-uix-relativelayout-common-pitfalls:

Common Pitfalls
---------------

As all positions within a :class:`RelativeLayout` are relative to the position
of the layout itself, the position of the layout should never be used in
determining the position of sub-widgets or the layout's :attr:`canvas`.

Take the following kv code for example:

.. container:: align-right

    .. figure:: images/relativelayout-fixedposition.png
        :scale: 50%

        expected result

    .. figure:: images/relativelayout-doubleposition.png
        :scale: 50%

        actual result

.. code-block:: kv

    FloatLayout:
        Widget:
            size_hint: None, None
            size: 200, 200
            pos: 200, 200

            canvas:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

        RelativeLayout:
            size_hint: None, None
            size: 200, 200
            pos: 200, 200

            canvas:
                Color:
                    rgba: 1, 0, 0, 0.5
                Rectangle:
                    pos: self.pos  # incorrect
                    size: self.size

You might expect this to render a single pink rectangle; however, the content
of the :class:`RelativeLayout` is already transformed, so the use of
`pos: self.pos` will double that transformation. In this case, using
`pos: 0, 0` or omitting `pos` completely will provide the expected result.

This also applies to the position of sub-widgets. Instead of positioning a
:class:`~kivy.uix.widget.Widget` based on the layout's own position:

.. code-block:: kv

    RelativeLayout:
        Widget:
            pos: self.parent.pos
        Widget:
            center: self.parent.center

use the :attr:`pos_hint` property:

.. code-block:: kv

    RelativeLayout:
        Widget:
            pos_hint: {'x': 0, 'y': 0}
        Widget:
            pos_hint: {'center_x': 0.5, 'center_y': 0.5}

.. versionchanged:: 1.7.0
    Prior to version 1.7.0, the :class:`RelativeLayout` was implemented as a
    :class:`~kivy.uix.floatlayout.FloatLayout` inside a
    :class:`~kivy.uix.scatter.Scatter`. This behavior/widget has
    been renamed to `ScatterLayout`. The :class:`RelativeLayout` now only
    supports relative positions (and can't be rotated, scaled or translated on
    a multitouch system using two or more fingers). This was done so that the
    implementation could be optimized and avoid the heavier calculations of
    :class:`Scatter` (e.g. inverse matrix, recalculating multiple properties
    etc.)

'''

__all__ = ('RelativeLayout', )

from kivy.uix.floatlayout import FloatLayout


class RelativeLayout(FloatLayout):
    '''RelativeLayout class, see module documentation for more information.
    '''

    def __init__(self, **kw):
        super(RelativeLayout, self).__init__(**kw)
        funbind = self.funbind
        trigger = self._trigger_layout
        funbind('pos', trigger)
        funbind('pos_hint', trigger)

    def do_layout(self, *args):
        super(RelativeLayout, self).do_layout(pos=(0, 0))

    def to_parent(self, x, y, **k):
        return (x + self.x, y + self.y)

    def to_local(self, x, y, **k):
        return (x - self.x, y - self.y)

    def _apply_transform(self, m, pos=None):
        m.translate(self.x, self.y, 0)
        return super(RelativeLayout, self)._apply_transform(m, (0, 0))

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
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = super(RelativeLayout, self).on_touch_down(touch)
        touch.pop()
        return ret

    def on_touch_move(self, touch):
        x, y = touch.x, touch.y
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = super(RelativeLayout, self).on_touch_move(touch)
        touch.pop()
        return ret

    def on_touch_up(self, touch):
        x, y = touch.x, touch.y
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = super(RelativeLayout, self).on_touch_up(touch)
        touch.pop()
        return ret
