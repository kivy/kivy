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


def test_fills_a_column_first_when_cols_is_None():
    # github issue #6538
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.widget import Widget
    gl = GridLayout(rows=3, size=(300, 300), pos=(0, 0))
    for i in range(4):
        gl.add_widget(Widget())
    gl.do_layout()
    children = tuple(reversed(gl.children))
    assert children[0].pos == [0, 200]
    assert children[1].pos == [0, 100]
    assert children[2].pos == [0, 0]
    assert children[3].pos == [150, 200]


if __name__ == '__main__':
    unittest.main()
