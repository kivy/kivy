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
        ((20, None, None), (None, None, None), (1, 1, 1), (1, 1, 1)),
        ((None, 20, None), (None, None, None), (1, 1, 1), (1, 1, 1)),
        ((None, None, 20), (None, None, None), (1, 1, 1), (1, 1, 1)),
        ((50, 50, None), (None, None, None), (1, 1, 1), (1, 1, 0)),
        ((50, None, 50), (None, None, None), (1, 1, 1), (1, 0, 1)),
        ((None, 50, 50), (None, None, None), (1, 1, 1), (0, 1, 1)),
        ((20, 20, None), (None, None, None), (1, 1, 1), (1, 1, 1)),
        ((20, None, 20), (None, None, None), (1, 1, 1), (1, 1, 1)),
        ((None, 20, 20), (None, None, None), (1, 1, 1), (1, 1, 1)),
        ((None, None, None), (50, None, None), (1, 1, 1), (1, 1, 1)),
        ((None, None, None), (None, 50, None), (1, 1, 1), (1, 1, 1)),
        ((None, None, None), (None, None, 50), (1, 1, 1), (1, 1, 1)),
        ((None, None, None), (20, None, None), (1, 1, 1), (1, 2, 2)),
        ((None, None, None), (None, 20, None), (1, 1, 1), (2, 1, 2)),
        ((None, None, None), (None, None, 20), (1, 1, 1), (2, 2, 1)),
        ((None, None, None), (50, 50, None), (1, 1, 1), (1, 1, 1)),
        ((None, None, None), (50, None, 50), (1, 1, 1), (1, 1, 1)),
        ((None, None, None), (None, 50, 50), (1, 1, 1), (1, 1, 1)),
        ((None, None, None), (20, 20, None), (1, 1, 1), (1, 1, 3)),
        ((None, None, None), (20, None, 20), (1, 1, 1), (1, 3, 1)),
        ((None, None, None), (None, 20, 20), (1, 1, 1), (3, 1, 1)),
        # a case where some space remaining.
        ((None, None, None), (20, 20, 20), (1, 1, 1), (1, 1, 1)),
        # some complex cases
        ((30, None, None), (None, None, 40), (1, 2, 3), (3, 3, 4)),
        ((20, None, None), (None, None, 40), (1, 2, 3), (1, 2, 2)),
        ((10, None, None), (None, None, 40), (1, 2, 3), (1, 2, 2)),
        # There are cases that are hard to predict the ratio. For example:
        # ((30, None, None), (None, None, 60), (1, 2, 3), (?, ?, ?)),
        # TODO: Someone who good at math, please add more tests.
    ])
def test_layout_hint_with_bounds(
        sh_min_vals, sh_max_vals, hint, expected_ratio):
    # test the parameters itself bacause `layout_hint_with_bounds()` doesn't
    # check it.
    assert len(sh_min_vals) == len(sh_max_vals)
    assert len(hint) == len(expected_ratio)
    assert len(hint) == len(sh_min_vals)

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
