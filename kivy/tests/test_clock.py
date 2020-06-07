'''
Clock tests
===========
'''

import pytest


@pytest.fixture
def kivy_clock():
    from kivy.context import Context
    from kivy.clock import ClockBase

    context = Context(init=False)
    context['Clock'] = ClockBase()
    context.push()

    from kivy.clock import Clock
    Clock._max_fps = 0

    try:
        yield Clock
    finally:
        context.pop()


@pytest.fixture
def clock_counter():
    class ClockCounter:

        counter = 0

        def __call__(self, *args, **kwargs):
            self.counter += 1

    yield ClockCounter()


def test_schedule_once(kivy_clock, clock_counter):
    kivy_clock.schedule_once(clock_counter)
    kivy_clock.tick()
    assert clock_counter.counter == 1


def test_schedule_once_twice(kivy_clock, clock_counter):
    kivy_clock.schedule_once(clock_counter)
    kivy_clock.schedule_once(clock_counter)
    kivy_clock.tick()
    assert clock_counter.counter == 2


def test_schedule_once_draw_after(kivy_clock, clock_counter):
    kivy_clock.schedule_once(clock_counter, 0)
    kivy_clock.tick_draw()
    assert clock_counter.counter == 0
    kivy_clock.tick()
    assert clock_counter.counter == 1


def test_schedule_once_draw_before(kivy_clock, clock_counter):
    kivy_clock.schedule_once(clock_counter, -1)
    kivy_clock.tick_draw()
    assert clock_counter.counter == 1
    kivy_clock.tick()
    assert clock_counter.counter == 1


def test_unschedule(kivy_clock, clock_counter):
    kivy_clock.schedule_once(clock_counter)
    kivy_clock.unschedule(clock_counter)
    kivy_clock.tick()
    assert clock_counter.counter == 0


def test_unschedule_event(kivy_clock, clock_counter):
    ev = kivy_clock.schedule_once(clock_counter)
    kivy_clock.unschedule(ev)
    kivy_clock.tick()
    assert clock_counter.counter == 0


def test_unschedule_after_tick(kivy_clock, clock_counter):
    kivy_clock.schedule_once(clock_counter, 5.)
    kivy_clock.tick()
    kivy_clock.unschedule(clock_counter)
    kivy_clock.tick()
    assert clock_counter.counter == 0


def test_unschedule_draw(kivy_clock, clock_counter):
    kivy_clock.schedule_once(clock_counter, 0)
    kivy_clock.tick_draw()
    assert clock_counter.counter == 0
    kivy_clock.unschedule(clock_counter)
    kivy_clock.tick()
    assert clock_counter.counter == 0


def test_trigger_create(kivy_clock, clock_counter):
    trigger = kivy_clock.create_trigger(clock_counter, 0)
    trigger()
    assert clock_counter.counter == 0
    kivy_clock.tick()
    assert clock_counter.counter == 1


def test_trigger_cancel(kivy_clock, clock_counter):
    trigger = kivy_clock.create_trigger(clock_counter, 5.)
    trigger()
    trigger.cancel()
    kivy_clock.tick()
    assert clock_counter.counter == 0


def test_trigger_interval(kivy_clock, clock_counter):
    trigger = kivy_clock.create_trigger(clock_counter, 0, interval=True)
    trigger()
    kivy_clock.tick()
    assert clock_counter.counter == 1
    kivy_clock.tick()
    assert clock_counter.counter == 2


def test_trigger_decorator(kivy_clock, clock_counter):
    from kivy.clock import triggered

    @triggered()
    def triggered_callback():
        clock_counter(dt=0)

    triggered_callback()
    assert clock_counter.counter == 0
    kivy_clock.tick()
    assert clock_counter.counter == 1


def test_trigger_decorator_cancel(kivy_clock, clock_counter):
    from kivy.clock import triggered

    @triggered()
    def triggered_callback():
        clock_counter(dt=0)

    triggered_callback()
    triggered_callback.cancel()
    kivy_clock.tick()
    assert clock_counter.counter == 0
