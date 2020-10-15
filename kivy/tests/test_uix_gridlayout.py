'''
uix.gridlayout tests
========================
'''

import unittest
import pytest
from kivy.tests.common import GraphicUnitTest

from kivy.uix.gridlayout import GridLayout


class GridLayoutTest(unittest.TestCase):

    def test_gridlayout_get_max_widgets_cols_rows_None(self):
        gl = GridLayout()
        expected = None
        value = gl.get_max_widgets()
        self.assertEqual(expected, value)

    def test_gridlayout_get_max_widgets_rows_None(self):
        gl = GridLayout()
        gl.cols = 1
        expected = None
        value = gl.get_max_widgets()
        self.assertEqual(expected, value)

    def test_gridlayout_get_max_widgets_cols_None(self):
        gl = GridLayout()
        gl.rows = 1
        expected = None
        value = gl.get_max_widgets()
        self.assertEqual(expected, value)

    def test_gridlayout_get_max_widgets_with_rows_cols(self):
        gl = GridLayout()
        gl.rows = 5
        gl.cols = 3
        expected = 15
        value = gl.get_max_widgets()
        self.assertEqual(expected, value)


class UixGridLayoutTest(GraphicUnitTest):

    def test_rows_cols_sizes(self):
        # ref github issue #5278 _init_rows_cols_sizes fix
        # this combination could trigger an error
        gl = GridLayout()
        gl.cols = 1
        gl.cols_minimum = {i: 10 for i in range(10)}
        gl.add_widget(GridLayout())
        self.render(gl)


@pytest.mark.parametrize(
    "n_cols, n_rows, orientation, expectation", [
        (2, 3, 'lr-tb', [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)]),
        (2, 3, 'lr-bt', [(0, 2), (1, 2), (0, 1), (1, 1), (0, 0), (1, 0)]),
        (2, 3, 'rl-tb', [(1, 0), (0, 0), (1, 1), (0, 1), (1, 2), (0, 2)]),
        (2, 3, 'rl-bt', [(1, 2), (0, 2), (1, 1), (0, 1), (1, 0), (0, 0)]),
        (2, 3, 'tb-lr', [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]),
        (2, 3, 'tb-rl', [(1, 0), (1, 1), (1, 2), (0, 0), (0, 1), (0, 2)]),
        (2, 3, 'bt-lr', [(0, 2), (0, 1), (0, 0), (1, 2), (1, 1), (1, 0)]),
        (2, 3, 'bt-rl', [(1, 2), (1, 1), (1, 0), (0, 2), (0, 1), (0, 0)]),
    ]
)
def test_create_idx_iter(
        n_cols, n_rows, orientation, expectation):
    from kivy.uix.gridlayout import GridLayout
    gl = GridLayout(orientation=orientation)
    index_iter = gl._create_idx_iter(n_cols, n_rows)
    assert expectation == list(index_iter)


@pytest.mark.parametrize("orientation", [
    'lr-tb', 'lr-bt', 'rl-tb', 'rl-bt',
    'tb-lr', 'tb-rl', 'bt-lr', 'bt-rl',
])
def test_create_idx_iter2(orientation):
    from kivy.uix.gridlayout import GridLayout
    gl = GridLayout(orientation=orientation)
    index_iter = gl._create_idx_iter(1, 1)
    assert [(0, 0)] == list(index_iter)


@pytest.mark.parametrize(
    "n_cols, n_rows, orientation, n_children, expectation", [
        (3, None, 'lr-tb', 4, [(0, 15), (10, 15), (20, 15), (0, 0)]),
        (3, None, 'lr-bt', 4, [(0, 0), (10, 0), (20, 0), (0, 15)]),
        (3, None, 'rl-tb', 4, [(20, 15), (10, 15), (0, 15), (20, 0)]),
        (3, None, 'rl-bt', 4, [(20, 0), (10, 0), (0, 0), (20, 15)]),
        (None, 3, 'tb-lr', 4, [(0, 20), (0, 10), (0, 0), (15, 20)]),
        (None, 3, 'tb-rl', 4, [(15, 20), (15, 10), (15, 0), (0, 20)]),
        (None, 3, 'bt-lr', 4, [(0, 0), (0, 10), (0, 20), (15, 0)]),
        (None, 3, 'bt-rl', 4, [(15, 0), (15, 10), (15, 20), (0, 0)]),
    ]
)
def test_children_pos(n_cols, n_rows, orientation, n_children, expectation):
    from kivy.uix.widget import Widget
    from kivy.uix.gridlayout import GridLayout
    gl = GridLayout(
        cols=n_cols, rows=n_rows, orientation=orientation,
        pos=(0, 0), size=(30, 30))
    for __ in range(n_children):
        gl.add_widget(Widget())
    gl.do_layout()
    actual_layout = [tuple(c.pos) for c in reversed(gl.children)]
    assert actual_layout == expectation


if __name__ == '__main__':
    unittest.main()
