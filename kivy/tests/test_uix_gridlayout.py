'''
uix.gridlayout tests
========================
'''
import pytest
import unittest
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


@pytest.mark.parametrize("cols, rows", [(2, None), (None, 2), (2, 2)])
@pytest.mark.parametrize("index_of_small_child", range(4))
def test_one_small_child_as_a_part_of_2x2_does_not_affect_the_entire_layout(
        cols, rows, index_of_small_child):
    from kivy.uix.widget import Widget
    from kivy.uix.gridlayout import GridLayout
    gl = GridLayout(size=(800, 600), pos=(0, 0), rows=rows, cols=cols)
    for i in range(4):
        gl.add_widget(Widget())
    c = gl.children[index_of_small_child]
    c.size_hint = (None, None)
    c.size = (100, 100)
    gl.do_layout()
    assert {tuple(c.pos) for c in gl.children} == \
        {(0, 0), (400, 0), (0, 300), (400, 300)}
    assert sorted(c.size for c in gl.children) == \
        [[100, 100], [400, 300], [400, 300], [400, 300]]


if __name__ == '__main__':
    unittest.main()
