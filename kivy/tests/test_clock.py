'''
Clock tests
===========
'''
import gc
import weakref
import pytest


class ClockCounter:

    counter = 0

    def __call__(self, *args, **kwargs):
        self.counter += 1


@pytest.fixture()
def clock_counter():
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


def test_exception_caught(kivy_clock, clock_counter):
    exception = None

    def handle_test_exception(e):
        nonlocal exception
        exception = str(e)

    # monkey patch to ignore exception
    kivy_clock.handle_exception = handle_test_exception

    def raise_exception(*args):
        raise ValueError('Stooooop')

    kivy_clock.schedule_once(raise_exception)
    kivy_clock.schedule_once(clock_counter)
    kivy_clock.tick()

    assert clock_counter.counter == 1
    assert exception == 'Stooooop'


def test_exception_ignored(kivy_clock, clock_counter):
    def raise_exception(*args):
        raise ValueError('Stooooop')

    kivy_clock.schedule_once(raise_exception)
    kivy_clock.schedule_once(clock_counter)

    with pytest.raises(ValueError):
        kivy_clock.tick()

    assert clock_counter.counter == 0


def test_exception_caught_handler(
        kivy_clock, clock_counter, kivy_exception_manager):
    from kivy.base import ExceptionHandler
    exception = None

    class KivyHandler(ExceptionHandler):

        def handle_exception(self, e):
            nonlocal exception
            exception = str(e)
            return kivy_exception_manager.PASS
    kivy_exception_manager.add_handler(KivyHandler())

    def raise_exception(*args):
        raise ValueError('Stooooop')

    kivy_clock.schedule_once(raise_exception)
    kivy_clock.schedule_once(clock_counter)
    kivy_clock.tick()

    assert clock_counter.counter == 1
    assert exception == 'Stooooop'


def test_clock_ended_callback(kivy_clock, clock_counter):
    counter2 = ClockCounter()
    counter_schedule = ClockCounter()

    kivy_clock.schedule_once(counter_schedule)
    event = kivy_clock.create_lifecycle_aware_trigger(clock_counter, counter2)
    event()

    kivy_clock.stop_clock()
    assert counter_schedule.counter == 0
    assert clock_counter.counter == 0
    assert counter2.counter == 1


def test_clock_ended_del_safe(kivy_clock, clock_counter):
    counter2 = ClockCounter()
    kivy_clock.schedule_lifecycle_aware_del_safe(clock_counter, counter2)

    kivy_clock.stop_clock()
    assert clock_counter.counter == 0
    assert counter2.counter == 1


def test_clock_ended_raises(kivy_clock, clock_counter):
    from kivy.clock import ClockNotRunningError
    event = kivy_clock.create_lifecycle_aware_trigger(
        clock_counter, clock_counter)

    kivy_clock.stop_clock()
    with pytest.raises(ClockNotRunningError):
        event()
    assert clock_counter.counter == 0

    # we should be able to create the event
    event = kivy_clock.create_lifecycle_aware_trigger(
        clock_counter, clock_counter)
    with pytest.raises(ClockNotRunningError):
        event()
    assert clock_counter.counter == 0

    kivy_clock.schedule_once(clock_counter)
    assert clock_counter.counter == 0


def test_clock_ended_del_safe_raises(kivy_clock, clock_counter):
    from kivy.clock import ClockNotRunningError
    counter2 = ClockCounter()

    kivy_clock.stop_clock()
    with pytest.raises(ClockNotRunningError):
        kivy_clock.schedule_lifecycle_aware_del_safe(clock_counter, counter2)
    assert clock_counter.counter == 0


def test_clock_stop_twice(kivy_clock, clock_counter):
    counter2 = ClockCounter()
    event = kivy_clock.create_lifecycle_aware_trigger(
        clock_counter, counter2)
    event()

    kivy_clock.stop_clock()
    assert clock_counter.counter == 0
    assert counter2.counter == 1

    kivy_clock.stop_clock()
    assert clock_counter.counter == 0
    assert counter2.counter == 1


def test_clock_restart(kivy_clock):
    kivy_clock.stop_clock()
    # with pytest.raises(TypeError):
    #     kivy_clock.start_clock()
    # for now it doesn't yet raise a error
    kivy_clock.start_clock()


def test_clock_event_trigger_ref(kivy_clock):
    value = None

    class Counter:
        def call(self, *args, **kwargs):
            nonlocal value
            value = 42

    event = kivy_clock.create_trigger(Counter().call)
    gc.collect()
    event()
    kivy_clock.tick()
    assert value is None

    kivy_clock.schedule_once(Counter().call)
    event()
    kivy_clock.tick()
    assert value is None

    event = kivy_clock.create_trigger(Counter().call, release_ref=False)
    gc.collect()
    event()
    kivy_clock.tick()
    assert value == 42
