from kivy.tests.common import GraphicUnitTest

from kivy.input.motionevent import MotionEvent
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.base import EventLoop
from kivy.clock import Clock
from time import sleep

DEBUG = False


class UTMotionEvent(MotionEvent):
    def depack(self, args):
        self.is_touch = True
        self.sx = args['x']
        self.sy = args['y']
        self.profile = ['pos']
        super(UTMotionEvent, self).depack(args)


class TestGrid(GridLayout):
    def __init__(self, **kwargs):
        kwargs['cols'] = 1
        kwargs['spacing'] = 10
        kwargs['size_hint'] = (None, None)
        super(TestGrid, self).__init__(**kwargs)
        self.bind(minimum_height=self.setter('height'))
        self.bind(minimum_width=self.setter('width'))

        for i in range(10):
            self.add_widget(Label(
                size_hint=(None, None),
                height=100, width=1000,
                text=str(i)
            ))


class TestScrollbarHorizontal(ScrollView):
    def __init__(self, **kwargs):
        kwargs['scroll_type'] = ["bars"]
        kwargs['bar_width'] = 20
        kwargs['do_scroll_y'] = False
        super(TestScrollbarHorizontal, self).__init__(**kwargs)


class TestScrollbarVertical(ScrollView):
    def __init__(self, **kwargs):
        kwargs['scroll_type'] = ["bars"]
        kwargs['bar_width'] = 20
        kwargs['do_scroll_x'] = False
        super(TestScrollbarVertical, self).__init__(**kwargs)


class TestScrollbarBoth(ScrollView):
    def __init__(self, **kwargs):
        kwargs['scroll_type'] = ["bars"]
        kwargs['bar_width'] = 20
        super(TestScrollbarBoth, self).__init__(**kwargs)


class TestScrollbarHorizontalMargin(ScrollView):
    def __init__(self, **kwargs):
        kwargs['scroll_type'] = ["bars"]
        kwargs['bar_margin'] = 40
        kwargs['bar_width'] = 20
        kwargs['do_scroll_y'] = False
        super(TestScrollbarHorizontalMargin, self).__init__(**kwargs)


class TestScrollbarVerticalMargin(ScrollView):
    def __init__(self, **kwargs):
        kwargs['scroll_type'] = ["bars"]
        kwargs['bar_margin'] = 40
        kwargs['bar_width'] = 20
        kwargs['do_scroll_x'] = False
        super(TestScrollbarVerticalMargin, self).__init__(**kwargs)


class TestScrollbarBothMargin(ScrollView):
    def __init__(self, **kwargs):
        kwargs['scroll_type'] = ["bars"]
        kwargs['bar_margin'] = 40
        kwargs['bar_width'] = 20
        super(TestScrollbarBothMargin, self).__init__(**kwargs)


class ScrollViewTestCase(GraphicUnitTest):
    framecount = 0

    def process_points(self, scroll, points):
        win = EventLoop.window
        dt = 0.02

        for point in points:
            if DEBUG:
                print('point:', point, scroll.scroll_x, scroll.scroll_y)
                Clock.schedule_once(lambda *dt: sleep(0.5), 0)
                self.render(scroll)

            x, y, nx, ny, pos_x, pos_y, border_check = point
            scroll.bar_pos = (pos_x, pos_y)

            touch = UTMotionEvent("unittest", 1, {
                "x": x / float(win.width),
                "y": y / float(win.height),
            })

            # we start with the default top-left corner
            self.assertAlmostEqual(scroll.scroll_x, 0.0, delta=dt)
            self.assertAlmostEqual(scroll.scroll_y, 1.0, delta=dt)

            # check the collision with the margin empty area
            if border_check:
                EventLoop.post_dispatch_input("begin", touch)
                touch.move({
                    "x": nx / float(win.width),
                    "y": ny / float(win.height)
                })
                EventLoop.post_dispatch_input("update", touch)
                EventLoop.post_dispatch_input("end", touch)

                self.assertAlmostEqual(scroll.scroll_x, 0.0, delta=dt)
                self.assertAlmostEqual(scroll.scroll_y, 1.0, delta=dt)
                return

            EventLoop.post_dispatch_input("begin", touch)
            touch.move({
                "x": nx / float(win.width),
                "y": ny / float(win.height)
            })
            EventLoop.post_dispatch_input("update", touch)
            EventLoop.post_dispatch_input("end", touch)

            if DEBUG:
                print(scroll.scroll_x, scroll.scroll_y)
                Clock.schedule_once(lambda *dt: sleep(0.5), 0)
                self.render(scroll)

            # check the scroll position
            self.assertAlmostEqual(
                scroll.scroll_x, 0.0 if x == nx else 1.0,
                delta=dt
            )
            self.assertAlmostEqual(
                scroll.scroll_y, 1.0 if y == ny else 0.0,
                delta=dt
            )

            # reset scroll to original state
            scroll.scroll_x = 0.0
            scroll.scroll_y = 1.0

    def test_scrollbar_horizontal(self):
        EventLoop.ensure_window()
        win = EventLoop.window
        grid = TestGrid()
        scroll = TestScrollbarHorizontal()
        scroll.add_widget(grid)
        win.add_widget(scroll)

        # get widgets ready
        EventLoop.idle()

        left, right = scroll.to_window(scroll.x, scroll.right)
        bottom, top = scroll.to_window(scroll.y, scroll.top)

        points = [
            [left, bottom, right, bottom, 'bottom', 'right', False],
            [left, top, right, top, 'top', 'right', False]
        ]
        self.process_points(scroll, points)
        self.render(scroll)

    def test_scrollbar_vertical(self):
        EventLoop.ensure_window()
        win = EventLoop.window
        grid = TestGrid()
        scroll = TestScrollbarVertical()
        scroll.add_widget(grid)
        win.add_widget(scroll)

        # get widgets ready
        EventLoop.idle()

        left, right = scroll.to_window(scroll.x, scroll.right)
        bottom, top = scroll.to_window(scroll.y, scroll.top)

        points = [
            [right, top, right, bottom, 'bottom', 'right', False],
            [left, top, left, bottom, 'bottom', 'left', False]
        ]
        self.process_points(scroll, points)
        self.render(scroll)

    def test_scrollbar_both(self):
        EventLoop.ensure_window()
        win = EventLoop.window
        grid = TestGrid()
        scroll = TestScrollbarBoth()
        scroll.add_widget(grid)
        win.add_widget(scroll)

        # get widgets ready
        EventLoop.idle()

        left, right = scroll.to_window(scroll.x, scroll.right)
        bottom, top = scroll.to_window(scroll.y, scroll.top)

        points = [
            [left, bottom, right, bottom, 'bottom', 'right', False],
            [left, top, right, top, 'top', 'right', False],
            [right, top, right, bottom, 'bottom', 'right', False],
            [left, top, left, bottom, 'bottom', 'left', False]
        ]
        self.process_points(scroll, points)
        self.render(scroll)

    def test_scrollbar_horizontal_margin(self):
        EventLoop.ensure_window()
        win = EventLoop.window
        grid = TestGrid()
        scroll = TestScrollbarHorizontalMargin()
        margin = scroll.bar_margin
        scroll.add_widget(grid)
        win.add_widget(scroll)

        # get widgets ready
        EventLoop.idle()

        left, right = scroll.to_window(scroll.x, scroll.right)
        bottom, top = scroll.to_window(scroll.y, scroll.top)

        # touch in the half of the bar
        m = margin + scroll.bar_width / 2.0
        points = [
            [left, bottom + m, right, bottom + m, 'bottom', 'right', False],
            [left, top - m, right, top - m, 'top', 'right', False],
            [left, bottom, right, bottom, 'bottom', 'right', True],
            [left, top, right, top, 'top', 'right', True]
        ]
        self.process_points(scroll, points)
        self.render(scroll)

    def test_scrollbar_vertical_margin(self):
        EventLoop.ensure_window()
        win = EventLoop.window
        grid = TestGrid()
        scroll = TestScrollbarVerticalMargin()
        margin = scroll.bar_margin
        scroll.add_widget(grid)
        win.add_widget(scroll)

        # get widgets ready
        EventLoop.idle()

        left, right = scroll.to_window(scroll.x, scroll.right)
        bottom, top = scroll.to_window(scroll.y, scroll.top)

        # touch in the half of the bar
        m = margin + scroll.bar_width / 2.0
        points = [
            [right - m, top, right - m, bottom, 'bottom', 'right', False],
            [left + m, top, left + m, bottom, 'bottom', 'left', False],
            [right, top, right, bottom, 'bottom', 'right', True],
            [left, top, left, bottom, 'bottom', 'left', True]
        ]
        self.process_points(scroll, points)
        self.render(scroll)

    def test_scrollbar_both_margin(self):
        EventLoop.ensure_window()
        win = EventLoop.window
        grid = TestGrid()
        scroll = TestScrollbarBothMargin()
        margin = scroll.bar_margin
        scroll.add_widget(grid)
        win.add_widget(scroll)

        # get widgets ready
        EventLoop.idle()

        left, right = scroll.to_window(scroll.x, scroll.right)
        bottom, top = scroll.to_window(scroll.y, scroll.top)

        # touch in the half of the bar
        m = margin + scroll.bar_width / 2.0
        points = [
            [left, bottom + m, right, bottom + m, 'bottom', 'right', False],
            [left, top - m, right, top - m, 'top', 'right', False],
            [right - m, top, right - m, bottom, 'bottom', 'right', False],
            [left + m, top, left + m, bottom, 'bottom', 'left', False],
            [left, bottom, right, bottom, 'bottom', 'right', True],
            [left, top, right, top, 'top', 'right', True],
            [right, top, right, bottom, 'bottom', 'right', True],
            [left, top, left, bottom, 'bottom', 'left', True]
        ]
        self.process_points(scroll, points)
        self.render(scroll)


if __name__ == '__main__':
    import unittest
    unittest.main()
