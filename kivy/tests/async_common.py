import asyncio
import random
import time
from collections import deque

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

    def __init__(self, *largs, **kwargs):
        self.grab_exclusive_class = None
        self.is_touch = True
        super(AsyncUnitTestTouch, self).__init__(*largs, **kwargs)

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


_unique_value = object


class WidgetResolver(object):
    """It assumes that the widget tree strictly forms a DAG.
    """

    base_widget = None

    matched_widget = None

    _kwargs_filter = {}

    _funcs_filter = []

    def __init__(self, base_widget, **kwargs):
        self.base_widget = base_widget
        self._kwargs_filter = {}
        self._funcs_filter = []
        super(WidgetResolver, self).__init__(**kwargs)

    def __call__(self):
        if self.matched_widget is not None:
            return self.matched_widget

        if not self._kwargs_filter and not self._funcs_filter:
            return self.base_widget
        return None

    def match(self, **kwargs_filter):
        self._kwargs_filter.update(kwargs_filter)

    def match_funcs(self, funcs_filter=()):
        self._funcs_filter.extend(funcs_filter)

    def check_widget(self, widget):
        if not all(func(widget) for func in self._funcs_filter):
            return False

        for attr, val in self._kwargs_filter.items():
            if getattr(widget, attr, _unique_value) != val:
                return False

        return True

    def not_found(self, op):
        raise ValueError(
            'Cannot find widget matching <{}, {}> starting from base '
            'widget "{}" doing "{}" traversal'.format(
                self._kwargs_filter, self._funcs_filter, self.base_widget, op))

    def down(self, **kwargs_filter):
        self.match(**kwargs_filter)
        check = self.check_widget

        fifo = deque([self.base_widget])
        while fifo:
            widget = fifo.popleft()
            if check(widget):
                return WidgetResolver(base_widget=widget)

            fifo.extend(widget.children)

        self.not_found('down')

    def up(self, **kwargs_filter):
        self.match(**kwargs_filter)
        check = self.check_widget

        parent = self.base_widget
        while parent is not None:
            if check(parent):
                return WidgetResolver(base_widget=parent)

            new_parent = parent.parent
            # Window is its own parent oO
            if new_parent is parent:
                break
            parent = new_parent

        self.not_found('up')

    def family_up(self, **kwargs_filter):
        self.match(**kwargs_filter)
        check = self.check_widget

        base_widget = self.base_widget
        already_checked_base = None
        while base_widget is not None:
            fifo = deque([base_widget])
            while fifo:
                widget = fifo.popleft()
                # don't check the child we checked before moving up
                if widget is already_checked_base:
                    continue

                if check(widget):
                    return WidgetResolver(base_widget=widget)

                fifo.extend(widget.children)

            already_checked_base = base_widget
            new_base_widget = base_widget.parent
            # Window is its own parent oO
            if new_base_widget is base_widget:
                break
            base_widget = new_base_widget

        self.not_found('family_up')


class UnitKivyApp(object):
    """Base class to use with async test apps.
    """

    app_has_started = False

    app_has_stopped = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        def started_app(*largs):
            self.app_has_started = True
        self.fbind('on_start', started_app)

        def stopped_app(*largs):
            self.app_has_stopped = True
        self.fbind('on_stop', stopped_app)

    def resolve_widget(self, base_widget=None):
        if base_widget is None:
            from kivy.core.window import Window
            base_widget = Window
        return WidgetResolver(base_widget=base_widget)

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
            self, pos=None, widget=None, duration=.2, pos_jitter=None,
            widget_jitter=False, jitter_dt=1 / 15., end_on_pos=False):
        x, y = pos or widget.to_window(*widget.center)
        touch = AsyncUnitTestTouch(x, y)

        ts = time.perf_counter()
        touch.touch_down()
        await self.wait_clock_frames(1)
        yield 'down', touch.pos

        if not pos_jitter and not widget_jitter:
            await async_sleep(duration)
            touch.touch_up()
            await self.wait_clock_frames(1)
            yield 'move', touch.pos

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
            yield 'move', touch.pos

        if end_on_pos and moved:
            touch.touch_move(x, y)
            await self.wait_clock_frames(1)
            yield 'move', touch.pos

        touch.touch_up()
        await self.wait_clock_frames(1)
        yield 'up', touch.pos

    async def do_touch_drag(
            self, pos=None, widget=None, target_pos=None, target_widget=None,
            dx=0, dy=0, duration=.2, drag_n=10):
        x, y = pos or widget.to_window(*widget.center)
        if target_pos is not None:
            tx, ty = target_pos
        elif target_widget is not None:
            tx, ty = target_pos = target_widget.to_window(
                *target_widget.center)
        else:
            tx, ty = target_pos = x + dx, y + dy

        touch = AsyncUnitTestTouch(x, y)

        touch.touch_down()
        await self.wait_clock_frames(1)
        yield 'down', touch.pos

        dx = (tx - x) / drag_n
        dy = (ty - y) / drag_n
        dt = duration / drag_n

        for i in range(drag_n):
            await async_sleep(dt)

            touch.touch_move(x + (i + 1) * dx, y + (i + 1) * dy)
            await self.wait_clock_frames(1)
            yield 'move', touch.pos

        if touch.pos != target_pos:
            touch.touch_move(*target_pos)
            await self.wait_clock_frames(1)
            yield 'move', touch.pos

        touch.touch_up()
        await self.wait_clock_frames(1)
        yield 'up', touch.pos

    async def do_keyboard_key(
            self, key, modifiers=(), duration=.2, num_press=1):
        from kivy.core.window import Window
        key_code = Window._system_keyboard.string_to_keycode(key.lower())

        known_modifiers = (
            'shift', 'alt', 'ctrl', 'meta', 'numlock', 'capslock')
        special_keys = {
            27: 'escape',
            9: 'tab',
            8: 'backspace',
            13: 'enter',
            127: 'del',
            271: 'enter',
            273: 'up',
            274: 'down',
            275: 'right',
            276: 'left',
            278: 'home',
            279: 'end',
            280: 'pgup',
            281: 'pgdown'}

        text = None
        if (key not in modifiers and key not in known_modifiers and
                key_code not in special_keys):
            try:
                text = chr(key_code)
            except ValueError:
                pass

        dt = duration / num_press
        for i in range(num_press):
            await async_sleep(dt)

            Window.dispatch('on_key_down', key_code, 0, text, modifiers)
            Window.dispatch('on_textinput', key)
            await self.wait_clock_frames(1)
            yield 'down', (key, key_code, 0, text, modifiers)

        Window.dispatch('on_key_up', key_code, 0)
        await self.wait_clock_frames(1)
        yield 'up', (key, key_code, 0, text, modifiers)
