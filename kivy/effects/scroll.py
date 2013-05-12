'''
Scroll Effect
=============

.. versionadded:: 1.7.0

Based on the :class:`~kivy.effects.kinetic`, the :class:`ScrollEffect` will
limit the movement to bounds, determined by :data:`~ScrollEffect.min` and
:data:`~ScrollEffect.max`. If the movement is going outside of the
bounds, it will calculate the amount of :data:`~ScrollEffect.overscroll`, and
try to get back the value to one of the bounds.

This is very useful for implementing scrolling list. We actually use that class
as a base effect for our :class:`~kivy.uix.scrollview.ScrollView` widget.

'''


__all__ = ('ScrollEffect', )


from kivy.effects.kinetic import KineticEffect
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ObjectProperty


class ScrollEffect(KineticEffect):
    '''ScrollEffect class. See the module documentation for more informations.
    '''

    drag_threshold = NumericProperty('20sp')
    '''Minimum distance to travel until the movement is considered as a drag.

    :data:`velocity` is a :class:`~kivy.properties.NumericProperty`, default to
    20sp
    '''

    min = NumericProperty(0)
    '''Minimum boundary to use for scrolling.

    :data:`min` is a :class:`~kivy.properties.NumericProperty`, default to
    0
    '''

    max = NumericProperty(0)
    '''Maximum boundary to use for scrolling.

    :data:`max` is a :class:`~kivy.properties.NumericProperty`, default to
    0
    '''

    scroll = NumericProperty(0)
    '''Computed value for scrolling. This is different that
    :data:`~kivy.effets.kinetic.KineticEffect.value`, this one will go back to
    one of the bounds instead.

    :data:`scroll` is a :class:`~kivy.properties.NumericProperty`, default
    to 0
    '''

    overscroll = NumericProperty(0)
    '''Computed value when the user over-scroll = going out of the bounds.

    :data:`overscroll` is a :class:`~kivy.properties.NumericProperty`, default to
    0
    '''

    target_widget = ObjectProperty(None, allownone=True, baseclass=Widget)
    '''Widget to attach to this effect. Even if this class doesn't do any change
    by default on the `target_widget`, subclass can change the graphics or apply
    custom transformation.

    :data:`target_widget` is a :class:`~kivy.properties.ObjectProperty`, default
    to None.
    '''

    displacement = NumericProperty(0)
    '''Cumulative distance of the movement, during the interaction. This is used
    to determine if the movemenent is a drag (more than :data:`drag_threshold`)
    or not.

    :data:`displacement` is a :class:`~kivy.properties.NumericProperty`, default to
    0
    '''

    def reset(self, pos):
        '''(internal) Reset the value and the velocity to the `pos`. Mostly used
        when the bounds are checked.
        '''
        self.value = pos
        self.velocity = 0
        if self.history:
            val = self.history[-1][1]
            super(ScrollEffect, self).start(val, None)

    def on_value(self, *args):
        scroll_min = self.min
        scroll_max = self.max
        if scroll_min > scroll_max:
            scroll_min, scroll_max = scroll_max, scroll_min
        if self.value < scroll_min:
            self.overscroll = self.value - scroll_min
            self.reset(scroll_min)
        elif self.value > scroll_max:
            self.overscroll = self.value - scroll_max
            self.reset(scroll_max)
        else:
            self.scroll = self.value

    def start(self, val, t=None):
        self.is_manual = True
        self.displacement = 0
        return super(ScrollEffect, self).start(val, t)

    def update(self, val, t=None):
        self.displacement += abs(val - self.history[-1][1])
        return super(ScrollEffect, self).update(val, t)

    def stop(self, val, t=None):
        self.is_manual = False
        self.displacement += abs(val - self.history[-1][1])
        if self.displacement <= self.drag_threshold:
            self.velocity = 0
            return
        return super(ScrollEffect, self).stop(val, t)

