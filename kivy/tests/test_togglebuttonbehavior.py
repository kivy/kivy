import gc
import unittest
import weakref
from unittest.mock import Mock

from kivy.clock import Clock
from kivy.tests.common import GraphicUnitTest
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.label import Label


def create_mock_touch(x=50, y=50, grab_current=None):
    touch = Mock()
    touch.is_mouse_scrolling = False
    touch.x, touch.y = x, y
    touch.pos = (x, y)
    touch.ud = {}
    if grab_current:
        touch.grab_current = grab_current
    return touch


class BasicToggleButton(ToggleButtonBehavior, Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.pos = (0, 0)
        self.size = (100, 100)


class ToggleButtonBehaviorTest(GraphicUnitTest):
    """Complete test suite for ToggleButtonBehavior"""

    def setUp(self):
        """Clear all groups before each test"""
        super().setUp()
        ToggleButtonBehavior._toggle_groups.clear()

    # Basic functionality tests

    def test_event_hooks(self):
        """Test ButtonBehavior event hooks exist"""
        btn = BasicToggleButton()
        self.assertTrue(hasattr(btn, "_do_press"))
        self.assertTrue(hasattr(btn, "_do_release"))
        self.assertTrue(hasattr(btn, "_do_cancel"))

    def test_basic_toggle(self):
        """Test manual toggle via 'activated' property"""
        btn = BasicToggleButton()
        self.assertFalse(btn.activated)
        btn.activated = True
        self.assertTrue(btn.activated)
        btn.activated = False
        self.assertFalse(btn.activated)

    # Toggle timing tests (toggle_on property)

    def test_default_toggle_on_release(self):
        """Test default toggle_on='release' behavior"""
        btn = BasicToggleButton()
        self.assertEqual(btn.toggle_on, "release")

        touch = create_mock_touch(grab_current=btn)

        self.assertFalse(btn.activated)
        btn.on_touch_down(touch)
        self.assertFalse(btn.activated)
        btn.on_touch_up(touch)
        self.assertTrue(btn.activated)

    def test_default_toggle_on_press(self):
        """Test toggle_on='press' behavior"""
        btn = BasicToggleButton()
        btn.toggle_on = "press"
        self.assertEqual(btn.toggle_on, "press")

        touch = create_mock_touch(grab_current=btn)

        self.assertFalse(btn.activated)
        btn.on_touch_down(touch)
        self.assertTrue(btn.activated)
        btn.on_touch_up(touch)
        self.assertTrue(btn.activated)

    def test_runtime_toggle_on_change(self):
        """Test dynamic toggle_on reassignment changes behavior"""
        btn = BasicToggleButton()
        self.assertEqual(btn.toggle_on, "release")

        # Default behavior (release)
        touch = create_mock_touch(grab_current=btn)
        self.assertFalse(btn.activated)
        btn.on_touch_down(touch)
        self.assertFalse(btn.activated)
        btn.on_touch_up(touch)
        self.assertTrue(btn.activated)

        # Switch to press
        btn.toggle_on = "press"
        touch = create_mock_touch(grab_current=btn)

        self.assertTrue(btn.activated)
        btn.on_touch_down(touch)
        self.assertFalse(btn.activated)
        btn.on_touch_up(touch)
        self.assertFalse(btn.activated)

        # Switch back to release
        btn.toggle_on = "release"
        touch = create_mock_touch(grab_current=btn)

        self.assertFalse(btn.activated)
        btn.on_touch_down(touch)
        self.assertFalse(btn.activated)
        btn.on_touch_up(touch)
        self.assertTrue(btn.activated)

    # Group behavior tests

    def test_group_mutual_exclusion_via_property(self):
        """Test mutual exclusion between buttons in the same group"""
        btn1 = BasicToggleButton(group="test")
        btn2 = BasicToggleButton(group="test")

        btn1.activated = True
        self.assertTrue(btn1.activated)
        self.assertFalse(btn2.activated)

        btn2.activated = True
        self.assertTrue(btn2.activated)
        self.assertFalse(btn1.activated)

    def test_group_mutual_exclusion_via_touch(self):
        """Test mutual exclusion between buttons in the same group via touch"""
        btn1 = BasicToggleButton(group="test")
        btn2 = BasicToggleButton(group="test")

        # Activate the first button via touch
        touch1 = create_mock_touch(grab_current=btn1)
        btn1.on_touch_down(touch1)
        btn1.on_touch_up(touch1)

        self.assertTrue(btn1.activated)
        self.assertFalse(btn2.activated)

        # Now toggle the second button via touch
        touch2 = create_mock_touch(grab_current=btn2)
        btn2.on_touch_down(touch2)
        btn2.on_touch_up(touch2)

        # Expected behavior: the second button becomes activated,
        # the first deactivates
        self.assertTrue(btn2.activated)
        self.assertFalse(btn1.activated)

    def test_scoped_groups_are_independent(self):
        """Test scoped group isolation"""
        owner1, owner2 = Label(), Label()
        btn1a = BasicToggleButton(group=(owner1, "g"))
        btn1b = BasicToggleButton(group=(owner1, "g"))
        btn2a = BasicToggleButton(group=(owner2, "g"))
        btn2b = BasicToggleButton(group=(owner2, "g"))

        btn1a.activated = True
        self.assertTrue(btn1a.activated)
        self.assertFalse(btn1b.activated)
        self.assertFalse(btn2a.activated)
        self.assertFalse(btn2b.activated)

        btn2a.activated = True
        self.assertTrue(btn1a.activated)
        self.assertTrue(btn2a.activated)

    def test_group_change_reassigns_correctly(self):
        """Changing group should rebind correctly"""
        btn1 = BasicToggleButton(group="g1", activated=True)
        btn2 = BasicToggleButton(group="g1")
        btn3 = BasicToggleButton(group="g2")

        btn1.group = "g2"
        btn2.activated = True

        self.assertTrue(btn1.activated)
        self.assertTrue(btn2.activated)
        self.assertFalse(btn3.activated)

    def test_group_cleanup_when_reassigned(self):
        """Old groups should be cleaned up when reassigning"""
        btn1 = BasicToggleButton(group="old")
        btn2 = BasicToggleButton(group="old")

        btn1.group = "new"

        self.assertEqual(len(btn1.get_group()), 1)
        self.assertEqual(len(btn2.get_group()), 1)

    def test_initial_activated_conflict_resolution(self):
        """If multiple in group start activated, last should win"""
        btn1 = BasicToggleButton(group="g", activated=True)
        btn2 = BasicToggleButton(group="g", activated=True)

        self.assertFalse(btn1.activated)
        self.assertTrue(btn2.activated)

    # allow_no_selection tests

    def test_allow_no_selection_true_via_property(self):
        """allow_no_selection=True should allow deselection via property"""
        btn1 = BasicToggleButton(allow_no_selection=True)

        btn1.activated = True
        self.assertTrue(btn1.activated)

        btn1.activated = False
        self.assertFalse(btn1.activated)

    def test_allow_no_selection_true_via_touch(self):
        """allow_no_selection=True should allow deselection via touch"""
        btn1 = BasicToggleButton(allow_no_selection=True, activated=True)

        touch = create_mock_touch(grab_current=btn1)
        btn1.on_touch_down(touch)
        btn1.on_touch_up(touch)
        self.assertFalse(btn1.activated)

    def test_allow_no_selection_false_via_property(self):
        """allow_no_selection=False should prevent deselection via property"""
        btn1 = BasicToggleButton(
            group="test", allow_no_selection=False, activated=True
        )
        btn2 = BasicToggleButton(group="test", allow_no_selection=False)

        btn1.activated = False
        self.assertTrue(btn1.activated)

    def test_allow_no_selection_false_via_touch(self):
        """allow_no_selection=False should prevent deselection via touch"""
        btn1 = BasicToggleButton(
            group="test", allow_no_selection=False, activated=True
        )
        btn2 = BasicToggleButton(group="test", allow_no_selection=False)

        touch = create_mock_touch(grab_current=btn1)
        btn1.on_touch_down(touch)
        btn1.on_touch_up(touch)
        self.assertTrue(btn1.activated)

    # get_group() method tests

    def test_get_group_instance_method(self):
        """get_group should return correct members (instance method)"""
        btn1 = BasicToggleButton(group="g")
        btn2 = BasicToggleButton(group="g")
        btn3 = BasicToggleButton(group="x")

        g = btn1.get_group()
        self.assertIn(btn1, g)
        self.assertIn(btn2, g)
        self.assertNotIn(btn3, g)

    def test_get_group_empty(self):
        """get_group should return [] if no group"""
        self.assertEqual(BasicToggleButton().get_group(), [])

    def test_get_group_class_method_global(self):
        """Test get_group as class method with global groups"""
        btn1 = BasicToggleButton(group="test")
        btn2 = BasicToggleButton(group="test")
        btn3 = BasicToggleButton(group="other")

        # Call as class method
        widgets = ToggleButtonBehavior.get_group("test")
        self.assertEqual(len(widgets), 2)
        self.assertIn(btn1, widgets)
        self.assertIn(btn2, widgets)
        self.assertNotIn(btn3, widgets)

    def test_get_group_class_method_scoped(self):
        """Test get_group as class method with scoped groups"""
        owner = Label()
        btn1 = BasicToggleButton(group=(owner, "options"))
        btn2 = BasicToggleButton(group=(owner, "options"))
        btn3 = BasicToggleButton(group=(owner, "filters"))

        # Call as class method with scoped group
        widgets = ToggleButtonBehavior.get_group((owner, "options"))
        self.assertEqual(len(widgets), 2)
        self.assertIn(btn1, widgets)
        self.assertIn(btn2, widgets)
        self.assertNotIn(btn3, widgets)

    def test_get_group_class_method_nonexistent(self):
        """Test get_group as class method returns empty list for nonexistent
        group"""
        widgets = ToggleButtonBehavior.get_group("nonexistent")
        self.assertEqual(widgets, [])

        # Scoped nonexistent
        widgets = ToggleButtonBehavior.get_group((Label(), "fake"))
        self.assertEqual(widgets, [])

    def test_get_group_after_widget_removal(self):
        """Test get_group after removing widget from parent"""
        from kivy.uix.widget import Widget

        group_name = "test"

        parent = Widget()
        btn1 = BasicToggleButton(group=group_name)
        btn2 = BasicToggleButton(group=group_name)
        parent.add_widget(btn1)
        parent.add_widget(btn2)

        # Remove btn1
        parent.remove_widget(btn1)

        # Use class method to get remaining widgets
        remaining = ToggleButtonBehavior.get_group(group_name)
        self.assertIn(btn2, remaining)

    def test_get_group_multiple_different_groups(self):
        """Test get_group correctly separates different groups"""
        btn1 = BasicToggleButton(group="g1")
        btn2 = BasicToggleButton(group="g2")
        btn3 = BasicToggleButton(group="g1")

        g1_widgets = ToggleButtonBehavior.get_group("g1")
        g2_widgets = ToggleButtonBehavior.get_group("g2")

        self.assertEqual(len(g1_widgets), 2)
        self.assertEqual(len(g2_widgets), 1)
        self.assertIn(btn1, g1_widgets)
        self.assertIn(btn3, g1_widgets)
        self.assertIn(btn2, g2_widgets)

    def test_get_group_returns_copy(self):
        """Test that modifying returned list doesn't affect internal group"""
        btn1 = BasicToggleButton(group="test")
        btn2 = BasicToggleButton(group="test")

        widgets = btn1.get_group()
        original_len = len(widgets)

        # Try to modify returned list
        widgets.clear()

        # Verify internal group is unchanged
        widgets_again = btn1.get_group()
        self.assertEqual(len(widgets_again), original_len)

    # Memory management tests

    def test_cleanup_on_delete(self):
        """Ensure dead buttons are cleaned from group sets"""
        btn1 = BasicToggleButton(group="g")
        btn2 = BasicToggleButton(group="g")
        ref = weakref.ref(btn2)
        del btn2
        gc.collect()

        def check_cleanup(dt):
            self.assertIsNone(ref())
            self.assertEqual(len(btn1.get_group()), 1)

        Clock.schedule_once(check_cleanup, 0)
        self.advance_frames(1)

    def test_get_group_no_memory_leak(self):
        """Verify get_group() doesn't prevent garbage collection"""
        finished = []

        btn1 = BasicToggleButton(group="test")
        btn2 = BasicToggleButton(group="test")
        btn3 = BasicToggleButton(group="test")

        # Get group reference
        group_list = btn1.get_group()
        self.assertEqual(len(group_list), 3)

        # Create weak references to track garbage collection
        ref2 = weakref.ref(btn2)
        ref3 = weakref.ref(btn3)

        # Delete buttons and the group list
        del btn2, btn3
        del group_list

        def check_cleanup(dt):
            gc.collect()
            finished.append(len(btn1.get_group()))

        Clock.schedule_once(check_cleanup, 0)
        self.advance_frames(1)

        # Verify widgets were garbage collected
        self.assertIsNone(ref2())
        self.assertIsNone(ref3())

        # Verify only btn1 remains in group after GC
        self.assertEqual(finished[0], 1)
        self.assertIn(btn1, btn1.get_group())

    # Validation and edge cases

    def test_invalid_group_definitions(self):
        """Invalid group definitions should raise ValueError"""
        with self.assertRaises(ValueError):
            BasicToggleButton(group=(1,))
        with self.assertRaises(ValueError):
            BasicToggleButton(group=(1, 2, 3))
        with self.assertRaises(ValueError):
            BasicToggleButton(group=(Label(), None))
        with self.assertRaises(ValueError):
            BasicToggleButton(group=["a", "b"])
        with self.assertRaises(ValueError):
            BasicToggleButton(group=(Label(), ["unhashable"]))

    def test_enum_and_int_group_names(self):
        """Enums and integers can be used as group names"""
        from enum import Enum

        class G(Enum):
            A = 1
            B = 2

        btn1 = BasicToggleButton(group=G.A)
        btn2 = BasicToggleButton(group=G.A)
        btn3 = BasicToggleButton(group=G.B)

        btn1.activated = True
        self.assertTrue(btn1.activated)
        self.assertFalse(btn2.activated)
        self.assertFalse(btn3.activated)

        b1 = BasicToggleButton(group=10)
        b2 = BasicToggleButton(group=10)
        b3 = BasicToggleButton(group=20)
        b1.activated = True
        self.assertTrue(b1.activated)
        self.assertFalse(b2.activated)
        self.assertFalse(b3.activated)

    # Event callback tests

    def test_on_activated_callback_invoked(self):
        """Verify subclass on_activated callback is called"""
        changes = []

        class SubToggle(BasicToggleButton):
            def on_activated(self, instance, value):
                changes.append(value)

        btn = SubToggle()
        btn.activated = True
        btn.activated = False
        self.assertEqual(changes, [True, False])


if __name__ == "__main__":
    unittest.main()
