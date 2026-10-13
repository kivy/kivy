import unittest


class PaddingSpacingTestCase(unittest.TestCase):
    def test_tb_lr_stacklayout(self):
        from kivy.uix.checkbox import CheckBox

        a = CheckBox(allow_no_selection=False, group="check")
        b = CheckBox(allow_no_selection=False, group="check")

        # Test activating first checkbox
        a.activated = True
        self.assertTrue(a.activated)
        self.assertFalse(b.activated)

        # Test activating second checkbox (deactivates first)
        b.activated = True
        self.assertFalse(a.activated)
        self.assertTrue(b.activated)

        # Test activating first checkbox again
        a.activated = True
        self.assertTrue(a.activated)
        self.assertFalse(b.activated)

        # Test activating second checkbox again
        b.activated = True
        self.assertFalse(a.activated)
        self.assertTrue(b.activated)

        # Test deactivating when allow_no_selection=False
        # This should NOT work - at least one must stay activated
        b.activated = False
        # Since allow_no_selection=False, b should remain activated
        self.assertFalse(a.activated)
        self.assertTrue(b.activated)

    def test_checkbox_allow_no_selection(self):
        from kivy.uix.checkbox import CheckBox

        a = CheckBox(allow_no_selection=True, group="check")
        b = CheckBox(allow_no_selection=True, group="check")

        # Test with allow_no_selection=True
        b.activated = True
        self.assertTrue(b.activated)
        self.assertFalse(a.activated)

        # Now deactivating should work
        b.activated = False
        self.assertFalse(a.activated)
        self.assertFalse(b.activated)

        # Activate again
        b.activated = True
        self.assertTrue(b.activated)
        self.assertFalse(a.activated)
