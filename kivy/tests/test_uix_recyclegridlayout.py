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
    @pytest.mark.parametrize("orientation, n_cols, n_rows", [
        ('lr-tb', 3, None),
        ('lr-bt', 3, None),
        ('lr-tb', None, 1),
        ('lr-bt', None, 1),
        ('lr-tb', 3, 1),
        ('lr-bt', 3, 1),
        ('tb-lr', 3, None),
        ('bt-lr', 3, None),
        ('tb-lr', None, 1),
        ('bt-lr', None, 1),
        ('tb-lr', 3, 1),
        ('bt-lr', 3, 1),
    ])
    def test_3x1_lr(self, orientation, n_cols, n_rows):
        assert {0: (0, 0), 1: (100, 0), 2: (200, 0)} == self.compute_layout(
            n_data=3, orientation=orientation, n_cols=n_cols, n_rows=n_rows)

    # |---|---|---|
    # | 2 | 1 | 0 |
    # |---|---|---|
    @pytest.mark.parametrize("orientation, n_cols, n_rows", [
        ('rl-tb', 3, None),
        ('rl-bt', 3, None),
        ('rl-tb', None, 1),
        ('rl-bt', None, 1),
        ('rl-tb', 3, 1),
        ('rl-bt', 3, 1),
        ('tb-rl', 3, None),
        ('bt-rl', 3, None),
        ('tb-rl', None, 1),
        ('bt-rl', None, 1),
        ('tb-rl', 3, 1),
        ('bt-rl', 3, 1),
    ])
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
    @pytest.mark.parametrize("orientation, n_cols, n_rows", [
        ('tb-lr', 1, None),
        ('tb-rl', 1, None),
        ('tb-lr', None, 3),
        ('tb-rl', None, 3),
        ('tb-lr', 1, 3),
        ('tb-rl', 1, 3),
        ('lr-tb', 1, None),
        ('rl-tb', 1, None),
        ('lr-tb', None, 3),
        ('rl-tb', None, 3),
        ('lr-tb', 1, 3),
        ('rl-tb', 1, 3),
    ])
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
    @pytest.mark.parametrize("orientation, n_cols, n_rows", [
        ('bt-lr', 1, None),
        ('bt-rl', 1, None),
        ('bt-lr', None, 3),
        ('bt-rl', None, 3),
        ('bt-lr', 1, 3),
        ('bt-rl', 1, 3),
        ('lr-bt', 1, None),
        ('rl-bt', 1, None),
        ('lr-bt', None, 3),
        ('rl-bt', None, 3),
        ('lr-bt', 1, 3),
        ('rl-bt', 1, 3),
    ])
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
