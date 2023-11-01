'''
Animations tests
================
'''
import pytest


@pytest.fixture(scope='module')
def ec_cls():
    class EventCounter:
        def __init__(self, anim):
            self.n_start = 0
            self.n_progress = 0
            self.n_complete = 0
            anim.bind(on_start=self.on_start,
                      on_progress=self.on_progress,
                      on_complete=self.on_complete)

        def on_start(self, anim, widget):
            self.n_start += 1

        def on_progress(self, anim, widget, progress):
            self.n_progress += 1

        def on_complete(self, anim, widget):
            self.n_complete += 1

        def assert_(self, n_start, n_progress_greater_than_zero, n_complete):
            assert self.n_start == n_start
            if n_progress_greater_than_zero:
                assert self.n_progress > 0
            else:
                assert self.n_progress == 0
            assert self.n_complete == n_complete
    return EventCounter


@pytest.fixture(autouse=True)
def cleanup():
    from kivy.animation import Animation
    Animation.cancel_all(None)


def no_animations_being_played():
    from kivy.animation import Animation
    return len(Animation._instances) == 0


def sleep(t):
    from time import time, sleep
    from kivy.clock import Clock
    tick = Clock.tick
    deadline = time() + t
    while time() < deadline:
        sleep(.01)
        tick()


class TestAnimation:

    def test_start_animation(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100, d=1)
        w = Widget()
        a.start(w)
        sleep(1.5)
        assert w.x == pytest.approx(100)
        assert no_animations_being_played()

    def test_animation_duration_0(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100, d=0)
        w = Widget()
        a.start(w)
        sleep(.5)
        assert no_animations_being_played()

    def test_cancel_all(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a1 = Animation(x=100)
        a2 = Animation(y=100)
        w1 = Widget()
        w2 = Widget()
        a1.start(w1)
        a1.start(w2)
        a2.start(w1)
        a2.start(w2)
        assert not no_animations_being_played()
        Animation.cancel_all(None)
        assert no_animations_being_played()

    def test_cancel_all_2(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a1 = Animation(x=100)
        a2 = Animation(y=100)
        w1 = Widget()
        w2 = Widget()
        a1.start(w1)
        a1.start(w2)
        a2.start(w1)
        a2.start(w2)
        assert not no_animations_being_played()
        Animation.cancel_all(None, 'x', 'z')
        assert not no_animations_being_played()
        Animation.cancel_all(None, 'y')
        assert no_animations_being_played()

    def test_stop_animation(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100, d=1)
        w = Widget()
        a.start(w)
        sleep(.5)
        a.stop(w)
        assert w.x != pytest.approx(100)
        assert w.x != pytest.approx(0)
        assert no_animations_being_played()

    def test_stop_all(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100, d=1)
        w = Widget()
        a.start(w)
        sleep(.5)
        Animation.stop_all(w)
        assert no_animations_being_played()

    def test_stop_all_2(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100, d=1)
        w = Widget()
        a.start(w)
        sleep(.5)
        Animation.stop_all(w, 'x')
        assert no_animations_being_played()

    def test_duration(self):
        from kivy.animation import Animation
        a = Animation(x=100, d=1)
        assert a.duration == 1

    def test_transition(self):
        from kivy.animation import Animation, AnimationTransition
        a = Animation(x=100, t='out_bounce')
        assert a.transition is AnimationTransition.out_bounce

    def test_animated_properties(self):
        from kivy.animation import Animation
        a = Animation(x=100)
        assert a.animated_properties == {'x': 100, }

    def test_animated_instruction(self):
        from kivy.graphics import Scale
        from kivy.animation import Animation
        a = Animation(x=100, d=1)
        instruction = Scale(3, 3, 3)
        a.start(instruction)
        assert a.animated_properties == {'x': 100, }
        assert instruction.x == pytest.approx(3)
        sleep(1.5)
        assert instruction.x == pytest.approx(100)
        assert no_animations_being_played()

    def test_weakref(self):
        import gc
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        w = Widget()
        a = Animation(x=100)
        a.start(w.proxy_ref)
        del w
        gc.collect()
        try:
            sleep(1.)
        except ReferenceError:
            pass
        assert no_animations_being_played()


class TestSequence:

    def test_cancel_all(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100) + Animation(x=0)
        w = Widget()
        a.start(w)
        sleep(.5)
        Animation.cancel_all(w)
        assert no_animations_being_played()

    def test_cancel_all_2(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100) + Animation(x=0)
        w = Widget()
        a.start(w)
        sleep(.5)
        Animation.cancel_all(w, 'x')
        assert no_animations_being_played()

    def test_stop_all(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100) + Animation(x=0)
        w = Widget()
        a.start(w)
        sleep(.5)
        Animation.stop_all(w)
        assert no_animations_being_played()

    def test_stop_all_2(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100) + Animation(x=0)
        w = Widget()
        a.start(w)
        sleep(.5)
        Animation.stop_all(w, 'x')
        assert no_animations_being_played()

    def test_count_events(self, ec_cls):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100, d=.5) + Animation(x=0, d=.5)
        w = Widget()
        ec = ec_cls(a)
        ec1 = ec_cls(a.anim1)
        ec2 = ec_cls(a.anim2)
        a.start(w)

        # right after the animation starts
        ec.assert_(1, False, 0)
        ec1.assert_(1, False, 0)
        ec2.assert_(0, False, 0)
        sleep(.2)

        # during the first half of the animation
        ec.assert_(1, True, 0)
        ec1.assert_(1, True, 0)
        ec2.assert_(0, False, 0)
        sleep(.5)

        # during the second half of the animation
        ec.assert_(1, True, 0)
        ec1.assert_(1, True, 1)
        ec2.assert_(1, True, 0)
        sleep(.5)

        # after the animation completed
        ec.assert_(1, True, 1)
        ec1.assert_(1, True, 1)
        ec2.assert_(1, True, 1)
        assert no_animations_being_played()

    def test_have_properties_to_animate(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100) + Animation(x=0)
        w = Widget()
        assert not a.have_properties_to_animate(w)
        a.start(w)
        assert a.have_properties_to_animate(w)
        a.stop(w)
        assert not a.have_properties_to_animate(w)
        assert no_animations_being_played()

    def test_animated_properties(self):
        from kivy.animation import Animation
        a = Animation(x=100, y=200) + Animation(x=0)
        assert a.animated_properties == {'x': 0, 'y': 200, }

    def test_transition(self):
        from kivy.animation import Animation
        a = Animation(x=100) + Animation(x=0)
        with pytest.raises(AttributeError):
            a.transition


class TestRepetitiveSequence:

    def test_stop(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100) + Animation(x=0)
        a.repeat = True
        w = Widget()
        a.start(w)
        a.stop(w)
        assert no_animations_being_played()

    def test_count_events(self, ec_cls):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100, d=.5) + Animation(x=0, d=.5)
        a.repeat = True
        w = Widget()
        ec = ec_cls(a)
        ec1 = ec_cls(a.anim1)
        ec2 = ec_cls(a.anim2)
        a.start(w)

        # right after the animation starts
        ec.assert_(1, False, 0)
        ec1.assert_(1, False, 0)
        ec2.assert_(0, False, 0)
        sleep(.2)

        # during the first half of the first round of the animation
        ec.assert_(1, True, 0)
        ec1.assert_(1, True, 0)
        ec2.assert_(0, False, 0)
        sleep(.5)

        # during the second half of the first round of the animation
        ec.assert_(1, True, 0)
        ec1.assert_(1, True, 1)
        ec2.assert_(1, True, 0)
        sleep(.5)

        # during the first half of the second round of the animation
        ec.assert_(1, True, 0)
        ec1.assert_(2, True, 1)
        ec2.assert_(1, True, 1)
        sleep(.5)

        # during the second half of the second round of the animation
        ec.assert_(1, True, 0)
        ec1.assert_(2, True, 2)
        ec2.assert_(2, True, 1)
        a.stop(w)

        # after the animation stopped
        ec.assert_(1, True, 1)
        ec1.assert_(2, True, 2)
        ec2.assert_(2, True, 2)
        assert no_animations_being_played()


class TestParallel:

    def test_have_properties_to_animate(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100) & Animation(y=100)
        w = Widget()
        assert not a.have_properties_to_animate(w)
        a.start(w)
        assert a.have_properties_to_animate(w)
        a.stop(w)
        assert not a.have_properties_to_animate(w)
        assert no_animations_being_played()

    def test_cancel_property(self):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100) & Animation(y=100)
        w = Widget()
        a.start(w)
        a.cancel_property(w, 'x')
        assert not no_animations_being_played()
        a.stop(w)
        assert no_animations_being_played()

    def test_animated_properties(self):
        from kivy.animation import Animation
        a = Animation(x=100) & Animation(y=100)
        assert a.animated_properties == {'x': 100, 'y': 100, }

    def test_transition(self):
        from kivy.animation import Animation
        a = Animation(x=100) & Animation(y=100)
        with pytest.raises(AttributeError):
            a.transition

    def test_count_events(self, ec_cls):
        from kivy.animation import Animation
        from kivy.uix.widget import Widget
        a = Animation(x=100) & Animation(y=100, d=.5)
        w = Widget()
        ec = ec_cls(a)
        ec1 = ec_cls(a.anim1)
        ec2 = ec_cls(a.anim2)
        a.start(w)

        # right after the animation started
        ec.assert_(1, False, 0)
        ec1.assert_(1, False, 0)
        ec2.assert_(1, False, 0)
        sleep(.2)

        # during the first half of the animation
        ec.assert_(1, False, 0)  # n_progress is still 0 !!
        ec1.assert_(1, True, 0)
        ec2.assert_(1, True, 0)
        sleep(.5)

        # during the second half of the animation
        ec.assert_(1, False, 0)  # n_progress is still 0 !!
        ec1.assert_(1, True, 0)
        ec2.assert_(1, True, 1)
        sleep(.5)

        # after the animation compeleted
        ec.assert_(1, False, 1)  # n_progress is still 0 !
        ec1.assert_(1, True, 1)
        ec2.assert_(1, True, 1)
        assert no_animations_being_played()
