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


class TestLayout_fixed_sized_children:
    def compute_layout(self, *, n_cols, n_rows, ori, n_children):
        from kivy.uix.widget import Widget
        from kivy.uix.gridlayout import GridLayout
        gl = GridLayout(cols=n_cols, rows=n_rows, orientation=ori, pos=(0, 0))
        gl.bind(minimum_size=gl.setter("size"))
        for __ in range(n_children):
            # set 'pos' to some random value to make this test more reliable
            gl.add_widget(Widget(
                size_hint=(None, None), size=(100, 100), pos=(8, 8)))
        gl.do_layout()
        return [tuple(c.pos) for c in reversed(gl.children)]

    # |---|
    # | 0 |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(1, None), (None, 1), (1, 1)])
    def test_1x1(self, n_cols, n_rows):
        from kivy.uix.gridlayout import GridLayout
        for ori in GridLayout.orientation.options:
            assert [(0, 0), ] == self.compute_layout(
                n_children=1, ori=ori, n_cols=n_cols, n_rows=n_rows)

    # |---|---|---|
    # | 0 | 1 | 2 |
    # |---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 1), (3, 1)])
    @pytest.mark.parametrize("ori", "lr-tb lr-bt tb-lr bt-lr".split())
    def test_3x1_lr(self, ori, n_cols, n_rows):
        assert [(0, 0), (100, 0), (200, 0)] == self.compute_layout(
            n_children=3, ori=ori, n_cols=n_cols, n_rows=n_rows)

    # |---|---|---|
    # | 2 | 1 | 0 |
    # |---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 1), (3, 1)])
    @pytest.mark.parametrize("ori", "rl-tb rl-bt tb-rl bt-rl".split())
    def test_3x1_rl(self, ori, n_cols, n_rows):
        assert [(200, 0), (100, 0), (0, 0)] == self.compute_layout(
            n_children=3, ori=ori, n_cols=n_cols, n_rows=n_rows)

    # |---|
    # | 0 |
    # |---|
    # | 1 |
    # |---|
    # | 2 |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(1, None), (None, 3), (1, 3)])
    @pytest.mark.parametrize("ori", "tb-lr tb-rl lr-tb rl-tb".split())
    def test_1x3_tb(self, ori, n_cols, n_rows):
        assert [(0, 200), (0, 100), (0, 0)] == self.compute_layout(
            n_children=3, ori=ori, n_cols=n_cols, n_rows=n_rows)

    # |---|
    # | 2 |
    # |---|
    # | 1 |
    # |---|
    # | 0 |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(1, None), (None, 3), (1, 3)])
    @pytest.mark.parametrize("ori", "bt-lr bt-rl lr-bt rl-bt".split())
    def test_1x3_bt(self, ori, n_cols, n_rows):
        assert [(0, 0), (0, 100), (0, 200)] == self.compute_layout(
            n_children=3, ori=ori, n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 0 | 1 |
    # |---|---|
    # | 2 | 3 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_lr_tb(self, n_cols, n_rows):
        assert [(0, 100), (100, 100), (0, 0), (100, 0)] == \
            self.compute_layout(
                n_children=4, ori='lr-tb', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 2 | 3 |
    # |---|---|
    # | 0 | 1 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_lr_bt(self, n_cols, n_rows):
        assert [(0, 0), (100, 0), (0, 100), (100, 100)] == \
            self.compute_layout(
                n_children=4, ori='lr-bt', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 1 | 0 |
    # |---|---|
    # | 3 | 2 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_rl_tb(self, n_cols, n_rows):
        assert [(100, 100), (0, 100), (100, 0), (0, 0)] == \
            self.compute_layout(
                n_children=4, ori='rl-tb', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 3 | 2 |
    # |---|---|
    # | 1 | 0 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_rl_bt(self, n_cols, n_rows):
        assert [(100, 0), (0, 0), (100, 100), (0, 100)] == \
            self.compute_layout(
                n_children=4, ori='rl-bt', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 0 | 2 |
    # |---|---|
    # | 1 | 3 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_tb_lr(self, n_cols, n_rows):
        assert [(0, 100), (0, 0), (100, 100), (100, 0)] == \
            self.compute_layout(
                n_children=4, ori='tb-lr', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 2 | 0 |
    # |---|---|
    # | 3 | 1 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_tb_rl(self, n_cols, n_rows):
        assert [(100, 100), (100, 0), (0, 100), (0, 0)] == \
            self.compute_layout(
                n_children=4, ori='tb-rl', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 1 | 3 |
    # |---|---|
    # | 0 | 2 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_bt_lr(self, n_cols, n_rows):
        assert [(0, 0), (0, 100), (100, 0), (100, 100)] == \
            self.compute_layout(
                n_children=4, ori='bt-lr', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 3 | 1 |
    # |---|---|
    # | 2 | 0 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_bt_rl(self, n_cols, n_rows):
        assert [(100, 0), (100, 100), (0, 0), (0, 100)] == \
            self.compute_layout(
                n_children=4, ori='bt-rl', n_cols=n_cols, n_rows=n_rows)


if __name__ == '__main__':
    unittest.main()
