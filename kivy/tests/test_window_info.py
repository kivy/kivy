from kivy.tests.common import GraphicUnitTest
from kivy import setupconfig


class WindowInfoTest(GraphicUnitTest):
    def test_window_info_nonzero(self):
        from kivy.core.window import Window
        window_info = Window.get_window_info()
        if window_info is None:
            return

        if setupconfig.USE_X11:
            from kivy.core.window.window_info import WindowInfoX11
            if isinstance(window_info, WindowInfoX11):
                self.assertNotEqual(window_info.display, 0)
                self.assertNotEqual(window_info.window, 0)

        if setupconfig.USE_WAYLAND:
            from kivy.core.window.window_info import WindowInfoWayland
            if isinstance(window_info, WindowInfoWayland):
                self.assertNotEqual(window_info.display, 0)
                self.assertNotEqual(window_info.surface, 0)
                self.assertNotEqual(window_info.shell_surface, 0)

        if setupconfig.PLATFORM == 'win32':
            from kivy.core.window.window_info import WindowInfoWindows
            if isinstance(window_info, WindowInfoWindows):
                self.assertNotEqual(window_info.window, 0)
                self.assertNotEqual(window_info.hdc, 0)
