"""
Tests for ButtonBehavior
========================
"""

import unittest
from unittest.mock import Mock

from kivy.tests.common import GraphicUnitTest
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget


def create_mock_touch(x=50, y=50, grab_current=None):
    touch = Mock()
    touch.is_mouse_scrolling = False
    touch.x, touch.y = x, y
    touch.pos = (x, y)
    touch.ud = {}
    if grab_current:
        touch.grab_current = grab_current
    return touch


class BasicButton(ButtonBehavior, Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.pos = (0, 0)
        self.size = (100, 100)


class ButtonBehaviorTestCase(GraphicUnitTest):
    """Test cases for ButtonBehavior"""

    def setUp(self):
        super().setUp()
        self.button = BasicButton()

    def tearDown(self):
        super().tearDown()
        self.button = None

    def test_event_hooks(self):
        """Test button event hooks exist"""
        self.assertTrue(hasattr(self.button, "_do_press"))
        self.assertTrue(hasattr(self.button, "_do_release"))
        self.assertTrue(hasattr(self.button, "_do_cancel"))

    def test_initial_state(self):
        """Test button initial properties"""
        self.assertFalse(self.button.pressed)
        self.assertFalse(self.button.always_release)

    def test_on_press_event(self):
        """Test on_press event is fired"""
        callback = Mock()
        self.button.bind(on_press=callback)

        touch = create_mock_touch()
        self.button.on_touch_down(touch)
        touch.grab_current = self.button
        self.button.on_touch_up(touch)

        callback.assert_called_once()
        self.assertFalse(self.button.pressed)

    def test_on_release_event(self):
        """Test on_release event is fired"""
        callback = Mock()
        self.button.bind(on_release=callback)

        touch = create_mock_touch()
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

        touch = create_mock_touch()
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

        touch = create_mock_touch()
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
        touch = create_mock_touch(x=200, y=200)
        result = self.button.on_touch_down(touch)

        self.assertFalse(result)
        self.assertFalse(self.button.pressed)

    def test_on_cancel_event(self):
        """Test on_cancel event is fired when touch moves outside bounds"""
        callback = Mock()
        self.button.bind(on_cancel=callback)

        touch = create_mock_touch()
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

        touch = create_mock_touch()
        self.button.on_touch_down(touch)
        touch.grab_current = self.button

        # Move touch outside button bounds
        touch.x, touch.y = 200, 200
        self.button.on_touch_move(touch)

        callback.assert_not_called()

    def test_touch_grab_ungrab(self):
        """Test touch grab and ungrab calls"""
        touch = create_mock_touch()
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
        touch = create_mock_touch()
        btn.on_touch_down(touch)

        self.assertTrue(hasattr(btn, "custom_flag") and btn.custom_flag)

    def test_on_release_override(self):
        """Test on_release can be overridden"""

        class CustomButton(ButtonBehavior, Widget):
            def on_release(self):
                self.custom_flag = True

        btn = CustomButton(pos=(0, 0), size=(100, 100))
        touch = create_mock_touch()
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
        touch = create_mock_touch()
        btn.on_touch_down(touch)
        touch.grab_current = btn
        # Move touch outside button bounds
        touch.x, touch.y = 200, 200
        btn.on_touch_move(touch)
        self.assertTrue(hasattr(btn, "custom_flag") and btn.custom_flag)

    def test_multiple_touches_only_one_press(self):
        """Test on_press fires only once with multiple touches"""
        callback = Mock()
        self.button.bind(on_press=callback)

        # First touch
        touch1 = create_mock_touch(x=30, y=30)
        self.button.on_touch_down(touch1)
        self.assertTrue(self.button.pressed)

        # Second touch
        touch2 = create_mock_touch(x=60, y=60)
        self.button.on_touch_down(touch2)
        self.assertTrue(self.button.pressed)

        # on_press should be called only once
        callback.assert_called_once()

    def test_release_only_after_all_touches_released(self):
        """Test on_release fires only when ALL touches are released"""
        callback = Mock()
        self.button.bind(on_release=callback)

        # First touch down
        touch1 = create_mock_touch(x=30, y=30)
        self.button.on_touch_down(touch1)
        touch1.grab_current = self.button

        # Second touch down
        touch2 = create_mock_touch(x=60, y=60)
        self.button.on_touch_down(touch2)
        touch2.grab_current = self.button

        # Release first touch - on_release should NOT fire yet
        self.button.on_touch_up(touch1)
        callback.assert_not_called()
        self.assertTrue(self.button.pressed)

        # Release second touch - NOW on_release should fire
        self.button.on_touch_up(touch2)
        callback.assert_called_once()
        self.assertFalse(self.button.pressed)

    def test_pressed_state_with_multiple_touches(self):
        """Test pressed state remains True while any touch is active"""
        # Initial state
        self.assertFalse(self.button.pressed)

        # First touch
        touch1 = create_mock_touch(x=30, y=30)
        self.button.on_touch_down(touch1)
        self.assertTrue(self.button.pressed)

        # Second touch
        touch2 = create_mock_touch(x=60, y=60)
        self.button.on_touch_down(touch2)
        self.assertTrue(self.button.pressed)

        # Third touch
        touch3 = create_mock_touch(x=45, y=45)
        self.button.on_touch_down(touch3)
        self.assertTrue(self.button.pressed)

        # Release first touch - still pressed
        touch1.grab_current = self.button
        self.button.on_touch_up(touch1)
        self.assertTrue(self.button.pressed)

        # Release second touch - still pressed
        touch2.grab_current = self.button
        self.button.on_touch_up(touch2)
        self.assertTrue(self.button.pressed)

        # Release last touch - now not pressed
        touch3.grab_current = self.button
        self.button.on_touch_up(touch3)
        self.assertFalse(self.button.pressed)

    def test_cancel_with_multiple_touches(self):
        """Test on_cancel fires when last active touch moves outside"""
        callback = Mock()
        self.button.bind(on_cancel=callback)
        self.button.always_release = False

        # Two touches down
        touch1 = create_mock_touch(x=30, y=30)
        self.button.on_touch_down(touch1)
        touch1.grab_current = self.button

        touch2 = create_mock_touch(x=60, y=60)
        self.button.on_touch_down(touch2)
        touch2.grab_current = self.button

        # Move first touch outside - should NOT fire on_cancel yet
        touch1.x, touch1.y = 200, 200
        self.button.on_touch_move(touch1)
        callback.assert_not_called()
        self.assertTrue(self.button.pressed)

        # Move second touch outside - NOW should fire on_cancel
        touch2.x, touch2.y = 200, 200
        self.button.on_touch_move(touch2)
        callback.assert_called_once()
        self.assertFalse(self.button.pressed)

    def test_mixed_release_and_cancel_multitouch(self):
        """Test mixed scenario: some touches released inside, some cancelled"""
        on_release = Mock()
        on_cancel = Mock()
        self.button.bind(on_release=on_release, on_cancel=on_cancel)
        self.button.always_release = False

        # Three touches down
        touch1 = create_mock_touch(x=30, y=30)
        self.button.on_touch_down(touch1)
        touch1.grab_current = self.button

        touch2 = create_mock_touch(x=60, y=60)
        self.button.on_touch_down(touch2)
        touch2.grab_current = self.button

        touch3 = create_mock_touch(x=45, y=45)
        self.button.on_touch_down(touch3)
        touch3.grab_current = self.button

        # Cancel first touch (move outside)
        touch1.x, touch1.y = 200, 200
        self.button.on_touch_move(touch1)
        on_cancel.assert_not_called()  # Still have active touches

        # Release second touch inside bounds
        self.button.on_touch_up(touch2)
        on_release.assert_not_called()  # Still have active touches

        # Cancel last touch
        touch3.x, touch3.y = 250, 250
        self.button.on_touch_move(touch3)
        on_cancel.assert_called_once()  # NOW cancel fires
        on_release.assert_not_called()  # Should NOT fire release
        self.assertFalse(self.button.pressed)


if __name__ == "__main__":
    unittest.main()
