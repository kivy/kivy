from kivy.tests.common import GraphicUnitTest

from kivy.input.motionevent import MotionEvent
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.base import EventLoop


class UTMotionEvent(MotionEvent):
    def depack(self, args):
        self.is_touch = True
        self.sx = args['x']
        self.sy = args['y']
        self.profile = ['pos']
        super(UTMotionEvent, self).depack(args)


class _TestSliderHandle(Slider):
    def __init__(self, **kwargs):
        super(_TestSliderHandle, self).__init__(**kwargs)
        self.sensitivity = 'handle'


class _TestSliderAll(Slider):
    def __init__(self, **kwargs):
        super(_TestSliderAll, self).__init__(**kwargs)
        self.sensitivity = 'all'


class SliderMoveTestCase(GraphicUnitTest):
    framecount = 0

    def setUp(self):
        # kill KV lang logging (too long test)
        import kivy.lang.builder as builder

        if not hasattr(self, '_trace'):
            self._trace = builder.trace

        self.builder = builder
        builder.trace = lambda *_, **__: None
        super(SliderMoveTestCase, self).setUp()

    def tearDown(self):
        # add the logging back
        import kivy.lang.builder as builder
        builder.trace = self._trace
        super(SliderMoveTestCase, self).tearDown()

    def test_slider_move(self):
        EventLoop.ensure_window()
        win = EventLoop.window
        layout = BoxLayout(orientation='vertical')

        s_handle = _TestSliderHandle()
        s_all = _TestSliderAll()
        layout.add_widget(s_handle)
        layout.add_widget(s_all)
        win.add_widget(layout)

        # get widgets ready
        EventLoop.idle()

        cur1 = s_handle.children[0]
        cur2 = s_all.children[0]

        h1 = cur1.to_window(*cur1.center)[1]
        h2 = h1 - s_handle.cursor_height
        h3 = cur2.to_window(*cur2.center)[1]
        h4 = h3 - s_all.cursor_height

        w1 = cur1.to_window(*cur1.center)[0]
        w2 = cur2.to_window(*cur2.center)[0]
        wh = win.width / 2.0
        dt = 2

        # default pos, new pos, slider ID
        points = [
            [w1, h1, wh, h1, 'handle'],
            [w1, h2, wh, h2, 'handle'],
            [w2, h3, wh, h3, 'all'],
            [w2, h4, wh, h4, 'all'],
        ]

        for point in points:
            x, y, nx, ny, id = point

            # custom touch
            touch = UTMotionEvent("unittest", 1, {
                "x": x / float(win.width),
                "y": y / float(win.height),
            })

            # touch down
            EventLoop.post_dispatch_input("begin", touch)

            if id == 'handle':
                # touch on handle
                if x == w1 and y == h1:
                    self.assertAlmostEqual(
                        s_handle.value, 0.0,
                        delta=dt
                    )
                # touch in widget area (ignored, previous value)
                elif x == w1 and y == h2:
                    self.assertAlmostEqual(
                        s_handle.value, 50.0,
                        delta=dt
                    )
            elif id == 'all':
                # touch on handle:
                if x == w1 and y == h3:
                    self.assertAlmostEqual(
                        s_all.value, 0.0,
                        delta=dt
                    )
                # touch in widget area
                elif x == w1 and y == h4:
                    self.assertAlmostEqual(
                        s_all.value, 0.0,
                        delta=dt
                    )

            # move from default to new pos
            touch.move({
                "x": nx / float(win.width),
                "y": ny / float(win.height)
            })
            EventLoop.post_dispatch_input("update", touch)

            if id == 'handle':
                # move from handle to center
                if nx == wh and ny == h1:
                    self.assertAlmostEqual(
                        s_handle.value, 50.0,
                        delta=dt
                    )
                # move to center (ignored, previous value)
                elif nx == wh and ny == h2:
                    self.assertAlmostEqual(
                        s_handle.value, 50.0,
                        delta=dt
                    )
            elif id == 'all':
                # touch on handle:
                if nx == wh and ny == h3:
                    self.assertAlmostEqual(
                        s_all.value, 50.0,
                        delta=dt
                    )
                # touch in widget area
                elif nx == wh and ny == h4:
                    self.assertAlmostEqual(
                        s_all.value, 50.0,
                        delta=dt
                    )

            # touch up
            EventLoop.post_dispatch_input("end", touch)

        self.render(layout)


if __name__ == '__main__':
    import unittest
    unittest.main()
