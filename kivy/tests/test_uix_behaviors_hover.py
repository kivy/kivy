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


@p_event_repeat_timeout
def test_enter_moveinside_leave(event_repeat_timeout):
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

        Window.mouse_pos = 120, 120
        advance_frames(1)
        assert target.hovered
        assert list(target.hover_ids.values()) == [pytest.approx((120, 120))]
        assert target.n_enter == 1
        assert target.n_update == 1
        assert target.n_leave == 0

        Window.mouse_pos = 130, 130
        advance_frames(1)
        assert target.hovered
        assert list(target.hover_ids.values()) == [pytest.approx((130, 130))]
        assert target.n_enter == 1
        assert target.n_update == 2
        assert target.n_leave == 0

        Window.mouse_pos = 20, 20
        advance_frames(1)
        assert not target.hovered
        assert target.hover_ids == {}
        assert target.n_enter == 1
        assert target.n_update == 2
        assert target.n_leave == 1


@p_event_repeat_timeout
def test_enter_stay(event_repeat_timeout, advance_time):
    from kivy.core.window import Window
    from kivy.lang import Builder

    tree = Builder.load_string(SIMPLE_WIDGET_TREE)
    Window.add_widget(tree)
    advance_frames(1)
    target = tree.ids.target

    with enable_hover_manager(event_repeat_timeout):
        Window.mouse_pos = 20, 20
        advance_frames(1)

        Window.mouse_pos = 110, 110
        advance_frames(1)
        assert target.hovered
        assert list(target.hover_ids.values()) == [pytest.approx((110, 110))]
        assert target.n_enter == 1
        assert target.n_update == 0
        assert target.n_leave == 0

        # Staying in the same position does not trigger `on_hover_update`.
        for __ in range(3):
            advance_time(1)
            advance_frames(1)
            assert target.hovered
            assert list(target.hover_ids.values()) == [pytest.approx((110, 110))]
            assert target.n_enter == 1
            assert target.n_update == 0
            assert target.n_leave == 0

    # Stopping the hover manager triggers `on_hover_leave`.
    assert not target.hovered
    assert target.hover_ids == {}
    assert target.n_enter == 1
    assert target.n_update == 0
    assert target.n_leave == 1


@p_event_repeat_timeout
def test_target_moves(event_repeat_timeout, advance_time):
    from kivy.core.window import Window
    from kivy.lang import Builder

    tree = Builder.load_string(SIMPLE_WIDGET_TREE)
    Window.add_widget(tree)
    advance_frames(1)
    target = tree.ids.target

    with enable_hover_manager(event_repeat_timeout):
        Window.mouse_pos = 20, 20
        advance_frames(1)

        Window.mouse_pos = 110, 110
        advance_frames(1)
        assert target.hovered
        assert list(target.hover_ids.values()) == [pytest.approx((110, 110))]
        assert target.n_enter == 1
        assert target.n_update == 0
        assert target.n_leave == 0

        # Moving the target to a position where it still collides with the mouse
        # cursor does not trigger `on_hover_update`.
        target.x = 90
        for __ in range(3):
            advance_time(1)
            advance_frames(1)
            assert target.hovered
            assert list(target.hover_ids.values()) == [pytest.approx((110, 110))]
            assert target.n_enter == 1
            assert target.n_update == 0
            assert target.n_leave == 0

        target.x = 1000
        advance_time(0.7)
        advance_frames(1)
        if event_repeat_timeout == 0:
            assert not target.hovered
            assert target.hover_ids == {}
            assert target.n_enter == 1
            assert target.n_update == 0
            assert target.n_leave == 1
        elif event_repeat_timeout in (-2, -1, 1):
            assert target.hovered
            assert list(target.hover_ids.values()) == [pytest.approx((110, 110))]
            assert target.n_enter == 1
            assert target.n_update == 0
            assert target.n_leave == 0
        else:
            pytest.fail("Unexpected event_repeat_timeout value: "
                        + str(event_repeat_timeout))
        advance_time(0.7)
        advance_frames(1)
        if event_repeat_timeout in (0, 1):
            assert not target.hovered
            assert target.hover_ids == {}
            assert target.n_enter == 1
            assert target.n_update == 0
            assert target.n_leave == 1
        elif event_repeat_timeout in (-2, -1):
            assert target.hovered
            assert list(target.hover_ids.values()) == [pytest.approx((110, 110))]
            assert target.n_enter == 1
            assert target.n_update == 0
            assert target.n_leave == 0


@p_event_repeat_timeout
def test_relative_coordinates(event_repeat_timeout):
    '''
    This test might be redundant since `test_clipped_by_scrollview` already covers it.
    I added it because ScrollView is a complex widget and might have its own bugs.
    '''
    from kivy.core.window import Window
    from kivy.lang import Builder

    tree = Builder.load_string(dedent("""
        Widget:
            RelativeLayout:
                pos: 100, 100
                HoverEventCounter:
                    id: target
                    size_hint: None, None
                    size: 100, 100
        """))
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
        assert list(target.hover_ids.values()) == [pytest.approx((10, 10))]
        assert target.n_enter == 1
        assert target.n_update == 0
        assert target.n_leave == 0

        Window.mouse_pos = 120, 120
        advance_frames(1)
        assert target.hovered
        assert list(target.hover_ids.values()) == [pytest.approx((20, 20))]
        assert target.n_enter == 1
        assert target.n_update == 1
        assert target.n_leave == 0

        Window.mouse_pos = 20, 20
        advance_frames(1)
        assert not target.hovered
        assert target.hover_ids == {}
        assert target.n_enter == 1
        assert target.n_update == 1
        assert target.n_leave == 1


@p_event_repeat_timeout
def test_clipped_by_scrollview(event_repeat_timeout):
    from kivy.core.window import Window
    from kivy.lang import Builder

    tree = Builder.load_string(dedent("""
        Widget:
            HoverCollideScrollView:
                pos: 100, 100
                size: 100, 100
                scroll_x: 0
                scroll_y: 0
                HoverEventCounter:
                    id: target
                    size_hint: None, None
                    size: 200, 200
        """))
    Window.add_widget(tree)
    advance_frames(1)
    target = tree.ids.target

    with enable_hover_manager(event_repeat_timeout):
        assert not target.hovered
        assert target.hover_ids == {}
        assert target.n_enter == 0
        assert target.n_update == 0
        assert target.n_leave == 0

        Window.mouse_pos = 50, 50
        advance_frames(1)
        assert not target.hovered
        assert target.hover_ids == {}
        assert target.n_enter == 0
        assert target.n_update == 0
        assert target.n_leave == 0

        Window.mouse_pos = 150, 150
        advance_frames(1)
        assert target.hovered
        assert list(target.hover_ids.values()) == [pytest.approx((50, 50))]
        assert target.n_enter == 1
        assert target.n_update == 0
        assert target.n_leave == 0

        Window.mouse_pos = 160, 160
        advance_frames(1)
        assert target.hovered
        assert list(target.hover_ids.values()) == [pytest.approx((60, 60))]
        assert target.n_enter == 1
        assert target.n_update == 1
        assert target.n_leave == 0

        # The mouse cursor would collide with the target if it were not clipped
        # by the ScrollView.
        Window.mouse_pos = 250, 250
        advance_frames(1)
        assert not target.hovered
        assert target.hover_ids == {}
        assert target.n_enter == 1
        assert target.n_update == 1
        assert target.n_leave == 1


NESTED_WIDGET_TREE = '''
Widget:
    HoverEventCounter:
        id: outer
        size_hint: None, None
        size: 200, 200
        pos: 100, 100
        HoverEventCounter:
            id: inner
            size_hint: None, None
            size: 200, 200
            pos: 200, 200
'''


def test_hover_mode_default():
    from kivy.core.window import Window
    from kivy.lang import Builder

    tree = Builder.load_string(NESTED_WIDGET_TREE)
    Window.add_widget(tree)
    outer = tree.ids.outer
    inner = tree.ids.inner
    outer.hover_mode = "default"
    advance_frames(1)

    with enable_hover_manager(0):
        # outside both
        Window.mouse_pos = 50, 50
        advance_frames(1)
        assert not outer.hovered
        assert not inner.hovered
        assert outer.hover_ids == {}
        assert inner.hover_ids == {}
        assert outer.n_enter == 0
        assert inner.n_enter == 0
        assert outer.n_update == 0
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # inside the outer. outside the inner.
        Window.mouse_pos = 150, 150
        advance_frames(1)
        assert outer.hovered
        assert not inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((150, 150))]
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 0
        assert outer.n_update == 0
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # inside the outer. outside the inner.
        Window.mouse_pos = 160, 160
        advance_frames(1)
        assert outer.hovered
        assert not inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((160, 160))]
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 0
        assert outer.n_update == 1
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # inside both.
        Window.mouse_pos = 250, 250
        advance_frames(1)
        assert not outer.hovered
        assert inner.hovered
        assert outer.hover_ids == {}
        assert list(inner.hover_ids.values()) == [pytest.approx((250, 250))]
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 1
        assert inner.n_update == 0
        assert outer.n_leave == 1
        assert inner.n_leave == 0

        # inside both.
        Window.mouse_pos = 260, 260
        advance_frames(1)
        assert not outer.hovered
        assert inner.hovered
        assert outer.hover_ids == {}
        assert list(inner.hover_ids.values()) == [pytest.approx((260, 260))]
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 1
        assert inner.n_update == 1
        assert outer.n_leave == 1
        assert inner.n_leave == 0

        # outside the outer. inside the inner.
        Window.mouse_pos = 350, 350
        advance_frames(1)
        assert not outer.hovered
        assert inner.hovered
        assert outer.hover_ids == {}
        assert list(inner.hover_ids.values()) == [pytest.approx((350, 350))]
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 1
        assert inner.n_update == 2
        assert outer.n_leave == 1
        assert inner.n_leave == 0

        # outside the outer. inside the inner.
        Window.mouse_pos = 360, 360
        advance_frames(1)
        assert not outer.hovered
        assert inner.hovered
        assert outer.hover_ids == {}
        assert list(inner.hover_ids.values()) == [pytest.approx((360, 360))]
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 1
        assert inner.n_update == 3
        assert outer.n_leave == 1
        assert inner.n_leave == 0

        # outside both.
        Window.mouse_pos = 1000, 1000
        advance_frames(1)
        assert not outer.hovered
        assert not inner.hovered
        assert outer.hover_ids == {}
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 1
        assert inner.n_update == 3
        assert outer.n_leave == 1
        assert inner.n_leave == 1


def test_hover_mode_self():
    from kivy.core.window import Window
    from kivy.lang import Builder

    tree = Builder.load_string(NESTED_WIDGET_TREE)
    Window.add_widget(tree)
    outer = tree.ids.outer
    inner = tree.ids.inner
    outer.hover_mode = "self"
    advance_frames(1)

    with enable_hover_manager(0):
        # outside both
        Window.mouse_pos = 50, 50
        advance_frames(1)
        assert not outer.hovered
        assert not inner.hovered
        assert outer.hover_ids == {}
        assert inner.hover_ids == {}
        assert outer.n_enter == 0
        assert inner.n_enter == 0
        assert outer.n_update == 0
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # inside the outer. outside the inner.
        Window.mouse_pos = 150, 150
        advance_frames(1)
        assert outer.hovered
        assert not inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((150, 150))]
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 0
        assert outer.n_update == 0
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # inside the outer. outside the inner.
        Window.mouse_pos = 160, 160
        advance_frames(1)
        assert outer.hovered
        assert not inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((160, 160))]
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 0
        assert outer.n_update == 1
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # inside both.
        Window.mouse_pos = 250, 250
        advance_frames(1)
        assert outer.hovered
        assert not inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((250, 250))]
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 0
        assert outer.n_update == 2
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # inside both.
        Window.mouse_pos = 260, 260
        advance_frames(1)
        assert outer.hovered
        assert not inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((260, 260))]
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 0
        assert outer.n_update == 3
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # outside the outer. inside the inner.
        Window.mouse_pos = 350, 350
        advance_frames(1)
        assert not outer.hovered
        assert not inner.hovered
        assert outer.hover_ids == {}
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 0
        assert outer.n_update == 3
        assert inner.n_update == 0
        assert outer.n_leave == 1
        assert inner.n_leave == 0

        # outside the outer. inside the inner.
        Window.mouse_pos = 360, 360
        advance_frames(1)
        assert not outer.hovered
        assert not inner.hovered
        assert outer.hover_ids == {}
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 0
        assert outer.n_update == 3
        assert inner.n_update == 0
        assert outer.n_leave == 1
        assert inner.n_leave == 0

        # outside both.
        Window.mouse_pos = 1000, 1000
        advance_frames(1)
        assert not outer.hovered
        assert not inner.hovered
        assert outer.hover_ids == {}
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 0
        assert outer.n_update == 3
        assert inner.n_update == 0
        assert outer.n_leave == 1
        assert inner.n_leave == 0


@p_event_repeat_timeout
def test_hover_mode_all(event_repeat_timeout):
    from kivy.core.window import Window
    from kivy.lang import Builder

    tree = Builder.load_string(NESTED_WIDGET_TREE)
    Window.add_widget(tree)
    outer = tree.ids.outer
    inner = tree.ids.inner
    outer.hover_mode = "all"
    advance_frames(1)

    with enable_hover_manager(event_repeat_timeout):
        # outside both
        Window.mouse_pos = 50, 50
        advance_frames(1)
        assert not outer.hovered
        assert not inner.hovered
        assert outer.hover_ids == {}
        assert inner.hover_ids == {}
        assert outer.n_enter == 0
        assert inner.n_enter == 0
        assert outer.n_update == 0
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # inside the outer. outside the inner.
        Window.mouse_pos = 150, 150
        advance_frames(1)
        assert outer.hovered
        assert not inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((150, 150))]
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 0
        assert outer.n_update == 0
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # inside the outer. outside the inner.
        Window.mouse_pos = 160, 160
        advance_frames(1)
        assert outer.hovered
        assert not inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((160, 160))]
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 0
        assert outer.n_update == 1
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # inside both.
        Window.mouse_pos = 250, 250
        advance_frames(1)
        assert outer.hovered
        assert inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((250, 250))]
        assert list(inner.hover_ids.values()) == [pytest.approx((250, 250))]
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 2
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # inside both.
        Window.mouse_pos = 260, 260
        advance_frames(1)
        assert outer.hovered
        assert inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((260, 260))]
        assert list(inner.hover_ids.values()) == [pytest.approx((260, 260))]
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 3
        assert inner.n_update == 1
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        # outside the outer. inside the inner.
        Window.mouse_pos = 350, 350
        advance_frames(1)
        assert not outer.hovered
        assert inner.hovered
        assert outer.hover_ids == {}
        assert list(inner.hover_ids.values()) == [pytest.approx((350, 350))]
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 3
        assert inner.n_update == 2
        assert outer.n_leave == 1
        assert inner.n_leave == 0

        # outside the outer. inside the inner.
        Window.mouse_pos = 360, 360
        advance_frames(1)
        assert not outer.hovered
        assert inner.hovered
        assert outer.hover_ids == {}
        assert list(inner.hover_ids.values()) == [pytest.approx((360, 360))]
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 3
        assert inner.n_update == 3
        assert outer.n_leave == 1
        assert inner.n_leave == 0

        # outside both.
        Window.mouse_pos = 1000, 1000
        advance_frames(1)
        assert not outer.hovered
        assert not inner.hovered
        assert outer.hover_ids == {}
        assert inner.hover_ids == {}
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 3
        assert inner.n_update == 3
        assert outer.n_leave == 1
        assert inner.n_leave == 1


@pytest.mark.parametrize("event_repeat_timeout", (0, 1))
def test_changing_hover_mode_while_hovered(event_repeat_timeout, advance_time):
    from kivy.core.window import Window
    from kivy.lang import Builder

    tree = Builder.load_string(NESTED_WIDGET_TREE)
    Window.add_widget(tree)
    outer = tree.ids.outer
    inner = tree.ids.inner
    outer.hover_mode = "all"
    advance_frames(1)

    with enable_hover_manager(event_repeat_timeout):
        # outside both
        Window.mouse_pos = 50, 50
        advance_frames(1)

        # inside both.
        Window.mouse_pos = 250, 250
        advance_frames(1)
        assert outer.hovered
        assert inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((250, 250))]
        assert list(inner.hover_ids.values()) == [pytest.approx((250, 250))]
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 0
        assert inner.n_update == 0
        assert outer.n_leave == 0
        assert inner.n_leave == 0

        outer.hover_mode = "default"
        advance_time(0.7)
        advance_frames(1)
        if event_repeat_timeout == 0:
            assert not outer.hovered
            assert inner.hovered
            assert outer.hover_ids == {}
            assert list(inner.hover_ids.values()) == [pytest.approx((250, 250))]
            assert outer.n_enter == 1
            assert inner.n_enter == 1
            assert outer.n_update == 0
            assert inner.n_update == 0
            assert outer.n_leave == 1
            assert inner.n_leave == 0
        else:
            assert outer.hovered
            assert inner.hovered
            assert list(outer.hover_ids.values()) == [pytest.approx((250, 250))]
            assert list(inner.hover_ids.values()) == [pytest.approx((250, 250))]
            assert outer.n_enter == 1
            assert inner.n_enter == 1
            assert outer.n_update == 0
            assert inner.n_update == 0
            assert outer.n_leave == 0
            assert inner.n_leave == 0

        advance_time(0.7)
        advance_frames(1)
        assert not outer.hovered
        assert inner.hovered
        assert outer.hover_ids == {}
        assert list(inner.hover_ids.values()) == [pytest.approx((250, 250))]
        assert outer.n_enter == 1
        assert inner.n_enter == 1
        assert outer.n_update == 0
        assert inner.n_update == 0
        assert outer.n_leave == 1
        assert inner.n_leave == 0


        outer.hover_mode = "self"
        advance_time(0.7)
        advance_frames(1)
        if event_repeat_timeout == 0:
            assert outer.hovered
            assert not inner.hovered
            assert list(outer.hover_ids.values()) == [pytest.approx((250, 250))]
            assert inner.hover_ids == {}
            assert outer.n_enter == 2
            assert inner.n_enter == 1
            assert outer.n_update == 0
            assert inner.n_update == 0
            assert outer.n_leave == 1
            assert inner.n_leave == 1
        else:
            assert not outer.hovered
            assert inner.hovered
            assert outer.hover_ids == {}
            assert list(inner.hover_ids.values()) == [pytest.approx((250, 250))]
            assert outer.n_enter == 1
            assert inner.n_enter == 1
            assert outer.n_update == 0
            assert inner.n_update == 0
            assert outer.n_leave == 1
            assert inner.n_leave == 0

        advance_time(0.7)
        advance_frames(1)
        assert outer.hovered
        assert not inner.hovered
        assert list(outer.hover_ids.values()) == [pytest.approx((250, 250))]
        assert inner.hover_ids == {}
        assert outer.n_enter == 2
        assert inner.n_enter == 1
        assert outer.n_update == 0
        assert inner.n_update == 0
        assert outer.n_leave == 1
        assert inner.n_leave == 1
