import unittest


class PaddingSpacingTestCase(unittest.TestCase):
    def test_tb_lr_stacklayout(self):
        from kivy.uix.checkbox import CheckBox

        a = CheckBox(allow_no_selection=False, group="check")
        b = CheckBox(allow_no_selection=False, group="check")

        # Test activating first checkbox
        a.active = True
        self.assertTrue(a.active)
        self.assertFalse(b.active)

        # Test activating second checkbox (deactivates first)
        b.active = True
        self.assertFalse(a.active)
        self.assertTrue(b.active)

        # Test activating first checkbox again
        a.active = True
        self.assertTrue(a.active)
        self.assertFalse(b.active)

        # Test activating second checkbox again
        b.active = True
        self.assertFalse(a.active)
        self.assertTrue(b.active)

        # Test deactivating when allow_no_selection=False
        # This should NOT work - at least one must stay active
        b.active = False
        # Since allow_no_selection=False, b should remain active
        self.assertFalse(a.active)
        self.assertTrue(b.active)

    def test_checkbox_allow_no_selection(self):
        from kivy.uix.checkbox import CheckBox

        a = CheckBox(allow_no_selection=True, group="check")
        b = CheckBox(allow_no_selection=True, group="check")

        # Test with allow_no_selection=True
        b.active = True
        self.assertTrue(b.active)
        self.assertFalse(a.active)

        # Now deactivating should work
        b.active = False
        self.assertFalse(a.active)
        self.assertFalse(b.active)

        # Activate again
        b.active = True
        self.assertTrue(b.active)
        self.assertFalse(a.active)
