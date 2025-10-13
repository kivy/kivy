"""
Tests for ButtonBehavior
========================
"""

import unittest
from unittest.mock import Mock

from kivy.tests.common import GraphicUnitTest
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior


class BasicButton(ButtonBehavior, Widget):
    """Simple button implementation for testing"""

    pass


class ButtonBehaviorTestCase(GraphicUnitTest):
    """Test cases for ButtonBehavior"""

    def setUp(self):
        super().setUp()
        self.button = BasicButton(
            pos=(0, 0), size_hint=(None, None), size=(100, 100)
        )

    def tearDown(self):
        super().tearDown()
        self.button = None

    def test_initial_state(self):
        """Test button initial properties"""
        self.assertFalse(self.button.pressed)
        self.assertFalse(self.button.always_release)

    def test_press_state(self):
        """Test button pressed state changes"""
        self.assertFalse(self.button.pressed)

        self.button._do_press()
        self.assertTrue(self.button.pressed)

        self.button._do_release()
        self.assertFalse(self.button.pressed)

    def test_on_press_event(self):
        """Test on_press event is fired"""
        callback = Mock()
        self.button.bind(on_press=callback)

        touch = Mock()
        touch.is_mouse_scrolling = False
        touch.x, touch.y = 50, 50  # Inside button
        touch.ud = {}
        touch.grab_current = None

        self.button.on_touch_down(touch)

        callback.assert_called_once()
        self.assertTrue(self.button.pressed)

    def test_on_release_event(self):
        """Test on_release event is fired"""
        callback = Mock()
        self.button.bind(on_release=callback)

        touch = Mock()
        touch.is_mouse_scrolling = False
        touch.x, touch.y = 50, 50  # Inside button
        touch.pos = (50, 50)
        touch.ud = {}
        touch.grab_current = None

        self.button.on_touch_down(touch)
        touch.grab_current = self.button
        self.button.on_touch_up(touch)

        callback.assert_called_once()
        self.assertFalse(self.button.pressed)

    def test_touch_outside_no_release(self):
        """Test no release when touch_up is outside and always_release=False"""
        callback = Mock()
        self.button.bind(on_release=callback)
        self.button.always_release = False

        touch = Mock()
        touch.is_mouse_scrolling = False
        touch.x, touch.y = 50, 50  # Inside button
        touch.ud = {}
        touch.grab_current = None

        self.button.on_touch_down(touch)
        touch.grab_current = self.button

        # Move touch outside
        touch.x, touch.y = 200, 200
        touch.pos = (200, 200)
        self.button.on_touch_up(touch)

        callback.assert_not_called()
        self.assertFalse(self.button.pressed)

    def test_always_release_true(self):
        """Test release fires even when touch_up is outside"""
        callback = Mock()
        self.button.bind(on_release=callback)
        self.button.always_release = True

        touch = Mock()
        touch.is_mouse_scrolling = False
        touch.x, touch.y = 50, 50  # Inside button
        touch.ud = {}
        touch.grab_current = None

        self.button.on_touch_down(touch)
        touch.grab_current = self.button

        # Move touch outside
        touch.x, touch.y = 200, 200
        touch.pos = (200, 200)
        self.button.on_touch_up(touch)

        callback.assert_called_once()
        self.assertFalse(self.button.pressed)

    def test_ignore_mouse_scrolling(self):
        """Test mouse scrolling is ignored"""
        touch = Mock()
        touch.is_mouse_scrolling = True
        touch.x, touch.y = 50, 50
        touch.ud = {}

        result = self.button.on_touch_down(touch)

        self.assertFalse(result)
        self.assertFalse(self.button.pressed)

    def test_ignore_touch_outside(self):
        """Test touch outside widget is ignored"""
        touch = Mock()
        touch.is_mouse_scrolling = False
        touch.x, touch.y = 200, 200  # Outside button
        touch.ud = {}

        result = self.button.on_touch_down(touch)

        self.assertFalse(result)
        self.assertFalse(self.button.pressed)

    def test_on_cancel_event(self):
        """Test on_cancel event is fired when touch moves outside bounds"""
        callback = Mock()
        self.button.bind(on_cancel=callback)

        touch = Mock()
        touch.is_mouse_scrolling = False
        touch.x, touch.y = 50, 50  # Inside button
        touch.ud = {}
        touch.grab_current = None

        self.button.on_touch_down(touch)
        touch.grab_current = self.button

        # Move touch outside button bounds
        touch.x, touch.y = 200, 200
        self.button.on_touch_move(touch)

        callback.assert_called_once()
        self.assertFalse(self.button.pressed)

    def test_on_cancel_not_fired_if_always_release(self):
        """Test on_cancel is NOT fired when always_release=True"""
        self.button.always_release = True
        callback = Mock()
        self.button.bind(on_cancel=callback)

        touch = Mock()
        touch.is_mouse_scrolling = False
        touch.x, touch.y = 50, 50  # Inside button
        touch.ud = {}
        touch.grab_current = None

        self.button.on_touch_down(touch)
        touch.grab_current = self.button

        # Move touch outside button bounds
        touch.x, touch.y = 200, 200
        self.button.on_touch_move(touch)

        callback.assert_not_called()

    def test_touch_grab_ungrab(self):
        """Test touch grab and ungrab calls"""
        touch = Mock()
        touch.is_mouse_scrolling = False
        touch.x, touch.y = 50, 50  # Inside button
        touch.pos = (50, 50)
        touch.ud = {}
        touch.grab_current = None

        self.button.on_touch_down(touch)
        touch.grab.assert_called_once_with(self.button)

        touch.grab_current = self.button
        self.button.on_touch_up(touch)
        touch.ungrab.assert_called_once_with(self.button)

    def test_on_press_override(self):
        """Test on_press can be overridden"""

        class CustomButton(ButtonBehavior, Widget):
            def on_press(self):
                self.custom_flag = True

        btn = CustomButton(pos=(0, 0), size=(100, 100))
        touch = Mock()
        touch.is_mouse_scrolling = False
        touch.x, touch.y = 50, 50  # Inside button
        touch.ud = {}

        btn.on_touch_down(touch)

        self.assertTrue(hasattr(btn, "custom_flag") and btn.custom_flag)

    def test_on_release_override(self):
        """Test on_release can be overridden"""

        class CustomButton(ButtonBehavior, Widget):
            def on_release(self):
                self.custom_flag = True

        btn = CustomButton(pos=(0, 0), size=(100, 100))
        touch = Mock()
        touch.is_mouse_scrolling = False
        touch.x, touch.y = 50, 50  # Inside button
        touch.pos = (50, 50)
        touch.ud = {}
        touch.grab_current = None

        btn.on_touch_down(touch)
        touch.grab_current = btn
        btn.on_touch_up(touch)

        self.assertTrue(hasattr(btn, "custom_flag") and btn.custom_flag)

    def test_on_cancel_override(self):
        """Test on_cancel can be overridden"""

        class CustomButton(ButtonBehavior, Widget):
            def on_cancel(self):
                self.custom_flag = True

        btn = CustomButton(pos=(0, 0), size=(100, 100))
        touch = Mock()
        touch.is_mouse_scrolling = False
        touch.x, touch.y = 50, 50  # Inside button
        touch.ud = {}
        touch.grab_current = None

        btn.on_touch_down(touch)
        touch.grab_current = btn

        # Move touch outside button bounds
        touch.x, touch.y = 200, 200
        btn.on_touch_move(touch)

        self.assertTrue(hasattr(btn, "custom_flag") and btn.custom_flag)


if __name__ == "__main__":
    unittest.main()
