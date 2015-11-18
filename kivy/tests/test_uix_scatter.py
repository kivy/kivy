'''
Scatter tests
================
'''

import pytest
from time import sleep, time

from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.input import MotionEvent
from kivy.uix.scatter import ScatterBehavior, Scatter
from kivy.uix.widget import Widget


# https://gist.github.com/tito/f111b6916aa6a4ed0851
# subclass for touch event in unit test
class UTMotionEvent(MotionEvent):
    def depack(self, args):
        self.is_touch = True
        self.sx = args['x']
        self.sy = args['y']
        self.profile = ['pos']
        super(UTMotionEvent, self).depack(args)


class UTWidget(Widget):
    def __init__(self, **kwargs):
        super(UTWidget, self).__init__(**kwargs)
        self.touched_down = False
        self.touched_move = False
        self.touched_up = False

    def on_touch_down(self, touch):
        self.touched_down = True

    def on_touch_move(self, touch):
        self.touched_move = True

    def on_touch_up(self, touch):
        self.touched_up = True


@pytest.fixture
def touch():
    return UTMotionEvent('unittest', 1, {'x': .5, 'y': .5})


@pytest.fixture
def multitouch():
    return (
        UTMotionEvent('unittest', 1, {'x': .5, 'y': .5}),
        UTMotionEvent('unittest', 2, {'x': .5, 'y': .25}),
    )


@pytest.fixture
def child():
    return UTWidget()


@pytest.fixture
def scatter(request, child):
    widget = Scatter()
    widget.bind(size=child.setter('size'))
    widget.add_widget(child)

    EventLoop.ensure_window()
    window = EventLoop.window
    window.add_widget(widget)
    request.addfinalizer(lambda: window.remove_widget(widget))
    Clock.tick()

    return widget


class TestScatterBehaviorTranslation:
    @pytest.fixture(autouse=True, params=[True, False])
    def setup(self, request, scatter):
        scatter.do_dispatch_after_children = request.param

    def test_scatterbehavior_translation_single_touch(self, touch, scatter, child):
        EventLoop.post_dispatch_input('begin', touch)
        touch.sx -= .1
        touch.sy -= .1
        EventLoop.post_dispatch_input('update', touch)
        assert child.touched_move != scatter.do_dispatch_after_children
        assert scatter.pos == touch.dpos

    def test_scatterbehavior_translation_multi_touch(self, multitouch, scatter, child):
        for touch in multitouch:
            EventLoop.post_dispatch_input('begin', touch)
        for touch in multitouch:
            touch.sx -= .1
            touch.sy -= .1
            EventLoop.post_dispatch_input('update', touch)
        assert child.touched_move != scatter.do_dispatch_after_children
        for touch in multitouch:
            for pos, dpos in zip(scatter.pos, touch.dpos):
                assert abs(pos - dpos) < 0.0001


class TestScatterBehaviorRotation:
    @pytest.fixture(autouse=True, params=[True, False])
    def setup(self, request, scatter):
        scatter.do_dispatch_after_children = request.param

    def test_scatterbehavior_rotation(self, multitouch, scatter, child):
        for touch in multitouch:
            EventLoop.post_dispatch_input('begin', touch)
        touch.sy, touch.sx = touch.spos
        EventLoop.post_dispatch_input('update', touch)
        assert child.touched_move != scatter.do_dispatch_after_children
        assert abs(scatter.rotation + 90) % 360 < 0.0001


class TestScatterBehaviorScale:
    @pytest.fixture(autouse=True, params=[True, False])
    def setup(self, request, scatter):
        scatter.do_dispatch_after_children = request.param

    def test_scatterbehavior_scale(self, multitouch, scatter, child):
        for touch in multitouch:
            EventLoop.post_dispatch_input('begin', touch)
        touch.sy = 0
        EventLoop.post_dispatch_input('update', touch)
        assert child.touched_move != scatter.do_dispatch_after_children
        assert abs(scatter.scale - 2) < 0.0001


class TestScatterBehaviorDispatchAfterChildren:
    def sleep(self, t):
        start = time()
        while time() < start + t:
            sleep(.01)
            Clock.tick()

    @pytest.fixture(autouse=True)
    def setup(self, scatter):
        scatter.do_dispatch_after_children = True

    def test_scatterbehavior_dispatch_after_children_on_touch_down_short(self, touch, child):
        EventLoop.post_dispatch_input('begin', touch)
        self.sleep(.1)
        assert child.touched_down == False

    def test_scatterbehavior_dispatch_after_children_on_touch_down_long(self, touch, child):
        EventLoop.post_dispatch_input('begin', touch)
        self.sleep(.6)
        assert child.touched_down == True

    def test_scatterbehavior_dispatch_after_children_on_touch_move_short(self, touch, scatter, child):
        EventLoop.post_dispatch_input('begin', touch)
        self.sleep(.1)
        touch.sx -= .1
        touch.sy -= .1
        EventLoop.post_dispatch_input('update', touch)
        assert child.touched_move == False
        assert scatter.pos == touch.dpos

    def test_scatterbehavior_dispatch_after_children_on_touch_move_long(self, touch, scatter, child):
        EventLoop.post_dispatch_input('begin', touch)
        self.sleep(.6)
        touch.sx -= .1
        touch.sy -= .1
        EventLoop.post_dispatch_input('update', touch)
        assert child.touched_move == True
        assert scatter.pos == (0, 0)

    def test_scatterbehavior_dispatch_after_children_on_touch_up_short(self, touch, child):
        EventLoop.post_dispatch_input('begin', touch)
        self.sleep(.1)
        EventLoop.post_dispatch_input('end', touch)
        assert child.touched_up == False
        self.sleep(.1)
        assert child.touched_up == True

    def test_scatterbehavior_dispatch_after_children_on_touch_up_long(self, touch, child):
        EventLoop.post_dispatch_input('begin', touch)
        self.sleep(.6)
        EventLoop.post_dispatch_input('end', touch)
        assert child.touched_up == True
        self.sleep(.1)
        assert child.touched_up == True
