'''
Animation
=========

:class:`Animation` and :class:`AnimationTransition` are used to animate
:class:`~kivy.uix.widget.Widget` properties. You must specify at least a
property name and target value. To use an Animation, follow these steps:

    * Setup an Animation object
    * Use the Animation object on a Widget

Simple animation
----------------

To animate a Widget's x or y position, simply specify the target x/y values
where you want the widget positioned at the end of the animation::

    anim = Animation(x=100, y=100)
    anim.start(widget)

The animation will last for 1 second unless :attr:`duration` is specified.
When anim.start() is called, the Widget will move smoothly from the current
x/y position to (100, 100).

Multiple properties and transitions
-----------------------------------

You can animate multiple properties and use built-in or custom transition
functions using :attr:`transition` (or the `t=` shortcut). For example,
to animate the position and size using the 'in_quad' transition::

    anim = Animation(x=50, size=(80, 80), t='in_quad')
    anim.start(widget)

Note that the `t=` parameter can be the string name of a method in the
:class:`AnimationTransition` class or your own animation function.

Sequential animation
--------------------

To join animations sequentially, use the '+' operator. The following example
will animate to x=50 over 1 second, then animate the size to (80, 80) over the
next two seconds::

    anim = Animation(x=50) + Animation(size=(80, 80), duration=2.)
    anim.start(widget)

Parallel animation
------------------

To join animations in parallel, use the '&' operator. The following example
will animate the position to (80, 10) over 1 second, whilst in parallel
animating the size to (800, 800)::

    anim = Animation(pos=(80, 10))
    anim &= Animation(size=(800, 800), duration=2.)
    anim.start(widget)

Keep in mind that creating overlapping animations on the same property may have
unexpected results. If you want to apply multiple animations to the same
property, you should either schedule them sequentially (via the '+' operator or
using the *on_complete* callback) or cancel previous animations using the
:attr:`~Animation.cancel_all` method.

Repeating animation
-------------------

.. versionadded:: 1.8.0

.. note::
    This is currently only implemented for 'Sequence' animations.

To set an animation to repeat, simply set the :attr:`Sequence.repeat`
property to `True`::

    anim = Animation(...) + Animation(...)
    anim.repeat = True
    anim.start(widget)

For flow control of animations such as stopping and cancelling, use the methods
already in place in the animation module.
'''

__all__ = ('Animation', 'AnimationTransition')

from math import sqrt, cos, sin, pi
from collections import ChainMap
from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.compat import string_types, iterkeys
from kivy.weakproxy import WeakProxy


class Animation(EventDispatcher):
    '''Create an animation definition that can be used to animate a Widget.

    :Parameters:
        `duration` or `d`: float, defaults to 1.
            Duration of the animation, in seconds.
        `transition` or `t`: str or func
            Transition function for animate properties. It can be the name of a
            method from :class:`AnimationTransition`.
        `step` or `s`: float
            Step in milliseconds of the animation. Defaults to 0, which means
            the animation is updated for every frame.

            To update the animation less often, set the step value to a float.
            For example, if you want to animate at 30 FPS, use s=1/30.

    :Events:
        `on_start`: animation, widget
            Fired when the animation is started on a widget.
        `on_complete`: animation, widget
            Fired when the animation is completed or stopped on a widget.
        `on_progress`: animation, widget, progression
            Fired when the progression of the animation is changing.

    .. versionchanged:: 1.4.0
        Added s/step parameter.

    .. versionchanged:: 1.10.0
        The default value of the step parameter was changed from 1/60. to 0.
    '''

    _update_ev = None

    _instances = set()

    __events__ = ('on_start', 'on_progress', 'on_complete')

    def __init__(self, **kw):
        super().__init__()
        # Initialize
        self._clock_installed = False
        self._duration = kw.pop('d', kw.pop('duration', 1.))
        self._transition = kw.pop('t', kw.pop('transition', 'linear'))
        self._step = kw.pop('s', kw.pop('step', 0))
        if isinstance(self._transition, string_types):
            self._transition = getattr(AnimationTransition, self._transition)
        self._animated_properties = kw
        self._widgets = {}

    @property
    def duration(self):
        '''Return the duration of the animation.
        '''
        return self._duration

    @property
    def transition(self):
        '''Return the transition of the animation.
        '''
        return self._transition

    @property
    def animated_properties(self):
        '''Return the properties used to animate.
        '''
        return self._animated_properties

    @staticmethod
    def stop_all(widget, *largs):
        '''Stop all animations that concern a specific widget / list of
        properties.

        Example::

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
            for animation in set(Animation._instances):
                animation.stop(widget)

    @staticmethod
    def cancel_all(widget, *largs):
        '''Cancel all animations that concern a specific widget / list of
        properties. See :attr:`cancel`.

        Example::

            anim = Animation(x=50)
            anim.start(widget)

            # and later
            Animation.cancel_all(widget, 'x')

        .. versionadded:: 1.4.0

        .. versionchanged:: 2.1.0
            If the parameter ``widget`` is None, all animated widgets will be
            the target and cancelled. If ``largs`` is also given, animation of
            these properties will be canceled for all animated widgets.
        '''
        if widget is None:
            if largs:
                for animation in Animation._instances.copy():
                    for info in tuple(animation._widgets.values()):
                        widget = info['widget']
                        for x in largs:
                            animation.cancel_property(widget, x)
            else:
                for animation in Animation._instances:
                    animation._widgets.clear()
                    animation._clock_uninstall()
                Animation._instances.clear()
            return
        if len(largs):
            for animation in list(Animation._instances):
                for x in largs:
                    animation.cancel_property(widget, x)
        else:
            for animation in set(Animation._instances):
                animation.cancel(widget)

    def start(self, widget):
        '''Start the animation on a widget.
        '''
        self.stop(widget)
        self._initialize(widget)
        self._register()
        self.dispatch('on_start', widget)

    def stop(self, widget):
        '''Stop the animation previously applied to a widget, triggering the
        `on_complete` event.'''
        props = self._widgets.pop(widget.uid, None)
        if props:
            self.dispatch('on_complete', widget)
        self.cancel(widget)

    def cancel(self, widget):
        '''Cancel the animation previously applied to a widget. Same
        effect as :attr:`stop`, except the `on_complete` event will
        *not* be triggered!

        .. versionadded:: 1.4.0
        '''
        self._widgets.pop(widget.uid, None)
        self._clock_uninstall()
        if not self._widgets:
            self._unregister()

    def stop_property(self, widget, prop):
        '''Even if an animation is running, remove a property. It will not be
        animated further. If it was the only/last property being animated,
        the animation will be stopped (see :attr:`stop`).
        '''
        props = self._widgets.get(widget.uid, None)
        if not props:
            return
        props['properties'].pop(prop, None)

        # no more properties to animation ? kill the animation.
        if not props['properties']:
            self.stop(widget)

    def cancel_property(self, widget, prop):
        '''Even if an animation is running, remove a property. It will not be
        animated further. If it was the only/last property being animated,
        the animation will be canceled (see :attr:`cancel`)

        .. versionadded:: 1.4.0
        '''
        props = self._widgets.get(widget.uid, None)
        if not props:
            return
        props['properties'].pop(prop, None)

        # no more properties to animation ? kill the animation.
        if not props['properties']:
            self.cancel(widget)

    def have_properties_to_animate(self, widget):
        '''Return True if a widget still has properties to animate.

        .. versionadded:: 1.8.0
        '''
        props = self._widgets.get(widget.uid, None)
        if props and props['properties']:
            return True

    #
    # Private
    #
    def _register(self):
        Animation._instances.add(self)

    def _unregister(self):
        Animation._instances.discard(self)

    def _initialize(self, widget):
        d = self._widgets[widget.uid] = {
            'widget': widget,
            'properties': {},
            'time': None}

        # get current values
        p = d['properties']
        for key, value in self._animated_properties.items():
            original_value = getattr(widget, key)
            if isinstance(original_value, (tuple, list)):
                original_value = original_value[:]
            elif isinstance(original_value, dict):
                original_value = original_value.copy()
            p[key] = (original_value, value)

        # install clock
        self._clock_install()

    def _clock_install(self):
        if self._clock_installed:
            return
        self._update_ev = Clock.schedule_interval(self._update, self._step)
        self._clock_installed = True

    def _clock_uninstall(self):
        if self._widgets or not self._clock_installed:
            return
        self._clock_installed = False
        if self._update_ev is not None:
            self._update_ev.cancel()
            self._update_ev = None

    def _update(self, dt):
        widgets = self._widgets
        transition = self._transition
        calculate = self._calculate
        for uid in list(widgets.keys()):
            anim = widgets[uid]
            widget = anim['widget']

            if isinstance(widget, WeakProxy) and not len(dir(widget)):
                # empty proxy, widget is gone. ref: #2458
                self._widgets.pop(uid, None)
                self._clock_uninstall()
                if not self._widgets:
                    self._unregister()
                continue

            if anim['time'] is None:
                anim['time'] = 0.
            else:
                anim['time'] += dt

            # calculate progression
            if self._duration:
                progress = min(1., anim['time'] / self._duration)
            else:
                progress = 1
            t = transition(progress)

            # apply progression on widget
            for key, values in anim['properties'].items():
                a, b = values
                value = calculate(a, b, t)
                setattr(widget, key, value)

            self.dispatch('on_progress', widget, progress)

            # time to stop ?
            if progress >= 1.:
                self.stop(widget)

    def _calculate(self, a, b, t):
        _calculate = self._calculate
        if isinstance(a, list) or isinstance(a, tuple):
            if isinstance(a, list):
                tp = list
            else:
                tp = tuple
            return tp([_calculate(a[x], b[x], t) for x in range(len(a))])
        elif isinstance(a, dict):
            d = {}
            for x in iterkeys(a):
                if x not in b:
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


class CompoundAnimation(Animation):

    def stop_property(self, widget, prop):
        self.anim1.stop_property(widget, prop)
        self.anim2.stop_property(widget, prop)
        if (not self.anim1.have_properties_to_animate(widget) and
                not self.anim2.have_properties_to_animate(widget)):
            self.stop(widget)

    def cancel(self, widget):
        self.anim1.cancel(widget)
        self.anim2.cancel(widget)
        super().cancel(widget)

    def cancel_property(self, widget, prop):
        '''Even if an animation is running, remove a property. It will not be
        animated further. If it was the only/last property being animated,
        the animation will be canceled (see :attr:`cancel`)

        This method overrides `:class:kivy.animation.Animation`'s
        version, to cancel it on all animations of the Sequence.

        .. versionadded:: 1.10.0
        '''
        self.anim1.cancel_property(widget, prop)
        self.anim2.cancel_property(widget, prop)
        if (not self.anim1.have_properties_to_animate(widget) and
                not self.anim2.have_properties_to_animate(widget)):
            self.cancel(widget)

    def have_properties_to_animate(self, widget):
        return (self.anim1.have_properties_to_animate(widget) or
                self.anim2.have_properties_to_animate(widget))

    @property
    def animated_properties(self):
        return ChainMap({},
                        self.anim2.animated_properties,
                        self.anim1.animated_properties)

    @property
    def transition(self):
        # This property is impossible to implement
        raise AttributeError(
            "Can't lookup transition attribute of a CompoundAnimation")


class Sequence(CompoundAnimation):

    def __init__(self, anim1, anim2):
        super().__init__()

        #: Repeat the sequence. See 'Repeating animation' in the header
        #: documentation.
        self.repeat = False

        self.anim1 = anim1
        self.anim2 = anim2

        self.anim1.bind(on_complete=self.on_anim1_complete,
                        on_progress=self.on_anim1_progress)
        self.anim2.bind(on_complete=self.on_anim2_complete,
                        on_progress=self.on_anim2_progress)

    @property
    def duration(self):
        return self.anim1.duration + self.anim2.duration

    def stop(self, widget):
        props = self._widgets.pop(widget.uid, None)
        self.anim1.stop(widget)
        self.anim2.stop(widget)
        if props:
            self.dispatch('on_complete', widget)
        super().cancel(widget)

    def start(self, widget):
        self.stop(widget)
        self._widgets[widget.uid] = True
        self._register()
        self.dispatch('on_start', widget)
        self.anim1.start(widget)

    def on_anim1_complete(self, instance, widget):
        if widget.uid not in self._widgets:
            return
        self.anim2.start(widget)

    def on_anim1_progress(self, instance, widget, progress):
        self.dispatch('on_progress', widget, progress / 2.)

    def on_anim2_complete(self, instance, widget):
        '''Repeating logic used with boolean variable "repeat".

        .. versionadded:: 1.7.1
        '''
        if widget.uid not in self._widgets:
            return
        if self.repeat:
            self.anim1.start(widget)
        else:
            self.dispatch('on_complete', widget)
            self.cancel(widget)

    def on_anim2_progress(self, instance, widget, progress):
        self.dispatch('on_progress', widget, .5 + progress / 2.)


class Parallel(CompoundAnimation):

    def __init__(self, anim1, anim2):
        super().__init__()
        self.anim1 = anim1
        self.anim2 = anim2

        self.anim1.bind(on_complete=self.on_anim_complete)
        self.anim2.bind(on_complete=self.on_anim_complete)

    @property
    def duration(self):
        return max(self.anim1.duration, self.anim2.duration)

    def stop(self, widget):
        self.anim1.stop(widget)
        self.anim2.stop(widget)
        if self._widgets.pop(widget.uid, None):
            self.dispatch('on_complete', widget)
        super().cancel(widget)

    def start(self, widget):
        self.stop(widget)
        self.anim1.start(widget)
        self.anim2.start(widget)
        self._widgets[widget.uid] = {'complete': 0}
        self._register()
        self.dispatch('on_start', widget)

    def on_anim_complete(self, instance, widget):
        self._widgets[widget.uid]['complete'] += 1
        if self._widgets[widget.uid]['complete'] == 2:
            self.stop(widget)


class AnimationTransition:
    '''Collection of animation functions to be used with the Animation object.
    Easing Functions ported to Kivy from the Clutter Project
    https://developer.gnome.org/clutter/stable/ClutterAlpha.html

    The `progress` parameter in each animation function is in the range 0-1.
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
        return -1.0 * cos(progress * (pi / 2.0)) + 1.0

    @staticmethod
    def out_sine(progress):
        '''.. image:: images/anim_out_sine.png
        '''
        return sin(progress * (pi / 2.0))

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
            return -.5 * (pow(2, 10 * q) * sin((q - s) * (2.0 * pi) / p))
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
