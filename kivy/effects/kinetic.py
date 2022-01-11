'''
Kinetic effect
==============

.. versionadded:: 1.7.0

The :class:`KineticEffect` is the base class that is used to compute the
velocity out of a movement. When the movement is finished, the effect will
compute the position of the movement according to the velocity, and reduce the
velocity with a friction. The movement stop until the velocity is 0.

Conceptually, the usage could be::

    >>> effect = KineticEffect()
    >>> effect.start(10)
    >>> effect.update(15)
    >>> effect.update(30)
    >>> effect.stop(48)

Over the time, you will start a movement of a value, update it, and stop the
movement. At this time, you'll get the movement value into
:attr:`KineticEffect.value`. On the example i've typed manually, the computed
velocity will be::

    >>> effect.velocity
    3.1619100231163046

After multiple clock interaction, the velocity will decrease according to
:attr:`KineticEffect.friction`. The computed value will be stored in
:attr:`KineticEffect.value`. The output of this `value` could be::

    46.30038145219605
    54.58302451968686
    61.9229016256196
    # ...

'''

__all__ = ('KineticEffect', )


from time import time
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, BooleanProperty
from kivy.clock import Clock


class KineticEffect(EventDispatcher):
    '''Kinetic effect class. See module documentation for more information.
    '''

    velocity = NumericProperty(0)
    '''Velocity of the movement.

    :attr:`velocity` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    friction = NumericProperty(0.05)
    '''Friction to apply on the velocity

    :attr:`friction` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.05.
    '''

    value = NumericProperty(0)
    '''Value (during the movement and computed) of the effect.

    :attr:`value` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    is_manual = BooleanProperty(False)
    '''Indicate if a movement is in progress (True) or not (False).

    :attr:`is_manual` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.
    '''

    max_history = NumericProperty(5)
    '''Save up to `max_history` movement value into the history. This is used
    for correctly calculating the velocity according to the movement.

    :attr:`max_history` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 5.
    '''

    min_distance = NumericProperty(.1)
    '''The minimal distance for a movement to have nonzero velocity.

    .. versionadded:: 1.8.0

    :attr:`min_distance` is :class:`~kivy.properties.NumericProperty` and
    defaults to 0.1.
    '''

    min_velocity = NumericProperty(.5)
    '''Velocity below this quantity is normalized to 0. In other words,
    any motion whose velocity falls below this number is stopped.

    .. versionadded:: 1.8.0

    :attr:`min_velocity` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.5.
    '''

    std_dt = NumericProperty(0.017)
    ''' std_dt
        correction update_velocity if dt is not constant

    .. versionadded:: 2.0.0

    :attr:`std_dt` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.017.
    '''

    def __init__(self, **kwargs):
        self.history = []
        self.trigger_velocity_update = Clock.create_trigger(
            self.update_velocity, 0)
        super(KineticEffect, self).__init__(**kwargs)

    def apply_distance(self, distance):
        if abs(distance) < self.min_distance:
            self.velocity = 0
        self.value += distance

    def start(self, val, t=None):
        '''Start the movement.

        :Parameters:
            `val`: float or int
                Value of the movement
            `t`: float, defaults to None
                Time when the movement happen. If no time is set, it will use
                time.time()
        '''
        self.is_manual = True
        t = t or time()
        self.velocity = 0
        self.history = [(t, val)]

    def update(self, val, t=None):
        '''Update the movement.

        See :meth:`start` for the arguments.
        '''
        t = t or time()
        distance = val - self.history[-1][1]
        self.apply_distance(distance)
        self.history.append((t, val))
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def stop(self, val, t=None):
        '''Stop the movement.

        See :meth:`start` for the arguments.
        '''
        self.is_manual = False
        t = t or time()
        distance = val - self.history[-1][1]
        self.apply_distance(distance)
        newest_sample = (t, val)
        old_sample = self.history[0]
        for sample in self.history:
            if (newest_sample[0] - sample[0]) < 10. / 60.:
                break
            old_sample = sample
        distance = newest_sample[1] - old_sample[1]
        duration = abs(newest_sample[0] - old_sample[0])
        self.velocity = (distance / max(duration, 0.0001))
        self.trigger_velocity_update()

    def cancel(self):
        '''Cancel a movement. This can be used in case :meth:`stop` cannot be
        called. It will reset :attr:`is_manual` to False, and compute the
        movement if the velocity is > 0.
        '''
        self.is_manual = False
        self.trigger_velocity_update()

    def update_velocity(self, dt):
        '''(internal) Update the velocity according to the frametime and
        friction.
        '''
        if abs(self.velocity) <= self.min_velocity:
            self.velocity = 0
            return

        self.velocity -= self.velocity * self.friction * dt / self.std_dt
        self.apply_distance(self.velocity * dt)
        self.trigger_velocity_update()
