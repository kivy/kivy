'''
Relative Layout
===============

.. versionadded:: 1.4.0


This layout allows you to set relative coordinates for children. If you want
absolute positioning, use the :class:`~kivy.uix.floatlayout.FloatLayout`.

The :class:`RelativeLayout` class behaves just like the regular
:class:`FloatLayout` except that its child widgets are positioned relative to
the layout.

For example, if you create a RelativeLayout, add a widget with position =
(0,0), the child widget will also move when you change the position of the
RelativeLayout.  The child widgets coordiantes remain (0,0) i.e. they are
always relative to the containing layout.


.. versionchanged:: 1.7.0

    Prior to version 1.7.0, the :class:`RelativeLayout` was implemented as a
    :class`FloatLayout` inside a :class:`Scatter`.  This behaviour/widget has
    been renamed to `ScatterLayout`.  The :class:`RelativeLayout` now only
    supports relative positions (and can't be rotated, scaled or translated on
    a multitouch system using two or more fingers). This was done so that the
    implementation could be optimized and avoid the heavier calculations of
    :class:`Scatter` (e.g. inverse matrix, recaculating multiple properties
    etc.)

'''

__all__ = ('RelativeLayout', )

from kivy.uix.floatlayout import FloatLayout


class RelativeLayout(FloatLayout):
    '''RelativeLayout class, see module documentation for more information.
    '''

    def __init__(self, **kw):
        self.content = FloatLayout()
        super(RelativeLayout, self).__init__(**kw)
        self.unbind(pos=self._trigger_layout,
                pos_hint=self._trigger_layout)

    def do_layout(self, *args):
        super(RelativeLayout, self).do_layout(pos=(0, 0))

    def to_parent(self, x, y, **k):
        return (x + self.x, y + self.y)

    def to_local(self, x, y, **k):
        return (x - self.x, y - self.y)

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


