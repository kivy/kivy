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
    # | 2 |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_lr_tb(self, kivy_clock, n_cols, n_rows):
        assert {0: (0, 100), 1: (100, 100), 2: (0, 0)} == self.compute_layout(
            n_data=3, orientation='lr-tb', n_cols=n_cols, n_rows=n_rows,
            clock=kivy_clock)

    # |---|
    # | 2 |
    # |---|---|
    # | 0 | 1 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_lr_bt(self, kivy_clock, n_cols, n_rows):
        assert {0: (0, 0), 1: (100, 0), 2: (0, 100)} == self.compute_layout(
            n_data=3, orientation='lr-bt', n_cols=n_cols, n_rows=n_rows,
            clock=kivy_clock)

    # |---|---|
    # | 1 | 0 |
    # |---|---|
    #     | 2 |
    #     |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_rl_tb(self, kivy_clock, n_cols, n_rows):
        assert {0: (100, 100), 1: (0, 100), 2: (100, 0)} == \
            self.compute_layout(
                n_data=3, orientation='rl-tb', n_cols=n_cols, n_rows=n_rows,
                clock=kivy_clock)

    #     |---|
    #     | 2 |
    # |---|---|
    # | 1 | 0 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_rl_bt(self, kivy_clock, n_cols, n_rows):
        assert {0: (100, 0), 1: (0, 0), 2: (100, 100)} == self.compute_layout(
            n_data=3, orientation='rl-bt', n_cols=n_cols, n_rows=n_rows,
            clock=kivy_clock)

    # |---|---|
    # | 0 | 2 |
    # |---|---|
    # | 1 |
    # |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_tb_lr(self, kivy_clock, n_cols, n_rows):
        assert {0: (0, 100), 1: (0, 0), 2: (100, 100)} == self.compute_layout(
            n_data=3, orientation='tb-lr', n_cols=n_cols, n_rows=n_rows,
            clock=kivy_clock)

    # |---|---|
    # | 2 | 0 |
    # |---|---|
    #     | 1 |
    #     |---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_tb_rl(self, kivy_clock, n_cols, n_rows):
        assert {0: (100, 100), 1: (100, 0), 2: (0, 100)} == \
            self.compute_layout(
                n_data=3, orientation='tb-rl', n_cols=n_cols, n_rows=n_rows,
                clock=kivy_clock)

    # |---|
    # | 1 |
    # |---|---|
    # | 0 | 2 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_bt_lr(self, kivy_clock, n_cols, n_rows):
        assert {0: (0, 0), 1: (0, 100), 2: (100, 0)} == self.compute_layout(
            n_data=3, orientation='bt-lr', n_cols=n_cols, n_rows=n_rows,
            clock=kivy_clock)

    #     |---|
    #     | 1 |
    # |---|---|
    # | 2 | 0 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(2, None), (None, 2), (2, 2)])
    def test_2x2_bt_rl(self, kivy_clock, n_cols, n_rows):
        assert {0: (100, 0), 1: (100, 100), 2: (0, 0)} == self.compute_layout(
            n_data=3, orientation='bt-rl', n_cols=n_cols, n_rows=n_rows,
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
        scrollable_width = layout.width - rv.width
        if scrollable_width:  # avoids ZeroDivisionError
            rv.scroll_x = x / scrollable_width
        scrollable_height = layout.height - rv.height
        if scrollable_height:  # avoids ZeroDivisionError
            rv.scroll_y = y / scrollable_height
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

    # |---|---|---|
    # |   |   |   |
    # |---|---|---|
    # |   | 4 | 5 |
    # |---|---|---|
    # |   | 7 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 3), (3, 3)])
    def test_3x3_lr_tb(self, kivy_clock, n_cols, n_rows):
        assert {4: (100, 100), 5: (200, 100), 7: (100, 0)} == \
            self.compute_layout(
                n_data=8, orientation='lr-tb', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 50), clock=kivy_clock)

    # |---|---|
    # |   | 7 |
    # |---|---|---|
    # |   | 4 | 5 |
    # |---|---|---|
    # |   |   |   |
    # |---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 3), (3, 3)])
    def test_3x3_lr_bt(self, kivy_clock, n_cols, n_rows):
        assert {4: (100, 100), 5: (200, 100), 7: (100, 200)} == \
            self.compute_layout(
                n_data=8, orientation='lr-bt', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 150), clock=kivy_clock)

    # |---|---|---|
    # |   |   |   |
    # |---|---|---|
    # | 5 | 4 |   |
    # |---|---|---|
    #     | 7 |   |
    #     |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 3), (3, 3)])
    def test_3x3_rl_tb(self, kivy_clock, n_cols, n_rows):
        assert {4: (100, 100), 5: (0, 100), 7: (100, 0)} == \
            self.compute_layout(
                n_data=8, orientation='rl-tb', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(50, 50), clock=kivy_clock)

    #     |---|---|
    #     | 7 |   |
    # |---|---|---|
    # | 5 | 4 |   |
    # |---|---|---|
    # |   |   |   |
    # |---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 3), (3, 3)])
    def test_3x3_rl_bt(self, kivy_clock, n_cols, n_rows):
        assert {4: (100, 100), 5: (0, 100), 7: (100, 200)} == \
            self.compute_layout(
                n_data=8, orientation='rl-bt', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(50, 150), clock=kivy_clock)

    # |---|---|---|
    # |   |   |   |
    # |---|---|---|
    # |   | 4 | 7 |
    # |---|---|---|
    # |   | 5 |
    # |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 3), (3, 3)])
    def test_3x3_tb_lr(self, kivy_clock, n_cols, n_rows):
        assert {4: (100, 100), 5: (100, 0), 7: (200, 100)} == \
            self.compute_layout(
                n_data=8, orientation='tb-lr', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 50), clock=kivy_clock)

    # |---|---|---|
    # |   |   |   |
    # |---|---|---|
    # | 7 | 4 |   |
    # |---|---|---|
    #     | 5 |   |
    #     |---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 3), (3, 3)])
    def test_3x3_tb_rl(self, kivy_clock, n_cols, n_rows):
        assert {4: (100, 100), 5: (100, 0), 7: (0, 100)} == \
            self.compute_layout(
                n_data=8, orientation='tb-rl', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(50, 50), clock=kivy_clock)

    # |---|---|
    # |   | 5 |
    # |---|---|---|
    # |   | 4 | 7 |
    # |---|---|---|
    # |   |   |   |
    # |---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 3), (3, 3)])
    def test_3x3_bt_lr(self, kivy_clock, n_cols, n_rows):
        assert {4: (100, 100), 5: (100, 200), 7: (200, 100)} == \
            self.compute_layout(
                n_data=8, orientation='bt-lr', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(150, 150), clock=kivy_clock)

    #     |---|---|
    #     | 5 |   |
    # |---|---|---|
    # | 7 | 4 |   |
    # |---|---|---|
    # |   |   |   |
    # |---|---|---|
    @pytest.mark.parametrize("n_cols, n_rows", [(3, None), (None, 3), (3, 3)])
    def test_3x3_bt_rl(self, kivy_clock, n_cols, n_rows):
        assert {4: (100, 100), 5: (100, 200), 7: (0, 100)} == \
            self.compute_layout(
                n_data=8, orientation='bt-rl', n_cols=n_cols, n_rows=n_rows,
                scroll_to=(50, 150), clock=kivy_clock)
