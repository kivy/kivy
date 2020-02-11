'''
uix.layout tests
================
Layout class is Abstract Base Class.
'''

import unittest
import pytest

from kivy.uix.layout import Layout


class UixLayoutTest(unittest.TestCase):

    def test_instantiation(self):
        with self.assertRaises(Exception):
            layout = Layout()


@pytest.mark.parametrize(
    "sh_min_vals, sh_max_vals, hint, expected_ratio", [
        ((50, None, None), (None, None, None), (1, 1, 1), (2, 1, 1)),
        ((None, 50, None), (None, None, None), (1, 1, 1), (1, 2, 1)),
        ((None, None, 50), (None, None, None), (1, 1, 1), (1, 1, 2)),
    ])
def test_layout_hint_with_bounds(sh_min_vals, sh_max_vals, hint,
                                 expected_ratio):
    from math import isclose
    from kivy.uix.layout import Layout
    copied_hint = list(hint)
    Layout.layout_hint_with_bounds(
        None, sum(hint), 100, sum(v for v in sh_min_vals if v is not None),
        sh_min_vals, sh_max_vals, copied_hint,
    )
    actual_ratio = copied_hint
    sum_actual = sum(actual_ratio)
    sum_expected = sum(expected_ratio)
    for actual, expected in zip(actual_ratio, expected_ratio):
        assert isclose(
            actual / sum_actual,
            expected / sum_expected,
            abs_tol=0.01,
        )
