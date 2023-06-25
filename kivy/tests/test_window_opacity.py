from kivy.tests.common import GraphicUnitTest


class WindowOpacityTest(GraphicUnitTest):

    def test_window_opacity_property(self):
        from kivy.core.window import Window
        
        opacity = 0.5
        Window.opacity = opacity
        self.assertEqual(Window.opacity, opacity)

        from kivy.logger import LoggerHistory
        
        Window.opacity = 15
        self.assertEqual(LoggerHistory.history[0].msg, 
                         'Window: The opacity value of '
                         'the window should be in the '
                         'range from 0.0 to 1.0.')
        
        LoggerHistory.clear_history()
        
        Window.opacity = -15
        assert len(LoggerHistory.history) == 1

