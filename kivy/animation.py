'''
Animation
=========

These classes are intended to be used on a :class:`~kivy.uix.widget.Widget`.
If you want to add animations to your application,
you need to follow two steps:

    * First, setup the animation object
    * Then, use the animation on one or multiple widgets

Simple animation
----------------

You can animate multiple properties at the same time, with custom transition
function. Here is an example to animate the widget on a custom position and
size, using 'in_quad' transition ::

    widget = Widget()
    animation = Animation(x=50, size=(80, 80), t='in_quad')
    animation.start(widget)

Sequential animation
--------------------

Multiple animation can be added. The result will be animated in sequential ::

    widget = Widget()
    animation = Animation(x=50) + Animation(size=(80, 80))
    animation.start(widget)

Parallel animation
------------------

You can join one or multiple animation in parallel. This can be used when you
want to use differents settings for each properties ::

    widget = Widget()
    animation = Animation(pos=(80, 10))
    animation &= Animation(size=(800, 800), duration=2.)

'''

__all__ = ('Animation', 'AnimationTransition')

from types import ListType, TupleType, DictType
from math import sqrt, cos, sin, pi
from kivy.event import EventDispatcher
from kivy.clock import Clock


class Animation(EventDispatcher):
    '''Create an animation definition, that can be used to animate a widget

    :Parameters:
        `duration` or `d`: float, default to 1.
            Duration of the animation
        `transition` or `t`: str or func
            Transition function for animate properties

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
        super(Animation, self).__init__()

        # Register events
        self.register_event_type('on_start')
        self.register_event_type('on_progress')
        self.register_event_type('on_complete')

        # Initialize
        self._clock_installed = False
        self._duration = kw.get('d', kw.get('duration', 1.))
        self._transition = kw.get('t', kw.get('transition', 'linear'))
        if isinstance(self._transition, basestring):
            self._transition = getattr(AnimationTransition, self._transition)
        for key in ('d', 't', 'duration', 'transition'):
            kw.pop(key, None)
        self._properties = kw
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
    def properties(self):
        '''Return the properties used to animate
        '''
        return self._properties

    @staticmethod
    def stop_all(widget, *largs):
        '''Stop all animations that concern a specific widget / list of
        properties.

        Example ::

            widget = Widget()
            animation = Animation(x=50)
            animation.start(widget)

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
        '''Even if a animation is going, remove a property for beeing animated.
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
        for key, value in self._properties.iteritems():
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
            return type(a)([_calculate(a[x], b[x], t) for x in xrange(len(a))])
        elif isinstance(a, DictType):
            return dict(zip(a.keys(),
                            [_calculate(a[x], b[x], t) for x in a.iterkeys()]))
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
    '''

    @staticmethod
    def linear(progress):
        return progress

    @staticmethod
    def in_quad(progress):
        return progress * progress

    @staticmethod
    def out_quad(progress):
        return -1.0 * progress * (progress - 2.0)

    @staticmethod
    def in_out_quad(progress):
        p = progress * 2
        if p < 1:
            return 0.5 * p * p
        p -= 1.0
        return -0.5 * (p * (p - 2.0) - 1.0)

    @staticmethod
    def in_cubic(progress):
        return progress * progress * progress

    @staticmethod
    def out_cubic(progress):
        p = progress - 1.0
        return p * p * p + 1.0

    @staticmethod
    def in_out_cubic(progress):
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p
        p -= 2
        return 0.5 * (p * p * p + 2.0)

    @staticmethod
    def in_quart(progress):
        return progress * progress * progress * progress

    @staticmethod
    def out_quart(progress):
        p = progress - 1.0
        return -1.0 * (p * p * p * p - 1.0)

    @staticmethod
    def in_out_quart(progress):
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p
        p -= 2
        return -0.5 * (p * p * p * p - 2.0)

    @staticmethod
    def in_quint(progress):
        return progress * progress * progress * progress * progress

    @staticmethod
    def out_quint(progress):
        p = progress - 1.0
        return p * p * p * p * p + 1.0

    @staticmethod
    def in_out_quint(progress):
        p = progress * 2
        if p < 1:
            return 0.5 * p * p * p * p * p
        p -= 2.0
        return 0.5 * (p * p * p * p * p + 2.0)

    @staticmethod
    def in_sine(progress):
        return -1.0 * cos(progress * (pi/2.0)) + 1.0

    @staticmethod
    def out_sine(progress):
        return sin(progress * (pi/2.0))

    @staticmethod
    def in_out_sine(progress):
        return -0.5 * (cos(pi * progress) - 1.0)

    @staticmethod
    def in_expo(progress):
        if progress == 0:
            return 0.0
        return pow(2, 10 * (progress - 1.0))

    @staticmethod
    def out_expo(progress):
        if progress == 1.0:
            return 1.0
        return -pow(2, -10 * progress) + 1.0

    @staticmethod
    def in_out_expo(progress):
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
        return -1.0 * (sqrt(1.0 - progress * progress) - 1.0)

    @staticmethod
    def out_circ(progress):
        p = progress - 1.0
        return sqrt(1.0 - p * p)

    @staticmethod
    def in_out_circ(progress):
        p = progress * 2
        if p < 1:
            return -0.5 * (sqrt(1.0 - p * p) - 1.0)
        p -= 2.0
        return 0.5 * (sqrt(1.0 - p * p) + 1.0)

    @staticmethod
    def in_elastic(progress):
        p = .3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        q -= 1.0
        return -(pow(2, 10 * q) * sin((q - s) * (2 * pi) / p))

    @staticmethod
    def out_elastic(progress):
        p = .3
        s = p / 4.0
        q = progress
        if q == 1:
            return 1.0
        return pow(2, -10 * q) * sin((q - s) * (2 * pi) / p) + 1.0

    @staticmethod
    def in_out_elastic(progress):
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
        return progress * progress * ((1.70158 + 1.0) * progress - 1.70158)

    @staticmethod
    def out_back(progress):
        p = progress - 1.0
        return p * p * ((1.70158 + 1) * p + 1.70158) + 1.0

    @staticmethod
    def in_out_back(progress):
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
        return AnimationTransition._in_bounce_internal(progress, 1.)

    @staticmethod
    def out_bounce(progress):
        return AnimationTransition._out_bounce_internal(progress, 1.)

    @staticmethod
    def in_out_bounce(progress):
        p = progress * 2.
        if p < 1.:
            return AnimationTransition._in_bounce_internal(p, 1.) * .5
        return AnimationTransition._out_bounce_internal(p - 1., 1.) * .5 + .5

