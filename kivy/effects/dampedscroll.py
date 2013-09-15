'''
Damped scroll effect
====================

.. versionadded:: 1.7.0

This damped scroll effect will use the
:data:`~kivy.effects.scroll.ScrollEffect.overscroll` to calculate the scroll
value, and slows going back to the upper or lower limit.

'''

__all__ = ('DampedScrollEffect',)


from kivy.effects.scroll import ScrollEffect
from kivy.properties import NumericProperty, BooleanProperty
from kivy.metrics import sp


class DampedScrollEffect(ScrollEffect):
    '''DampedScrollEffect class. See the module documentation for more
    information.
    '''

    edge_damping = NumericProperty(0.25)
    '''Edge damping.

    :data:`edge_damping` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.25
    '''

    spring_constant = NumericProperty(2.0)
    '''Spring constant.

    :data:`spring_constant` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 2.0
    '''

    min_overscroll = NumericProperty(.5)
    '''An overscroll less than this amount will be normalized to 0.

    .. versionadded:: 1.8.0

    :data:`min_overscroll` is a :class:`~kivy.properties.NumericProperty` and
    defaults to .5.
    '''

    round_value = BooleanProperty(True)
    '''If True, when the motion stops, :attr:`value` is rounded to the nearest
    integer.

    .. versionadded:: 1.8.0

    :data:`round_value` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''
    def update_velocity(self, dt):
        if abs(self.velocity) <= self.min_velocity and self.overscroll == 0:
            self.velocity = 0
            # why does this need to be rounded? For now refactored it.
            if self.round_value:
                self.value = round(self.value)
            return

        total_force = self.velocity * self.friction
        if abs(self.overscroll) > self.min_overscroll:
            total_force += self.velocity * self.edge_damping
            total_force += self.overscroll * self.spring_constant
        else:
            self.overscroll = 0

        self.velocity = self.velocity - total_force
        if not self.is_manual:
            self.apply_distance(self.velocity * dt)
        self.trigger_velocity_update()

    def on_value(self, *args):
        scroll_min = self.min
        scroll_max = self.max
        if scroll_min > scroll_max:
            scroll_min, scroll_max = scroll_max, scroll_min
        if self.value < scroll_min:
            self.overscroll = self.value - scroll_min
        elif self.value > scroll_max:
            self.overscroll = self.value - scroll_max
        else:
            self.overscroll = 0
        self.scroll = self.value

    def on_overscroll(self, *args):
        self.trigger_velocity_update()

    def apply_distance(self, distance):
        os = abs(self.overscroll)
        if os:
            distance /= 1. + os / sp(200.)
        super(DampedScrollEffect, self).apply_distance(distance)



