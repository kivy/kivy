'''
Effects
=======

.. versionadded:: 1.7.0

Everything starts with the :class:`~kinetic.KineticEffect`, the base class for
computing velocity out of a movement.

This base class is used to implement the :class:`~scroll.ScrollEffect`, a base
class used for our :class:`~kivy.uix.scrollview.ScrollView` widget effect.
We have multiple implementations:

- :class:`~kivy.effects.scroll.ScrollEffect`: base class used for implementing
  an effect. It only calculates the scrolling and the overscroll.
- :class:`~kivy.effects.dampedscroll.DampedScrollEffect`: uses the overscroll
  information to allow the user to drag more than expected. Once the user stops
  the drag, the position is returned to one of the bounds.
- :class:`~kivy.effects.opacityscroll.OpacityScrollEffect`: uses the overscroll
  information to reduce the opacity of the scrollview widget. When the user
  stops the drag, the opacity is set back to 1.

'''

