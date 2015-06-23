'''
uix.stacklayout tests
=====================
'''

import unittest

from kivy.uix.stacklayout import StackLayout
from kivy.uix.widget import Widget


class UixStackLayoutTest(unittest.TestCase):

    def test_stacklayout_no_children(self):
        sl = StackLayout()
        sl.do_layout()

    def test_stacklayout_default(self):
        # Default orientation is lr-tb.
        sl = StackLayout()
        wgts = [Widget(size_hint=(.5, .5)) for i in range(4)]
        for wgt in wgts:
            sl.add_widget(wgt)
        sl.do_layout()

        self.assertEqual(wgts[0].pos, [0, sl.height / 2.])
        self.assertEqual(wgts[1].pos, [sl.width / 2., sl.height / 2.])
        self.assertEqual(wgts[2].pos, [0, 0])
        self.assertEqual(wgts[3].pos, [sl.width / 2., 0])

    def test_stacklayout_fixed_size(self):
        sl = StackLayout()
        wgts = [Widget(size=(50, 50), size_hint=(None, None))
                for i in range(4)]
        for wgt in wgts:
            sl.add_widget(wgt)
        sl.do_layout()

        self.assertEqual(wgts[0].pos, [0, sl.height / 2.])
        self.assertEqual(wgts[1].pos, [sl.width / 2., sl.height / 2.])
        self.assertEqual(wgts[2].pos, [0, 0])
        self.assertEqual(wgts[3].pos, [sl.width / 2., 0])

    def test_stacklayout_orientation_btrl(self):
        # Default orientation is lr-tb.
        sl = StackLayout()
        wgts = [Widget(size_hint=(.5, .5)) for i in range(4)]
        for wgt in wgts:
            sl.add_widget(wgt)
        sl.orientation = 'bt-rl'
        sl.do_layout()

        self.assertEqual(wgts[0].pos, [sl.width / 2., 0])
        self.assertEqual(wgts[1].pos, [sl.width / 2., sl.height / 2.])
        self.assertEqual(wgts[2].pos, [0, 0])
        self.assertEqual(wgts[3].pos, [0, sl.height / 2.])

    def test_stacklayout_orientation_rlbt(self):
        # Default orientation is lr-tb.
        sl = StackLayout()
        wgts = [Widget(size_hint=(.5, .5)) for i in range(4)]
        for wgt in wgts:
            sl.add_widget(wgt)
        sl.orientation = 'rl-bt'
        sl.do_layout()

        self.assertEqual(wgts[0].pos, [sl.width / 2., 0])
        self.assertEqual(wgts[1].pos, [0, 0])
        self.assertEqual(wgts[2].pos, [sl.width / 2., sl.height / 2.])
        self.assertEqual(wgts[3].pos, [0, sl.height / 2.])

    def test_stacklayout_padding(self):
        sl = StackLayout()
        wgts = [Widget(size_hint=(.5, .5)) for i in range(4)]
        for wgt in wgts:
            sl.add_widget(wgt)
        sl.padding = 5.
        sl.do_layout()

        self.assertEqual(wgts[0].pos, [5., sl.height / 2.])
        self.assertEqual(wgts[1].pos, [sl.width / 2., sl.height / 2.])
        self.assertEqual(wgts[2].pos, [5., 5.])
        self.assertEqual(wgts[3].pos, [sl.width / 2., 5.])

    def test_stacklayout_spacing(self):
        sl = StackLayout()
        wgts = [Widget(size_hint=(.5, .5)) for i in range(4)]
        for wgt in wgts:
            sl.add_widget(wgt)
        sl.spacing = 10
        sl.do_layout()

        self.assertEqual(wgts[0].pos, [0, sl.height / 2.])
        self.assertEqual(wgts[1].pos, [sl.width / 2. + 5, sl.height / 2.])
        self.assertEqual(wgts[2].pos, [0, -10])
        self.assertEqual(wgts[3].pos, [sl.width / 2. + 5, -10])

    def test_stacklayout_overflow(self):
        sl = StackLayout()
        wgts = [Widget(size_hint=(.2 * i, .2 * i)) for i in range(1, 4)]
        for wgt in wgts:
            sl.add_widget(wgt)
        sl.padding = 5
        sl.spacing = 5
        sl.do_layout()

        self.assertEqual(wgts[0].pos, [5, 77])
        self.assertEqual(wgts[1].pos, [27, 59])
        # floating point error, requires almost equal
        self.assertAlmostEqual(wgts[2].pos[0], 5)
        self.assertAlmostEqual(wgts[2].pos[1], 0)

    def test_stacklayout_nospace(self):
        # happens when padding is too big
        sl = StackLayout()
        wgts = [Widget(size_hint=(1., .25)) for i in range(1, 4)]
        for wgt in wgts:
            sl.add_widget(wgt)
        sl.padding = 10
        sl.do_layout()
