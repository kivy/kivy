import unittest


class PaddingSpacingTestCase(unittest.TestCase):
    def test_tb_lr_stacklayout(self):
        from kivy.uix.checkbox import CheckBox
        a = CheckBox(allow_no_selection=False, group='check')
        b = CheckBox(allow_no_selection=False, group='check')

        a.active = True
        self.assertTrue(a.active)
        self.assertEqual(a.state, 'down')

        self.assertFalse(b.active)
        self.assertEqual(b.state, 'normal')

        b.active = True
        self.assertTrue(b.active)
        self.assertEqual(b.state, 'down')

        self.assertFalse(a.active)
        self.assertEqual(a.state, 'normal')

        a.state = 'down'
        self.assertTrue(a.active)
        self.assertEqual(a.state, 'down')

        self.assertFalse(b.active)
        self.assertEqual(b.state, 'normal')

        b.state = 'down'
        self.assertTrue(b.active)
        self.assertEqual(b.state, 'down')

        self.assertFalse(a.active)
        self.assertEqual(a.state, 'normal')

        b.state = 'normal'
        self.assertFalse(a.active)
        self.assertEqual(a.state, 'normal')
        self.assertFalse(b.active)
        self.assertEqual(b.state, 'normal')

        b.state = 'down'
        self.assertTrue(b.active)
        self.assertEqual(b.state, 'down')

        self.assertFalse(a.active)
        self.assertEqual(a.state, 'normal')

        b.active = False
        self.assertFalse(a.active)
        self.assertEqual(a.state, 'normal')
        self.assertFalse(b.active)
        self.assertEqual(b.state, 'normal')
