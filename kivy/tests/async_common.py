import asyncio
import random
import time

from kivy.tests import UnitTestTouch

__all__ = ('UnitKivyApp', 'async_sleep')


try:
    import pytest_asyncio
    async_sleep = asyncio.sleep
except ImportError:
    try:
        import trio
        from pytest_trio import trio_fixture
        async_sleep = trio.sleep
    except ImportError:
        async_sleep = None


class AsyncUnitTestTouch(UnitTestTouch):

    def touch_down(self, *args):
        self.eventloop._dispatch_input("begin", self)

    def touch_move(self, x, y):
        win = self.eventloop.window
        self.move({
            "x": x / float(win.width),
            "y": y / float(win.height)
        })
        self.eventloop._dispatch_input("update", self)

    def touch_up(self, *args):
        self.eventloop._dispatch_input("end", self)


_base_widget_flag = object()


class UnitKivyApp(object):
    """Base class to use with async test apps.
    """

    app_has_started = False

    app_has_stopped = False

    resolved_widgets_cache = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.resolved_widgets_cache = {}

        def started_app(*largs):
            self.app_has_started = True
        self.fbind('on_start', started_app)

        def stopped_app(*largs):
            self.app_has_stopped = True
        self.fbind('on_stop', stopped_app)

    def resolve_widget(
            self, *match_funcs, base_widget=_base_widget_flag, **attrs):
        if base_widget is None:
            return None

        if base_widget is _base_widget_flag:
            base_widget = self.root

        for widget in base_widget.walk(restrict=True):
            if all(match(widget) for match in match_funcs):
                for attr, val in attrs.items():
                    if getattr(widget, attr, _base_widget_flag) != val:
                        break
                else:
                    return widget
        return None

    def resolve_widget_cached(
            self, *match_funcs, base_widget=_base_widget_flag, **attrs):
        if base_widget is None:
            return None

        key = match_funcs, base_widget, attrs
        widget = self.resolved_widgets_cache.get(key, None)
        if widget is not None:
            return widget

        widget = self.resolve_widget(
            *match_funcs, base_widget=base_widget, **attrs)
        if widget is None:
            return None

        self.resolved_widgets_cache[key] = widget
        return widget

    async def wait_clock_frames(self, n, sleep_time=1 / 60.):
        from kivy.clock import Clock
        frames_start = Clock.frames
        while Clock.frames < frames_start + n:
            await async_sleep(sleep_time)

    def get_widget_pos_pixel(self, widget, positions):
        from kivy.graphics import Fbo, ClearColor, ClearBuffers

        canvas_parent_index = -2
        if widget.parent is not None:
            canvas_parent_index = widget.parent.canvas.indexof(widget.canvas)
            if canvas_parent_index > -1:
                widget.parent.canvas.remove(widget.canvas)

        w, h = int(widget.width), int(widget.height)
        fbo = Fbo(size=(w, h), with_stencilbuffer=True)

        with fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()

        fbo.add(widget.canvas)
        fbo.draw()
        pixels = fbo.pixels
        fbo.remove(widget.canvas)

        if widget.parent is not None and canvas_parent_index > -1:
            widget.parent.canvas.insert(canvas_parent_index, widget.canvas)

        values = []
        for x, y in positions:
            x = int(x)
            y = int(y)
            i = y * w * 4 + x * 4
            values.append(tuple(pixels[i:i + 4]))

        return values

    async def do_touch_down_up(
            self, pos=None, widget=None, duration=.5, pos_jitter=None,
            widget_jitter=False, jitter_dt=1 / 15., end_on_pos=False):
        x, y = pos or widget.center
        touch = AsyncUnitTestTouch(x, y)

        ts = time.perf_counter()
        touch.touch_down()
        await self.wait_clock_frames(1)
        yield touch.pos, 'down'

        if not pos_jitter and not widget_jitter:
            await async_sleep(duration)
            touch.touch_up()
            await self.wait_clock_frames(1)
            yield touch.pos, 'move'

            return

        moved = False
        if pos_jitter:
            dx, dy = pos_jitter
        else:
            dx = widget.width / 2.
            dy = widget.height / 2.

        while time.perf_counter() - ts < duration:
            moved = True
            await async_sleep(jitter_dt)

            touch.touch_move(
                x + (random.random() * 2 - 1) * dx,
                y + (random.random() * 2 - 1) * dy
            )
            await self.wait_clock_frames(1)
            yield touch.pos, 'move'

        if end_on_pos and moved:
            touch.touch_move(x, y)
            await self.wait_clock_frames(1)
            yield touch.pos, 'move'

        touch.touch_up()
        await self.wait_clock_frames(1)
        yield touch.pos, 'up'

    async def do_touch_drag(
            self, pos=None, widget=None, target_pos=None, target_widget=None,
            duration=.5, drag_n=10):
        x, y = pos or widget.center
        tx, ty = target_pos or target_widget.center
        touch = AsyncUnitTestTouch(x, y)

        touch.touch_down()
        await self.wait_clock_frames(1)
        yield touch.pos, 'down'

        dx = (tx - x) / drag_n
        dy = (ty - y) / drag_n
        dt = duration / drag_n

        for i in range(drag_n):
            await async_sleep(dt)

            touch.touch_move(x + (i + 1) * dx, y + (i + 1) * dy)
            await self.wait_clock_frames(1)
            yield touch.pos, 'move'

        if touch.pos != target_pos:
            touch.touch_move(*target_pos)
            await self.wait_clock_frames(1)
            yield touch.pos, 'move'

        touch.touch_up()
        await self.wait_clock_frames(1)
        yield touch.pos, 'up'
