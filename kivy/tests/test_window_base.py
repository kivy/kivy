import os
import sys
import tempfile
import types
from itertools import product
from unittest import mock

import pytest

from kivy import setupconfig
from kivy.tests import GraphicUnitTest
from kivy.tests.common import requires_graphics, UTMotionEvent
from kivy.logger import LoggerHistory


class WindowBaseTest(GraphicUnitTest):

    def test_to_normalized_pos(self):
        win = self.Window
        old_system_size = win.system_size[:]
        win.system_size = w, h = type(old_system_size)((320, 240))
        try:
            for x, y in product([0, 319, 50, 51], [0, 239, 50, 51]):
                expected_sx = x / (w - 1.0)
                expected_sy = y / (h - 1.0)
                result_sx, result_sy = win.to_normalized_pos(x, y)
                assert result_sx == expected_sx
                assert result_sy == expected_sy
        finally:
            win.system_size = old_system_size


class WindowSoftinputTest(GraphicUnitTest):
    """softinput_mode with a mobile system keyboard (kivy/kivy#9363)."""

    def setUp(self):
        super().setUp()
        from kivy.uix.widget import Widget

        win = self.Window
        self._kb = {'height': 0.0}
        mobile = types.ModuleType('kivy.mobile')
        mobile.get_keyboard_height = lambda: self._kb['height']
        self._patches = [
            mock.patch.dict(sys.modules, {'kivy.mobile': mobile}),
            mock.patch('kivy.core.window.platform', 'android'),
        ]
        for p in self._patches:
            p.start()
        self.target = Widget(size_hint=(None, None), size=(100, 40))
        win.add_widget(self.target)
        win.softinput_mode = 'below_target'

    def tearDown(self):
        win = self.Window
        self.show_keyboard(0, target=None)
        win.softinput_mode = ''
        win.remove_widget(self.target)
        for p in reversed(self._patches):
            p.stop()
        win._keyboard_changed = not win._keyboard_changed
        super().tearDown()

    def show_keyboard(self, height, target):
        """Settle the IME at *height* without waiting for the animation."""
        win = self.Window
        win._system_keyboard.target = target
        self._kb['height'] = height
        win._kheight = height
        win._keyboard_changed = not win._keyboard_changed
        win.update_viewport()

    def drawn_offset(self):
        return self.Window.render_context['modelview_mat'].get()[13]

    def touch_y(self, y):
        win = self.Window
        w, h = win.unrotated_size
        me = UTMotionEvent('unittest', 1, {'x': 0.5, 'y': y / (h - 1.0)})
        win.transform_motion_event_2d(me)
        return me.y

    def test_target_above_keyboard_is_not_offset(self):
        self.target.y = 150
        self.show_keyboard(100, target=self.target)
        assert self.Window.keyboard_height == 100
        assert self.drawn_offset() == 0
        assert self.touch_y(170) == pytest.approx(170)

    def test_target_behind_keyboard_touch_follows_content(self):
        self.target.y = 20
        self.show_keyboard(100, target=self.target)
        assert self.drawn_offset() == 80
        # a tap on the drawn target lands on the widget
        assert self.target.collide_point(0, self.touch_y(20 + 80 + 10))

    def test_no_target_is_not_offset(self):
        # focus was lost but keyboard_height has not caught up yet
        self.target.y = 150
        self.show_keyboard(100, target=None)
        assert self.drawn_offset() == 0
        assert self.touch_y(170) == pytest.approx(170)

    def test_vkeyboard_height_is_already_target_relative(self):
        win = self.Window
        with mock.patch.object(win, 'allow_vkeyboard', True):
            self.show_keyboard(60, target=None)
            assert self.drawn_offset() == 60
            assert self.touch_y(170) == pytest.approx(110)

    def test_system_pan_leaves_content_in_place(self):
        win = self.Window
        self.target.y = 20
        with mock.patch.object(win, '_system_pans_softinput', True):
            for mode in ('pan', 'below_target'):
                win.softinput_mode = mode
                self.show_keyboard(100, target=self.target)
                assert self.drawn_offset() == 0, mode
                assert self.touch_y(30) == pytest.approx(30), mode

    def test_system_pan_viewport_before_keyboards_configured(self):
        # create_window() calls update_viewport() before
        # configure_keyboards() sets allow_vkeyboard
        win = self.Window
        win.softinput_mode = ''
        allow_vkeyboard = win.allow_vkeyboard
        del win.allow_vkeyboard
        try:
            with mock.patch.object(win, '_system_pans_softinput', True):
                win.update_viewport()
        finally:
            win.allow_vkeyboard = allow_vkeyboard

    def test_system_pan_keeps_vkeyboard_offset(self):
        win = self.Window
        with mock.patch.object(win, '_system_pans_softinput', True), \
                mock.patch.object(win, 'allow_vkeyboard', True):
            self.show_keyboard(60, target=None)
            assert self.drawn_offset() == 60


class WindowScreenshotTest(GraphicUnitTest):

    @requires_graphics
    def test_screenshot_saves_png(self):
        Image = pytest.importorskip('PIL.Image')
        from kivy.graphics import Color, Rectangle
        from kivy.uix.widget import Widget

        win = self.Window
        if type(win).__name__ != 'WindowSDL':
            pytest.skip('Window.screenshot() is only implemented for SDL3')

        # A blue top-left quadrant on red catches flipped or garbled rows.
        win.clearcolor = (1, 0, 0, 1)
        widget = Widget()
        with widget.canvas:
            Color(0, 0, 1, 1)
            Rectangle(pos=(0, win.height / 2),
                      size=(win.width / 2, win.height / 2))
        win.add_widget(widget)
        try:
            # Take the screenshot after the frame was presented, when the
            # back buffer may be undefined (e.g. ANGLE/Metal).
            self.advance_frames(2)
            with tempfile.TemporaryDirectory() as tmpdir:
                path = win.screenshot(name=os.path.join(tmpdir, 'shot.png'))
                assert os.path.exists(path)
                with Image.open(path) as img:
                    img = img.convert('RGB')
                    w, h = img.size
                    assert (w, h) == tuple(win.size)
                    assert img.getpixel((w // 4, h // 4)) == (0, 0, 255)
                    assert img.getpixel((3 * w // 4, h // 4)) == (255, 0, 0)
                    assert img.getpixel((w // 4, 3 * h // 4)) == (255, 0, 0)
                    assert img.getpixel((3 * w // 4, 3 * h // 4)) == (
                        255, 0, 0)
        finally:
            win.remove_widget(widget)


class WindowRotationTest(GraphicUnitTest):

    def test_rotation_sizes(self):
        win = self.Window
        win.system_size = 320, 240

        for rotation in (0, 90, 180, 270):
            win.rotation = rotation

            # Comparison should be performed with unrotated size
            # as it also takes into account the window density
            w, h = win.unrotated_size
            if rotation in (90, 270):
                w, h = h, w

            assert win.size == (w, h)


class WindowUnrotatedSizeTest(GraphicUnitTest):

    def test_unrotated_size(self):
        win = self.Window
        win.system_size = 320, 240

        # This is automatically set by the window provider, but we can
        # force it manually for this specific test
        win._density = 3.0

        assert win.unrotated_size == (960, 720)


class WindowSizeTest(GraphicUnitTest):

    def test_window_size_property(self):
        win = self.Window

        # Test that setting the size property to 100, 100
        # sets the system_size to 100, 100 when the window is not rotated
        # and the density is 1.0
        win.rotation = 0
        win._density = 1.0
        win.size = 100, 100
        assert win.system_size == [100, 100]

        # Test that setting the size property to 100, 50 sets the system_size
        # to 50, 100 when the window is rotated 90 degrees and the density is
        # 1.0
        win.rotation = 90
        win._density = 1.0
        win.size = 100, 50
        assert win.system_size == [50, 100]

        # Test that setting the size property to 200, 100 sets the system_size
        # to 100, 50 when the window is unrotated and the density is 2.0
        win.rotation = 0
        win._density = 2.0
        win.size = 200, 100
        assert win.system_size == [100, 50]

        # Test that setting the size property to 100, 200 sets the system_size
        # to 100, 50 when the window is rotated 90 degrees and the density is
        # 2.0
        win.rotation = 90
        win._density = 2.0
        win.size = 100, 200
        assert win.system_size == [100, 50]


class WindowOpacityTest(GraphicUnitTest):

    def setUp(self):
        super().setUp()
        self._prev_window_opacity = self.Window.opacity
        self._prev_history = LoggerHistory.history[:]

    def tearDown(self):
        self.Window.opacity = self._prev_window_opacity
        LoggerHistory.history[:] = self._prev_history
        super().tearDown()

    def get_new_opacity_value(self):
        opacity = self.Window.opacity
        opacity = opacity - 0.1 if opacity >= 0.9 else opacity + 0.1
        return round(opacity, 2)

    def check_opacity_support(self):
        LoggerHistory.clear_history()
        self.Window.opacity = self.get_new_opacity_value()
        return not LoggerHistory.history

    def test_window_opacity_property(self):
        if self.check_opacity_support():
            opacity = self.get_new_opacity_value()
            self.Window.opacity = opacity
            self.assertEqual(self.Window.opacity, opacity)

    def test_window_opacity_clamping_positive(self):
        if self.check_opacity_support():
            self.Window.opacity = 1.5
            self.assertEqual(self.Window.opacity, 1.0)

    def test_window_opacity_clamping_negative(self):
        if self.check_opacity_support():
            self.Window.opacity = -1.5
            self.assertEqual(self.Window.opacity, 0.0)


class WindowNativeHandleTest(GraphicUnitTest):

    def test_native_handle_non_zero(self):
        win = self.Window
        native_handle = win.native_handle

        # The native handle is implemented on all the (known)
        # supported platforms, if it is not implemented we likely do
        # not have a WindowInfo implementation, and returns None
        self.assertNotEqual(native_handle, None)

        # Even if we have a WindowInfo implementation, and therefore
        # is not None, if returns 0, it means something is wrong.
        self.assertNotEqual(native_handle, 0)


class WindowSystemThemeTest(GraphicUnitTest):
    def test_get_system_theme_exists(self):
        """Test that the get_system_theme method exists and returns a string."""
        win = self.Window
        theme = win.get_system_theme()
        self.assertIsInstance(theme, str)
        self.assertIn(theme, ["light", "dark", "unknown"])

        print(f"Detected system theme: {theme}")

    def test_get_system_theme_valid_value(self):
        """Test that get_system_theme returns a valid theme when available."""
        win = self.Window
        theme = win.get_system_theme()

        # Skip the test if the system returns "unknown"
        if theme == "unknown":
            self.skipTest(
                "System theme detection is not available on this platform"
            )

        # We expect a valid theme: either 'light' or 'dark'
        self.assertIn(theme, ["light", "dark"])
