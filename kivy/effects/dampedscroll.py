'''
Damped scroll effect
====================

.. versionadded:: 3.0.0

This scroll effect is inspired by Flutter's BouncingScrollPhysics, which mimics
iOS-style scrolling behavior. Key features:

1. Logarithmic resistance during overscroll drag (rubber band feel)
2. Critically damped spring for bounce-back (no oscillation)
3. Exponential friction for momentum scrolling
4. Mathematically guaranteed stability

IMPLEMENTATION NOTES:
--------------------
This is a clean-room implementation based on understanding the physics and
algorithms used in Flutter and iOS, not a direct port of the code.

Mathematical formulas, physical laws, and algorithms are not subject to
copyright. This implementation uses standard physics equations and
mathematical transformations that are in the public domain.

Differences from the original DampedScrollEffect:
-------------------------------------------------
This implementation is different from the original DampedScrollEffect
that was introduced in Kivy 1.7.0.  The original DampedScrollEffect had a
numerical instability issue. This implementation uses critical damping
to ensure the effect is stable.  Additionally the properties in the
effect are different, and allow for more control over the effect.
'''

__all__ = ('DampedScrollEffect',)

from math import sqrt
from kivy.effects.scroll import ScrollEffect
from kivy.properties import NumericProperty


class DampedScrollEffect(ScrollEffect):
    '''Flutter-inspired scroll effect with iOS-style rubber banding.

    This implementation uses:

    1. Logarithmic resistance for overscroll (increasing resistance as you pull)
    2. Critically damped spring for bounce-back (no oscillation)
    3. Exponential friction for smooth momentum

    See module documentation for more information.
    '''

    rubber_band_coeff = NumericProperty(0.55)
    '''Rubber band resistance coefficient. Higher values = less resistance.

    Flutter/iOS typically use ~0.55. Lower values (0.3-0.4) feel stiffer,
    higher values (0.6-0.8) feel more elastic.

    :attr:`rubber_band_coeff` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.55.
    '''

    spring_mass = NumericProperty(1.0)
    '''Mass for spring simulation (affects bounce-back speed).

    :attr:`spring_mass` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.0.
    '''

    spring_stiffness = NumericProperty(100.0)
    '''Stiffness for spring simulation (affects bounce-back speed).

    :attr:`spring_stiffness` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 100.0.
    '''

    min_overscroll = NumericProperty(.5)
    '''An overscroll less than this amount will be normalized to 0.

    :attr:`min_overscroll` is a :class:`~kivy.properties.NumericProperty` and
    defaults to .5.
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._spring_time = 0
        self._spring_start_position = 0
        self._spring_target = 0
        self._spring_velocity = 0

    def _rubber_band_clamp(self, overscroll, dimension):
        # Calculate rubber band resistance using logarithmic function.
        # This is the key to iOS-style feel: resistance increases
        # logarithmically, as you pull further, creating natural
        # rubber band behavior.
        # Formula from WebKit: (1.0 - (1.0 / ((x * coeff / dim) + 1.0))) * dim
        if abs(overscroll) < 0.001:
            return 0

        sign = 1 if overscroll > 0 else -1
        x = abs(overscroll)

        # Logarithmic resistance formula
        result = (1.0 - (1.0 / ((x * self.rubber_band_coeff / dimension) + 1.0))
                  ) * dimension
        return sign * result

    def _get_viewport_dimension(self):
        # Get the viewport dimension for rubber band calculation.
        # Detects whether this effect is used for X or Y scrolling by checking
        # which effect instance (effect_x or effect_y) this is in the parent
        # ScrollView.
        # Returns the appropriate dimension.
        target_widget = self.target_widget
        sv = target_widget.parent

        if sv.effect_x is self:
            # This is the X effect - use width for horizontal scrolling
            return target_widget.width
        elif sv.effect_y is self:
            # This is the Y effect - use height for vertical scrolling
            return self.target_widget.height

    def update_velocity(self, dt):
        # Update velocity with critically damped spring physics.
        # If we're not moving and not overscrolled, stop
        if abs(self.velocity) <= self.min_velocity and abs(
                self.overscroll) < self.min_overscroll:
            self.velocity = 0
            self.overscroll = 0
            return

        # Check if we're in overscroll and should apply spring forces
        if abs(self.overscroll) > self.min_overscroll and not self.is_manual:
            # Use critically damped spring simulation
            self._apply_spring_force(dt)
        else:
            # Normal momentum scrolling with exponential friction
            if abs(self.overscroll) < self.min_overscroll:
                self.overscroll = 0

            # Standard friction
            friction_force = self.velocity * self.friction * dt / self.std_dt
            self.velocity = self.velocity - friction_force

            if not self.is_manual:
                self.apply_distance(self.velocity * dt)

        self.trigger_velocity_update()

    def _apply_spring_force(self, dt):
        # (internal) Apply critically damped spring force for stable bounce-back.
        # Uses the critical damping formula to ensure no oscillation:
        # damping = 2 * sqrt(stiffness * mass)
        # This is what makes the effect stable - critical damping prevents
        # overshoot.
        # Calculate critical damping (this is the key to stability!)
        critical_damping = 2.0 * sqrt(self.spring_stiffness * self.spring_mass)

        # Spring force (Hooke's law: F = -kx)
        spring_force = -self.spring_stiffness * self.overscroll

        # Damping force (F = -cv)
        damping_force = -critical_damping * self.velocity

        # Total acceleration (F = ma, so a = F/m)
        acceleration = (spring_force + damping_force) / self.spring_mass

        # Update velocity
        self.velocity += acceleration * dt

        # Update position
        distance = self.velocity * dt

        # Determine target (min or max)
        if self.overscroll > 0:
            target = self.max
        else:
            target = self.min

        # Apply distance
        self.apply_distance(distance)

        # Check if we've reached the target and should stop
        if self.overscroll > 0 and self.value <= self.max:
            self.value = self.max
            self.velocity = 0
            self.overscroll = 0
        elif self.overscroll < 0 and self.value >= self.min:
            self.value = self.min
            self.velocity = 0
            self.overscroll = 0

    def apply_distance(self, distance):
        # Apply distance with rubber band resistance during manual scrolling.
        if self.is_manual and abs(self.overscroll) > 0:
            # Apply logarithmic resistance during drag
            dimension = self._get_viewport_dimension()

            # Calculate how much resistance to apply
            # As overscroll increases, resistance increases logarithmically
            current_factor = abs(
                self._rubber_band_clamp(self.overscroll, dimension) /
                (self.overscroll if self.overscroll != 0 else 1))

            # Reduce distance based on resistance
            # The further you pull, the less distance you get per pixel of drag
            distance *= current_factor * 0.5  # 0.5 adds extra resistance

        super().apply_distance(distance)

    def on_value(self, *args):
        # Update overscroll when value changes.
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
        # Trigger velocity update when overscroll changes.
        if not self.is_manual:
            self.trigger_velocity_update()
