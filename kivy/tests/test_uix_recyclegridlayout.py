import pytest


class Test_layout:
    def compute_layout(self, *, n_cols, n_rows, orientation, n_data):
        '''Returns {view-index: pos, view-index: pos, ...}'''
        from textwrap import dedent
        from kivy.clock import Clock
        from kivy.lang import Builder

        # Use Kv because RecycleView cannot be constructed from python
        rv = Builder.load_string(dedent(f'''
            RecycleView:
                viewclass: 'Widget'
                size: 300, 300
                data: ({{}} for __ in range({n_data}))
                RecycleGridLayout:
                    id: layout
                    cols: {n_cols}
                    rows: {n_rows}
                    orientation: '{orientation}'
                    default_size_hint: None, None
                    default_size: 100, 100
                    size_hint: None, None
                    size: self.minimum_size
            '''))
        Clock.tick()
        layout = rv.ids.layout
        return {
            layout.get_view_index_at(c.center): tuple(c.pos)
            for c in layout.children
        }

    # |---|---|---|
    # | 0 | 1 | 2 |
    # |---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 1), (3, 1)])
    @pytest.mark.parametrize("orientation", "lr-tb lr-bt tb-lr bt-lr".split())
    def test_3x1_lr(self, orientation, n_cols, n_rows):
        assert {0: (0, 0), 1: (100, 0), 2: (200, 0)} == self.compute_layout(
            n_data=3, orientation=orientation, n_cols=n_cols, n_rows=n_rows)

    # |---|---|---|
    # | 2 | 1 | 0 |
    # |---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 1), (3, 1)])
    @pytest.mark.parametrize("orientation", "rl-tb rl-bt tb-rl bt-rl".split())
    def test_3x1_rl(self, orientation, n_cols, n_rows):
        assert {0: (200, 0), 1: (100, 0), 2: (0, 0)} == self.compute_layout(
            n_data=3, orientation=orientation, n_cols=n_cols, n_rows=n_rows)

    # |---|
    # | 0 |
    # |---|
    # | 1 |
    # |---|
    # | 2 |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(1, None), (None, 3), (1, 3)])
    @pytest.mark.parametrize("orientation", "tb-lr tb-rl lr-tb rl-tb".split())
    def test_1x3_tb(self, orientation, n_cols, n_rows):
        assert {0: (0, 200), 1: (0, 100), 2: (0, 0)} == self.compute_layout(
            n_data=3, orientation=orientation, n_cols=n_cols, n_rows=n_rows)

    # |---|
    # | 2 |
    # |---|
    # | 1 |
    # |---|
    # | 0 |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(1, None), (None, 3), (1, 3)])
    @pytest.mark.parametrize("orientation", "bt-lr bt-rl lr-bt rl-bt".split())
    def test_1x3_bt(self, orientation, n_cols, n_rows):
        assert {0: (0, 0), 1: (0, 100), 2: (0, 200)} == self.compute_layout(
            n_data=3, orientation=orientation, n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 0 | 1 |
    # |---|---|
    # | 2 | 3 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_lr_tb(self, n_cols, n_rows):
        assert {0: (0, 100), 1: (100, 100), 2: (0, 0), 3: (100, 0)} == \
            self.compute_layout(
                n_data=4, orientation='lr-tb', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 2 | 3 |
    # |---|---|
    # | 0 | 1 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_lr_bt(self, n_cols, n_rows):
        assert {0: (0, 0), 1: (100, 0), 2: (0, 100), 3: (100, 100)} == \
            self.compute_layout(
                n_data=4, orientation='lr-bt', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 1 | 0 |
    # |---|---|
    # | 3 | 2 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_rl_tb(self, n_cols, n_rows):
        assert {0: (100, 100), 1: (0, 100), 2: (100, 0), 3: (0, 0)} == \
            self.compute_layout(
                n_data=4, orientation='rl-tb', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 3 | 2 |
    # |---|---|
    # | 1 | 0 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_rl_bt(self, n_cols, n_rows):
        assert {0: (100, 0), 1: (0, 0), 2: (100, 100), 3: (0, 100)} == \
            self.compute_layout(
                n_data=4, orientation='rl-bt', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 0 | 2 |
    # |---|---|
    # | 1 | 3 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_tb_lr(self, n_cols, n_rows):
        assert {0: (0, 100), 1: (0, 0), 2: (100, 100), 3: (100, 0)} == \
            self.compute_layout(
                n_data=4, orientation='tb-lr', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 2 | 0 |
    # |---|---|
    # | 3 | 1 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_tb_rl(self, n_cols, n_rows):
        assert {0: (100, 100), 1: (100, 0), 2: (0, 100), 3: (0, 0)} == \
            self.compute_layout(
                n_data=4, orientation='tb-rl', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 1 | 3 |
    # |---|---|
    # | 0 | 2 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_bt_lr(self, n_cols, n_rows):
        assert {0: (0, 0), 1: (0, 100), 2: (100, 0), 3: (100, 100)} == \
            self.compute_layout(
                n_data=4, orientation='bt-lr', n_cols=n_cols, n_rows=n_rows)

    # |---|---|
    # | 3 | 1 |
    # |---|---|
    # | 2 | 0 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_bt_rl(self, n_cols, n_rows):
        assert {0: (100, 0), 1: (100, 100), 2: (0, 0), 3: (0, 100)} == \
            self.compute_layout(
                n_data=4, orientation='bt-rl', n_cols=n_cols, n_rows=n_rows)
