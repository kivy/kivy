import pytest

KV_CODE_1 = '''
RecycleView:
    pos: 0, 0
    size: 800, 600
    viewclass: 'Widget'
    data: ({} for __ in range(4))
    RecycleGridLayout:
        default_size_hint: 1, 1
'''


class TestRecycleGridLayout:
    @pytest.mark.parametrize("cols, rows", [(2, None), (None, 2), (2, 2)])
    @pytest.mark.parametrize("index_of_small_child", range(4))
    def test_one_small_child_as_a_part_of_2x2_doesnt_affect_the_entire_layout(
            self, cols, rows, index_of_small_child):
        from kivy.clock import Clock
        from kivy.lang import Builder
        rv = Builder.load_string(KV_CODE_1)
        gl = rv.children[0]
        gl.cols = cols
        gl.rows = rows
        rv.data[index_of_small_child] = {
            'size_hint': (None, None), 'size': (100, 100), }
        Clock.tick()
        Clock.tick()
        assert {tuple(c.pos) for c in gl.children} == \
            {(0, 0), (400, 0), (0, 300), (400, 300)}
        assert sorted(c.size for c in gl.children) == \
            [[100, 100], [400, 300], [400, 300], [400, 300]]
