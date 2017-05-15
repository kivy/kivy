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


class TestSliderHandle(Slider):
    def __init__(self, **kwargs):
        super(TestSliderHandle, self).__init__(**kwargs)
        self.sensitivity = 'handle'


class TestSliderAll(Slider):
    def __init__(self, **kwargs):
        super(TestSliderAll, self).__init__(**kwargs)
        self.sensitivity = 'all'


class SliderMoveTestCase(GraphicUnitTest):
    framecount = 0

    # debug with
    # def tearDown(self, *a): pass
    # def setUp(self): pass

    def test_slider_move(self):
        EventLoop.ensure_window()
        win = EventLoop.window
        layout = BoxLayout(orientation='vertical')

        h1 = 0.75 * win.height
        h2 = 0.625 * win.height
        h3 = 0.25 * win.height
        h4 = 0.125 * win.height
        wh = win.width / 2.0
        w1 = 0.1 * wh
        dt = 2

        # default pos, new pos, slider ID
        points = [
            [w1, h1, wh, h1, 'handle'],  # handle
            [w1, h2, wh, h2, 'handle'],  # handle
            [w1, h3, wh, h3, 'all'],     # all
            [w1, h4, wh, h4, 'all'],     # all
        ]

        s_handle = TestSliderHandle()
        s_all = TestSliderAll()
        layout.add_widget(s_handle)
        layout.add_widget(s_all)
        win.add_widget(layout)

        for point in points:
            x, y, nx, ny, id = point

            # get widgets ready
            EventLoop.idle()

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
