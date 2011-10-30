'''
Animation
=========

:class:`Animation` and :class:`AnimationTransition` are used to animate
:class:`~kivy.uix.widget.Widget` properties. You must specify (minimum) a
property name and target value. To use Animation, follow these steps:

    * Setup an Animation object
    * Use the Animation object on a Widget

Simple animation
----------------

To animate a Widget's x or y position, simply specify the target x/y values
where you want the widget positioned at the end of the animation::

    anim = Animation(x=100, y=100)
    anim.start(widget)

The animation will last for 1 second unless :data:`duration` is specified.
When anim.start() is called, the Widget will move smoothly from the current
x/y position to (100, 100).

Multiple properties and transitions
-----------------------------------

You can animate multiple properties and use built-in or custom transition
functions using :data:`transition` (or `t=` shortcut). For example,
to animate the position and size using the 'in_quad' transition::

    anim = Animation(x=50, size=(80, 80), t='in_quad')
    anim.start(widget)

Note that the `t=` parameter can be the string name of a method in the
:class:`AnimationTransition` class, or your own animation function.

Sequential animation
--------------------

To join animations sequentially, use the '+' operator. The following example
will animate to x=50 over 1 second, then animate size to (80, 80) over the
next two seconds::

    anim = Animation(x=50) + Animation(size=(80, 80), duration=2.)
    anim.start(widget)

Parallel animation
------------------

To join animations in parallel, use the '&' operator. The following example
will animate position to (80, 10) over 1 second, while in parallel animating
the first half of size=(800, 800)::

    anim = Animation(pos=(80, 10))
    anim &= Animation(size=(800, 800), duration=2.)
    anim.start(widget)

'''

__all__ = ('Animation', 'AnimationTransition')

from types import ListType, TupleType, DictType
from math import sqrt, cos, sin, pi
from kivy.event import EventDispatcher
from kivy.clock import Clock


class Animation(EventDispatcher):
    '''Create an animation definition that can be used to animate a Widget

    :Parameters:
        `duration` or `d`: float, default to 1.
            Duration of the animation, in seconds
        `transition` or `t`: str or func
            Transition function for animate properties. It can be the name of a
            method from :class:`AnimationTransition`

    :Events:
        `on_start`: widget
            Fired when the animation is started on a widget
        `on_complete`: widget
            Fired when the animation is completed or stopped on a widget
        `on_progress`: widget, progression
            Fired when the progression of the animation is changing
    '''

    _instances = set()

    def __init__(self, **kw):
        # Register events
        self.register_event_type('on_start')
        self.register_event_type('on_progress')
        self.register_event_type('on_complete')

        super(Animation, self).__init__(**kw)

        # Initialize
        self._clock_installed = False
        self._duration = kw.get('d', kw.get('duration', 1.))
        self._transition = kw.get('t', kw.get('transition', 'linear'))
        if isinstance(self._transition, basestring):
            self._transition = getattr(AnimationTransition, self._transition)
        for key in ('d', 't', 'duration', 'transition'):
            kw.pop(key, None)
        self._animated_properties = kw
        self._widgets = {}

    @property
    def duration(self):
        '''Return the duration of the animation
        '''
        return self._duration

    @property
    def transition(self):
        '''Return the transition of the animation
        '''
        return self._transition

    @property
    def animated_animated_properties(self):
        '''Return the properties used to animate
        '''
        return self._animated_properties

    @staticmethod
    def stop_all(widget, *largs):
        '''Stop all animations that concern a specific widget / list of
        properties.

        Example ::

            anim = Animation(x=50)
            anim.start(widget)

            # and later
            Animation.stop_all(widget, 'x')
        '''
        if len(largs):
            for animation in list(Animation._instances):
                for x in largs:
                    animation.stop_property(widget, x)
        else:
            for animation in Animation._instances[:]:
                animation.stop(widget)

    def start(self, widget):
        '''Start the animation on a widget
        '''
        self.stop(widget)
        self._initialize(widget)
        self._register()
        self.dispatch('on_start', widget)

    def stop(self, widget):
        '''Stop the animation previously applied on a widget
        '''
        props = self._widgets.pop(widget, None)
        if props:
            self.dispatch('on_complete', widget)
        self._clock_uninstall()
        if not self._widgets:
            self._unregister()

    def stop_property(self, widget, prop):
        '''Even if an animation is running, remove a property. It will not be
        animated further.
        '''
        props = self._widgets.get(widget, None)
        if not props:
            return
        props['properties'].pop(prop, None)

        # no more properties to animation ? kill the animation.
        if not props['properties']:
            self.stop(widget)

    #
    # Private
    #
    def _register(self):
        Animation._instances.add(self)

    def _unregister(self):
        if self in Animation._instances:
            Animation._instances.remove(self)

    def _initialize(self, widget):
        d = self._widgets[widget] = {
            'properties': {},
            'time': 0.}

        # get current values
        p = d['properties']
        for key, value in self._animated_properties.iteritems():
            p[key] = (getattr(widget, key), value)

        # install clock
        self._clock_install()

    def _clock_install(self):
        if self._clock_installed:
            return
        Clock.schedule_interval(self._update, 1 / 60.)
        self._clock_installed = True

    def _clock_uninstall(self):
        if self._widgets or not self._clock_installed:
            return
        self._clock_installed = False
        Clock.unschedule(self._update)

    def _update(self, dt):
        widgets = self._widgets
        transition = self._transition
        calculate = self._calculate
        for widget in widgets.keys()[:]:
            anim = widgets[widget]
            anim['time'] += dt

            # calculate progression
            progress = min(1., anim['time'] / self._duration)
            t = transition(progress)

            # apply progression on widget
            for key, values in anim['properties'].iteritems():
                a, b = values
                value = calculate(a, b, t)
                setattr(widget, key, value)

            self.dispatch('on_progress', widget, progress)

            # time to stop ?
            if progress >= 1.:
                self.stop(widget)

    def _calculate(self, a, b, t):
        _calculate = self._calculate
        if isinstance(a, ListType) or isinstance(a, TupleType):
            if isinstance(a, ListType):
                tp = list
            else:
                tp = tuple
            return tp([_calculate(a[x], b[x], t) for x in xrange(len(a))])
        elif isinstance(a, DictType):
            d = {}
            for x in a.iterkeys():
                if not x in b.keys():
                    # User requested to animate only part of the dict.
                    # Copy the rest
                    d[x] = a[x]
                else:
                    d[x] = _calculate(a[x], b[x], t)
            return d
        else:
            return (a * (1. - t)) + (b * t)

    #
    # Default handlers
    #
    def on_start(self, widget):
        pass

    def on_progress(self, widget, progress):
        pass

    def on_complete(self, widget):
        pass

    def __add__(self, animation):
        return Sequence(self, animation)

    def __and__(self, animation):
        return Parallel(self, animation)


class Sequence(Animation):

    def __init__(self, anim1, anim2):
        super(Sequence, self).__init__()
        self.anim1 = anim1
        self.anim2 = anim2

        self.anim1.bind(on_start=self.on_anim1_start,
                        on_complete=self.on_anim1_complete,
                        on_progress=self.on_anim1_progress)
        self.anim2.bind(on_complete=self.on_anim2_complete,
                        on_progress=self.on_anim2_progress)

    @property
    def duration(self):
        return self.anim1.duration + self.anim2.duration

    def start(self, widget):
        self.stop(widget)
        self.anim1.start(widget)
        self._widgets[widget] = True
        self._register()

    def stop(self, widget):
        self.anim1.stop(widget)
        self.anim2.stop(widget)
        self._widgets.pop(widget, None)
        if not self._widgets:
            self._unregister()

    def on_anim1_start(self, instance, widget):
        self.dispatch('on_start', widget)

    def on_anim1_complete(self, instance, widget):
        self.anim2.start(widget)

    def on_anim1_progress(self, instance, widget, progress):
        self.dispatch('on_progress', widget, progress / 2.)

    def on_anim2_complete(self, instance, widget):
        self.dispatch('on_complete', widget)

    def on_anim2_progress(self, instance, widget, progress):
        self.dispatch('on_progress', widget, .5 + progress / 2.)


class Parallel(Animation):

    def __init__(self, anim1, anim2):
        super(Parallel, self).__init__()
        self.anim1 = anim1
        self.anim2 = anim2

        self.anim1.bind(on_complete=self.on_anim_complete)
        self.anim2.bind(on_complete=self.on_anim_complete)

    @property
    def duration(self):
        return max(self.anim1.duration, self.anim2.duration)

    def start(self, widget):
        self.stop(widget)
        self.anim1.start(widget)
        self.anim2.start(widget)
        self._widgets[widget] = {'complete': 0}
        self._register()
        self.dispatch('on_start', widget)

    def stop(self, widget):
        self.anim1.stop(widget)
        self.anim2.stop(widget)
        self._widgets.pop(widget, None)
        if not self._widgets:
            self._unregister()

    def on_anim_complete(self, instance, widget):
        self._widgets[widget]['complete'] += 1
        if self._widgets[widget]['complete'] == 2:
            self.dispatch('on_complete', widget)


class AnimationTransition(object):
    '''Collection of animation function, to be used with Animation object.
    Easing Functions ported into Kivy from Clutter Project
    http://www.clutter-project.org/docs/clutter/stable/ClutterAlpha.html

    `progress` parameter in each animation functions is between 0-1 range.
    '''

    @staticmethod
    def linear(progress):
        '''.. image:: images/anim_linear.png'''
        return progress

    @staticmethod
    def in_quad(progress):
        '''.. image:: images/anim_in_quad.png
        '''
        return progress * progress

    @staticmethod
    def out_quad(progress):
        '''.. image:: images/anim_out_quad.png
        '''
        return -1.0 * progress * (progress - 2.0)

    @staticmethod
    def in_out_quad(progress):
        '''.. image:: images/anim_in_out_quad.png
        '''
        p = progress * 2
        if p < 1:
            return 0.5 * p * p
        p -= 1.0
        return -0.5 * (p * (p - 2.0) - 1.0)

    @staticmethod
    def in_cubic(progress):
        '''.. image:: images/anim_in_cubic.png
        '''
        return progress * progress * progress

    @staticmethod
    def out_cubic(progress):
        '''.. image:: images/anim_out_cubic.png
        '''
        p = progress - 1.0
        return p * p * p + 1.0

    @staticmethod
    def in_out_cubic(progress):
        '''.. image:: images/anim_in_out_cubic.png
        '''
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p
        p -= 2
        return 0.5 * (p * p * p + 2.0)

    @staticmethod
    def in_quart(progress):
        '''.. image:: images/anim_in_quart.png
        '''
        return progress * progress * progress * progress

    @staticmethod
    def out_quart(progress):
        '''.. image:: images/anim_out_quart.png
        '''
        p = progress - 1.0
        return -1.0 * (p * p * p * p - 1.0)

    @staticmethod
    def in_out_quart(progress):
        '''.. image:: images/anim_in_out_quart.png
        '''
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p
        p -= 2
        return -0.5 * (p * p * p * p - 2.0)

    @staticmethod
    def in_quint(progress):
        '''.. image:: images/anim_in_quint.png
        '''
        return progress * progress * progress * progress * progress

    @staticmethod
    def out_quint(progress):
        '''.. image:: images/anim_out_quint.png
        '''
        p = progress - 1.0
        return p * p * p * p * p + 1.0

    @staticmethod
    def in_out_quint(progress):
        '''.. image:: images/anim_in_out_quint.png
        '''
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p * p
        p -= 2.0
        return 0.5 * (p * p * p * p * p + 2.0)

    @staticmethod
    def in_sine(progress):
        '''.. image:: images/anim_in_sine.png
        '''
        return -1.0 * cos(progress * (pi/2.0)) + 1.0

    @staticmethod
    def out_sine(progress):
        '''.. image:: images/anim_out_sine.png
        '''
        return sin(progress * (pi/2.0))

    @staticmethod
    def in_out_sine(progress):
        '''.. image:: images/anim_in_out_sine.png
        '''
        return -0.5 * (cos(pi * progress) - 1.0)

    @staticmethod
    def in_expo(progress):
        '''.. image:: images/anim_in_expo.png
        '''
        if progress == 0:
            return 0.0
        return pow(2, 10 * (progress - 1.0))

    @staticmethod
    def out_expo(progress):
        '''.. image:: images/anim_out_expo.png
        '''
        if progress == 1.0:
            return 1.0
        return -pow(2, -10 * progress) + 1.0

    @staticmethod
    def in_out_expo(progress):
        '''.. image:: images/anim_in_out_expo.png
        '''
        if progress == 0:
            return 0.0
        if progress == 1.:
            return 1.0
        p = progress * 2
        if p < 1:
            return 0.5 * pow(2, 10 * (p - 1.0))
        p -= 1.0
        return 0.5 * (-pow(2, -10 * p) + 2.0)

    @staticmethod
    def in_circ(progress):
        '''.. image:: images/anim_in_circ.png
        '''
        return -1.0 * (sqrt(1.0 - progress * progress) - 1.0)

    @staticmethod
    def out_circ(progress):
        '''.. image:: images/anim_out_circ.png
        '''
        p = progress - 1.0
        return sqrt(1.0 - p * p)

    @staticmethod
    def in_out_circ(progress):
        '''.. image:: images/anim_in_out_circ.png
        '''
        p = progress * 2
        if p < 1:
            return -0.5 * (sqrt(1.0 - p * p) - 1.0)
        p -= 2.0
        return 0.5 * (sqrt(1.0 - p * p) + 1.0)

    @staticmethod
    def in_elastic(progress):
        '''.. image:: images/anim_in_elastic.png
        '''
        p = .3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        q -= 1.0
        return -(pow(2, 10 * q) * sin((q - s) * (2 * pi) / p))

    @staticmethod
    def out_elastic(progress):
        '''.. image:: images/anim_out_elastic.png
        '''
        p = .3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        return pow(2, -10 * q) * sin((q - s) * (2 * pi) / p) + 1.0

    @staticmethod
    def in_out_elastic(progress):
        '''.. image:: images/anim_in_out_elastic.png
        '''
        p = .3 * 1.5
        s = p / 4.0
        q = progress * 2
        if q == 2:
            return 1.0
        if q < 1:
            q -= 1.0
            return -.5 * (pow(2, 10 * q) * sin((q - s) * (2.0 *pi) / p))
        else:
            q -= 1.0
            return pow(2, -10 * q) * sin((q - s) * (2.0 * pi) / p) * .5 + 1.0

    @staticmethod
    def in_back(progress):
        '''.. image:: images/anim_in_back.png
        '''
        return progress * progress * ((1.70158 + 1.0) * progress - 1.70158)

    @staticmethod
    def out_back(progress):
        '''.. image:: images/anim_out_back.png
        '''
        p = progress - 1.0
        return p * p * ((1.70158 + 1) * p + 1.70158) + 1.0

    @staticmethod
    def in_out_back(progress):
        '''.. image:: images/anim_in_out_back.png
        '''
        p = progress * 2.
        s = 1.70158 * 1.525
        if p < 1:
            return 0.5 * (p * p * ((s + 1.0) * p - s))
        p -= 2.0
        return 0.5 * (p * p * ((s + 1.0) * p + s) + 2.0)

    @staticmethod
    def _out_bounce_internal(t, d):
        p = t / d
        if p < (1.0 / 2.75):
            return 7.5625 * p * p
        elif p < (2.0 / 2.75):
            p -= (1.5 / 2.75)
            return 7.5625 * p * p + .75
        elif p < (2.5 / 2.75):
            p -= (2.25 / 2.75)
            return 7.5625 * p * p + .9375
        else:
            p -= (2.625 / 2.75)
            return 7.5625 * p * p + .984375

    @staticmethod
    def _in_bounce_internal(t, d):
        return 1.0 - AnimationTransition._out_bounce_internal(d - t, d)

    @staticmethod
    def in_bounce(progress):
        '''.. image:: images/anim_in_bounce.png
        '''
        return AnimationTransition._in_bounce_internal(progress, 1.)

    @staticmethod
    def out_bounce(progress):
        '''.. image:: images/anim_out_bounce.png
        '''
        return AnimationTransition._out_bounce_internal(progress, 1.)

    @staticmethod
    def in_out_bounce(progress):
        '''.. image:: images/anim_in_out_bounce.png
        '''
        p = progress * 2.
        if p < 1.:
            return AnimationTransition._in_bounce_internal(p, 1.) * .5
        return AnimationTransition._out_bounce_internal(p - 1., 1.) * .5 + .5

