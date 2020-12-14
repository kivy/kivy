import pytest


class TestLayout_all_the_data_is_visible:
    def compute_layout(self, *, n_cols, n_rows, orientation, n_data, clock):
        '''Returns {view-index: pos, view-index: pos, ...}'''
        from textwrap import dedent
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
        clock.tick()
        layout = rv.ids.layout
        return {
            layout.get_view_index_at(c.center): tuple(c.pos)
            for c in layout.children
        }

    # |---|
    # | 0 |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(1, None), (None, 1), (1, 1)])
    def test_1x1(self, kivy_clock, n_cols, n_rows):
        from kivy.uix.recyclegridlayout import RecycleGridLayout
        for orientation in RecycleGridLayout.orientation.options:
            assert {0: (0, 0), } == self.compute_layout(
                n_data=1, orientation=orientation, n_cols=n_cols,
                n_rows=n_rows, clock=kivy_clock)

    # |---|---|---|
    # | 0 | 1 | 2 |
    # |---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 1), (3, 1)])
    @pytest.mark.parametrize("orientation", "lr-tb lr-bt tb-lr bt-lr".split())
    def test_3x1_lr(self, kivy_clock, orientation, n_cols, n_rows):
        assert {0: (0, 0), 1: (100, 0), 2: (200, 0)} == self.compute_layout(
            n_data=3, orientation=orientation, n_cols=n_cols, n_rows=n_rows,
            clock=kivy_clock)

    # |---|---|---|
    # | 2 | 1 | 0 |
    # |---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 1), (3, 1)])
    @pytest.mark.parametrize("orientation", "rl-tb rl-bt tb-rl bt-rl".split())
    def test_3x1_rl(self, kivy_clock, orientation, n_cols, n_rows):
        assert {0: (200, 0), 1: (100, 0), 2: (0, 0)} == self.compute_layout(
            n_data=3, orientation=orientation, n_cols=n_cols, n_rows=n_rows,
            clock=kivy_clock)

    # |---|
    # | 0 |
    # |---|
    # | 1 |
    # |---|
    # | 2 |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(1, None), (None, 3), (1, 3)])
    @pytest.mark.parametrize("orientation", "tb-lr tb-rl lr-tb rl-tb".split())
    def test_1x3_tb(self, kivy_clock, orientation, n_cols, n_rows):
        assert {0: (0, 200), 1: (0, 100), 2: (0, 0)} == self.compute_layout(
            n_data=3, orientation=orientation, n_cols=n_cols, n_rows=n_rows,
            clock=kivy_clock)

    # |---|
    # | 2 |
    # |---|
    # | 1 |
    # |---|
    # | 0 |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(1, None), (None, 3), (1, 3)])
    @pytest.mark.parametrize("orientation", "bt-lr bt-rl lr-bt rl-bt".split())
    def test_1x3_bt(self, kivy_clock, orientation, n_cols, n_rows):
        assert {0: (0, 0), 1: (0, 100), 2: (0, 200)} == self.compute_layout(
            n_data=3, orientation=orientation, n_cols=n_cols, n_rows=n_rows,
            clock=kivy_clock)

    # |---|---|
    # | 0 | 1 |
    # |---|---|
    # | 2 | 3 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_lr_tb(self, kivy_clock, n_cols, n_rows):
        assert {0: (0, 100), 1: (100, 100), 2: (0, 0), 3: (100, 0)} == \
            self.compute_layout(
                n_data=4, orientation='lr-tb', n_cols=n_cols, n_rows=n_rows,
                clock=kivy_clock)

    # |---|---|
    # | 2 | 3 |
    # |---|---|
    # | 0 | 1 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_lr_bt(self, kivy_clock, n_cols, n_rows):
        assert {0: (0, 0), 1: (100, 0), 2: (0, 100), 3: (100, 100)} == \
            self.compute_layout(
                n_data=4, orientation='lr-bt', n_cols=n_cols, n_rows=n_rows,
                clock=kivy_clock)

    # |---|---|
    # | 1 | 0 |
    # |---|---|
    # | 3 | 2 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_rl_tb(self, kivy_clock, n_cols, n_rows):
        assert {0: (100, 100), 1: (0, 100), 2: (100, 0), 3: (0, 0)} == \
            self.compute_layout(
                n_data=4, orientation='rl-tb', n_cols=n_cols, n_rows=n_rows,
                clock=kivy_clock)

    # |---|---|
    # | 3 | 2 |
    # |---|---|
    # | 1 | 0 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_rl_bt(self, kivy_clock, n_cols, n_rows):
        assert {0: (100, 0), 1: (0, 0), 2: (100, 100), 3: (0, 100)} == \
            self.compute_layout(
                n_data=4, orientation='rl-bt', n_cols=n_cols, n_rows=n_rows,
                clock=kivy_clock)

    # |---|---|
    # | 0 | 2 |
    # |---|---|
    # | 1 | 3 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_tb_lr(self, kivy_clock, n_cols, n_rows):
        assert {0: (0, 100), 1: (0, 0), 2: (100, 100), 3: (100, 0)} == \
            self.compute_layout(
                n_data=4, orientation='tb-lr', n_cols=n_cols, n_rows=n_rows,
                clock=kivy_clock)

    # |---|---|
    # | 2 | 0 |
    # |---|---|
    # | 3 | 1 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_tb_rl(self, kivy_clock, n_cols, n_rows):
        assert {0: (100, 100), 1: (100, 0), 2: (0, 100), 3: (0, 0)} == \
            self.compute_layout(
                n_data=4, orientation='tb-rl', n_cols=n_cols, n_rows=n_rows,
                clock=kivy_clock)

    # |---|---|
    # | 1 | 3 |
    # |---|---|
    # | 0 | 2 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_bt_lr(self, kivy_clock, n_cols, n_rows):
        assert {0: (0, 0), 1: (0, 100), 2: (100, 0), 3: (100, 100)} == \
            self.compute_layout(
                n_data=4, orientation='bt-lr', n_cols=n_cols, n_rows=n_rows,
                clock=kivy_clock)

    # |---|---|
    # | 3 | 1 |
    # |---|---|
    # | 2 | 0 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_bt_rl(self, kivy_clock, n_cols, n_rows):
        assert {0: (100, 0), 1: (100, 100), 2: (0, 0), 3: (0, 100)} == \
            self.compute_layout(
                n_data=4, orientation='bt-rl', n_cols=n_cols, n_rows=n_rows,
                clock=kivy_clock)


class TestLayout_only_a_part_of_the_data_is_visible:
    def compute_layout(self, *, n_cols, n_rows, orientation, n_data,
                       scroll_to, clock):
        '''Returns {view-index: pos, view-index: pos, ...}'''
        from textwrap import dedent
        from kivy.lang import Builder

        # Use Kv because RecycleView cannot be constructed from python
        rv = Builder.load_string(dedent(f'''
            RecycleView:
                viewclass: 'Widget'
                size: 100, 100
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
        clock.tick()
        layout = rv.ids.layout
        x, y = scroll_to
        try:
            rv.scroll_x = x / (layout.width - rv.width)
        except ZeroDivisionError:
            pass
        try:
            rv.scroll_y = y / (layout.height - rv.height)
        except ZeroDivisionError:
            pass
        clock.tick()
        return {
            layout.get_view_index_at(c.center): tuple(c.pos)
            for c in layout.children
        }

    # |---|---|---|---|
    # |   | 1 | 2 |   |
    # |---|---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(4, None), (None, 1), (4, 1)])
    @pytest.mark.parametrize("orientation", "lr-tb lr-bt tb-lr bt-lr".split())
    def test_4x1_lr(self, kivy_clock, orientation, n_cols, n_rows):
        assert {1: (100, 0), 2: (200, 0)} == self.compute_layout(
            n_data=4, orientation=orientation, n_cols=n_cols, n_rows=n_rows,
            scroll_to=(150, 0), clock=kivy_clock)

    # |---|---|---|---|
    # |   | 2 | 1 |   |
    # |---|---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(4, None), (None, 1), (4, 1)])
    @pytest.mark.parametrize("orientation", "rl-tb rl-bt tb-rl bt-rl".split())
    def test_4x1_rl(self, kivy_clock, orientation, n_cols, n_rows):
        assert {1: (200, 0), 2: (100, 0)} == self.compute_layout(
            n_data=4, orientation=orientation, n_cols=n_cols, n_rows=n_rows,
            scroll_to=(150, 0), clock=kivy_clock)

    # |---|
    # |   |
    # |---|
    # | 1 |
    # |---|
    # | 2 |
    # |---|
    # |   |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(1, None), (None, 4), (1, 4)])
    @pytest.mark.parametrize("orientation", "tb-lr tb-rl lr-tb rl-tb".split())
    def test_1x4_tb(self, kivy_clock, orientation, n_cols, n_rows):
        assert {1: (0, 200), 2: (0, 100)} == self.compute_layout(
            n_data=4, orientation=orientation, n_cols=n_cols, n_rows=n_rows,
            scroll_to=(0, 150), clock=kivy_clock)

    # |---|
    # |   |
    # |---|
    # | 2 |
    # |---|
    # | 1 |
    # |---|
    # |   |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(1, None), (None, 4), (1, 4)])
    @pytest.mark.parametrize("orientation", "bt-lr bt-rl lr-bt rl-bt".split())
    def test_1x4_bt(self, kivy_clock, orientation, n_cols, n_rows):
        assert {1: (0, 100), 2: (0, 200)} == self.compute_layout(
            n_data=4, orientation=orientation, n_cols=n_cols, n_rows=n_rows,
            scroll_to=(0, 150), clock=kivy_clock)

    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    # |   | 5 | 6 |   |
    # |---|---|---|---|
    # |   | 9 | 10|   |
    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(4, None), (None, 4), (4, 4)])
    def test_4x4_lr_tb(self, kivy_clock, n_cols, n_rows):
        assert {5: (100, 200), 6: (200, 200), 9: (100, 100), 10: (200, 100)} \
            == self.compute_layout(
                n_data=16, orientation='lr-tb', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 150), clock=kivy_clock)

    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    # |   | 9 | 10|   |
    # |---|---|---|---|
    # |   | 5 | 6 |   |
    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(4, None), (None, 4), (4, 4)])
    def test_4x4_lr_bt(self, kivy_clock, n_cols, n_rows):
        assert {5: (100, 100), 6: (200, 100), 9: (100, 200), 10: (200, 200)} \
            == self.compute_layout(
                n_data=16, orientation='lr-bt', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 150), clock=kivy_clock)

    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    # |   | 6 | 5 |   |
    # |---|---|---|---|
    # |   | 10| 9 |   |
    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(4, None), (None, 4), (4, 4)])
    def test_4x4_rl_tb(self, kivy_clock, n_cols, n_rows):
        assert {5: (200, 200), 6: (100, 200), 9: (200, 100), 10: (100, 100)} \
            == self.compute_layout(
                n_data=16, orientation='rl-tb', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 150), clock=kivy_clock)

    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    # |   | 10| 9 |   |
    # |---|---|---|---|
    # |   | 6 | 5 |   |
    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(4, None), (None, 4), (4, 4)])
    def test_4x4_rl_bt(self, kivy_clock, n_cols, n_rows):
        assert {5: (200, 100), 6: (100, 100), 9: (200, 200), 10: (100, 200)} \
            == self.compute_layout(
                n_data=16, orientation='rl-bt', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 150), clock=kivy_clock)

    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    # |   | 5 | 9 |   |
    # |---|---|---|---|
    # |   | 6 | 10|   |
    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(4, None), (None, 4), (4, 4)])
    def test_4x4_tb_lr(self, kivy_clock, n_cols, n_rows):
        assert {5: (100, 200), 6: (100, 100), 9: (200, 200), 10: (200, 100)} \
            == self.compute_layout(
                n_data=16, orientation='tb-lr', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 150), clock=kivy_clock)

    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    # |   | 9 | 5 |   |
    # |---|---|---|---|
    # |   | 10| 6 |   |
    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(4, None), (None, 4), (4, 4)])
    def test_4x4_tb_rl(self, kivy_clock, n_cols, n_rows):
        assert {5: (200, 200), 6: (200, 100), 9: (100, 200), 10: (100, 100)} \
            == self.compute_layout(
                n_data=16, orientation='tb-rl', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 150), clock=kivy_clock)

    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    # |   | 6 | 10|   |
    # |---|---|---|---|
    # |   | 5 | 9 |   |
    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(4, None), (None, 4), (4, 4)])
    def test_4x4_bt_lr(self, kivy_clock, n_cols, n_rows):
        assert {5: (100, 100), 6: (100, 200), 9: (200, 100), 10: (200, 200)} \
            == self.compute_layout(
                n_data=16, orientation='bt-lr', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 150), clock=kivy_clock)

    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    # |   | 10| 6 |   |
    # |---|---|---|---|
    # |   | 9 | 5 |   |
    # |---|---|---|---|
    # |   |   |   |   |
    # |---|---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(4, None), (None, 4), (4, 4)])
    def test_4x4_bt_rl(self, kivy_clock, n_cols, n_rows):
        assert {5: (200, 100), 6: (200, 200), 9: (100, 100), 10: (100, 200)} \
            == self.compute_layout(
                n_data=16, orientation='bt-rl', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 150), clock=kivy_clock)
