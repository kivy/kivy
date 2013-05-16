'''
Effects
=======

.. versionadded:: 1.7.0

Everything start with the :class:`~kinetic.KineticEffect`, the base class for
computing velocity out of a movement.

This base class is used to implement :class:`~scroll.ScrollEffect`, base class
used for our :class:`~kivy.uix.scrollview.ScrollView` widget effect. We have
multiple implementation:

- :class:`~kivy.effects.scroll.ScrollEffect`: base class used for implementing
  an effect. It only calculate the scrolling and the overscroll.
- :class:`~kivy.effects.dampedscroll.DampedScrollEffect`: use the overscroll
  information to allow the user to drag more than expected. Once the user stop
  the drag, the position is back to one of the bounds.
- :class:`~kivy.effects.opacityscroll.OpacityScrollEffect`: use the overscroll
  information to reduce the opacity of the scrollview widget. One the user stop
  the drag, the opacity back to one.

'''

