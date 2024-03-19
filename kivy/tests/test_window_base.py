from itertools import product

from kivy import setupconfig
from kivy.tests import GraphicUnitTest
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

        if setupconfig.USE_X11:
            self.assertNotEqual(native_handle, 0)

        if setupconfig.USE_WAYLAND:
            self.assertNotEqual(native_handle, 0)

        if setupconfig.PLATFORM == 'win32':
            self.assertNotEqual(native_handle, 0)
