"""
MotionCollideBehavior
=====================

.. versionadded:: 3.0.0

.. note::
    :class:`MotionCollideBehavior` is part of the `hover` package which can be
    found in the GitHub `repository <https://github.com/pythonic64/hover>`_.
    You can install the `hover` package using the instructions from the GitHub
    page, if you want to use `Kivy>=2.1.0,<3.0.0`.

:class:`MotionCollideBehavior` is a
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class which filters events
which do not collide with a widget or events for which currently grabbed
widget is not the widget itself.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

:class:`MotionCollideBehavior` is meant to be used with
:class:`~kivy.uix.stencilview.StencilView` or its subclasses so that hover
events (events with :attr:`~kivy.input.motionevent.MotionEvent.type_id` set to
"hover") don't get handled when their position is outside the view.

Example of using :class:`MotionCollideBehavior` with
:class:`~kivy.uix.recycleview.RecycleView`::

    FilteredRecycleView(MotionCollideBehavior, RecycleView):
        pass

:class:`MotionCollideBehavior` overrides
:meth:`~kivy.uix.widget.Widget.on_motion` to add event filtering::

    class MotionCollideBehavior(object):

        def on_motion(self, etype, me):
            if me.grab_current is self \
                    or 'pos' in me.profile and self.collide_point(*me.pos):
                return super().on_motion(etype, me)
"""


class MotionCollideBehavior(object):
    """MotionCollideBehavior `mixin <https://en.wikipedia.org/wiki/Mixin>`_
    overrides :meth:`~kivy.uix.widget.Widget.on_motion` to filter-out events
    which do not collide with the widget or events which are not grabbed
    events.

    It's recommended to use this behavior with
    :class:`~kivy.uix.stencilview.StencilView` or its subclasses
    (`RecycleView`, `ScrollView`, etc.) so that hover events don't get handled
    when outside of stencil view.
    """

    def on_motion(self, etype, me):
        if me.grab_current is self \
                or 'pos' in me.profile and self.collide_point(*me.pos):
            return super().on_motion(etype, me)
