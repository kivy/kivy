from contextlib import contextmanager
from textwrap import dedent

import pytest
from kivy.tests.common import advance_frames


@pytest.fixture()
def advance_time(kivy_init, kivy_clock):
    '''
    Allows advancing Kivy time independently of real time, enabling reliable
    testing of time-sensitive code.
    '''
    current_time = kivy_clock.time()
    kivy_clock.time = lambda: current_time

    def advance(duration):
        nonlocal current_time
        current_time += duration
    return advance


@pytest.fixture(autouse=True, scope="module")
def register_widgets_to_factory():
    from kivy.factory import Factory
    from kivy.uix.widget import Widget
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.behaviors import HoverBehavior, HoverCollideBehavior

    class HoverEventCounter(HoverBehavior, Widget):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.n_enter = 0
            self.n_update = 0
            self.n_leave = 0

        def on_hover_enter(self, me):
            self.n_enter += 1
            return super().on_hover_enter(me)

        def on_hover_update(self, me):
            self.n_update += 1
            return super().on_hover_update(me)

        def on_hover_leave(self, me):
            self.n_leave += 1
            return super().on_hover_leave(me)

    class HoverCollideScrollView(HoverCollideBehavior, ScrollView):
        pass

    yield
    Factory.unregister("HoverEventCounter")
    Factory.unregister("HoverCollideScrollView")


@pytest.fixture(autouse=True)
def enable_mouse_motion_event_provider(kivy_init):
    from kivy.base import EventLoop
    from kivy.input.providers.mouse import MouseMotionEventProvider
    from kivy.core.window import Window
    Window.mouse_pos = Window.property("mouse_pos").defaultvalue
    provider = MouseMotionEventProvider("mouse", "")
    EventLoop.add_input_provider(provider)
    provider.start()
    yield
    provider.stop()
    EventLoop.remove_input_provider(provider)


@contextmanager
def enable_hover_manager(event_repeat_timeout):
    from kivy.core.window import Window
    from kivy.eventmanager.hover import HoverManager
    mgr = HoverManager(event_repeat_timeout=event_repeat_timeout)
    Window.register_event_manager(mgr)
    try:
        yield mgr
    finally:
        Window.unregister_event_manager(mgr)


SIMPLE_WIDGET_TREE = '''
Widget:
    HoverEventCounter:
        id: target
        size_hint: None, None
        size: 100, 100
        pos: 100, 100
'''

p_event_repeat_timeout = pytest.mark.parametrize(
    "event_repeat_timeout", (-2, -1, 0, 1), ids=lambda v: f"event_repeat_timeout={v}")


@p_event_repeat_timeout
def test_enter_leave(event_repeat_timeout):
    from kivy.core.window import Window
    from kivy.lang import Builder

    tree = Builder.load_string(SIMPLE_WIDGET_TREE)
    Window.add_widget(tree)
    advance_frames(1)
    target = tree.ids.target

    with enable_hover_manager(event_repeat_timeout):
        assert not target.hovered
        assert target.hover_ids == {}
        assert target.n_enter == 0
        assert target.n_update == 0
        assert target.n_leave == 0

        Window.mouse_pos = 20, 20
        advance_frames(1)
        assert not target.hovered
        assert target.hover_ids == {}
        assert target.n_enter == 0
        assert target.n_update == 0
        assert target.n_leave == 0

        Window.mouse_pos = 110, 110
        advance_frames(1)
        assert target.hovered
        assert list(target.hover_ids.values()) == [pytest.approx((110, 110))]
        assert target.n_enter == 1
        assert target.n_update == 0
        assert target.n_leave == 0

        Window.mouse_pos = 20, 20
        advance_frames(1)
        assert not target.hovered
        assert target.hover_ids == {}
        assert target.n_enter == 1
        assert target.n_update == 0
        assert target.n_leave == 1
