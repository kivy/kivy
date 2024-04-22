import itertools
import pytest


class Test_children_pos_when_all_the_data_is_visible:
    @classmethod
    def gen_size(cls, is_horizontal):
        '''
        >>> list(gen_size(True))
        [(100, 100), (200, 100), (300, 100), ...]
        >>> list(gen_size(False))
        [(100, 100), (100, 200), (100, 300), ...]
        '''
        w = h = 100
        if is_horizontal:
            w_incr, h_incr = 100, 0
        else:
            w_incr, h_incr = 0, 100
        while True:
            yield (w, h, )
            w += w_incr
            h += h_incr

    @classmethod
    def compute_layout(cls, *, ori, n_data, clock):
        '''Returns {view-index: pos, view-index: pos, ...}'''
        from textwrap import dedent
        from kivy.lang import Builder

        # Use Kvlang because RecycleView cannot be constructed from python
        rv = Builder.load_string(dedent(f'''
            RecycleView:
                viewclass: 'Widget'
                size: 1000, 1000
                RecycleBoxLayout:
                    id: layout
                    orientation: '{ori}'
                    default_size_hint: None, None
            '''))
        size_iter = cls.gen_size(rv.ids.layout._is_horizontal)
        rv.data = [
            {'width': w, 'height': h, }
            for w, h in itertools.islice(size_iter, n_data)
        ]
        clock.tick()
        clock.tick()
        layout = rv.ids.layout
        return {
            layout.get_view_index_at(c.center): tuple(c.pos)
            for c in layout.children
        }

    # |
    # |---|
    # | 0 |
    # |---|---
    def test_1x1(self, kivy_clock):
        from kivy.uix.recycleboxlayout import RecycleBoxLayout
        for ori in RecycleBoxLayout.orientation.options:
            assert {0: (0, 0), } == self.compute_layout(
                n_data=1, ori=ori, clock=kivy_clock)

    # |
    # |---|-----|-------|
    # | 0 |  1  |   2   |
    # |---|-----|-------|---
    @pytest.mark.parametrize('ori', ['horizontal', 'lr', ])
    def test_3x1_lr(self, kivy_clock, ori):
        assert {0: (0, 0), 1: (100, 0), 2: (300, 0), } == \
            self.compute_layout(n_data=3, ori=ori, clock=kivy_clock)

    # |
    # |-------|-----|---|
    # |   2   |  1  | 0 |
    # |-------|-----|---|---
    def test_3x1_rl(self, kivy_clock):
        assert {0: (500, 0), 1: (300, 0), 2: (0, 0), } == \
            self.compute_layout(n_data=3, ori='rl', clock=kivy_clock)

    # |
    # |---|
    # | 0 |
    # |---|
    # |   |
    # | 1 |
    # |---|
    # |   |
    # | 2 |
    # |   |
    # |---|---
    @pytest.mark.parametrize('ori', ['vertical', 'tb', ])
    def test_1x3_tb(self, kivy_clock, ori):
        assert {0: (0, 500), 1: (0, 300), 2: (0, 0), } == \
            self.compute_layout(n_data=3, ori=ori, clock=kivy_clock)

    # |
    # |---|
    # |   |
    # | 2 |
    # |   |
    # |---|
    # |   |
    # | 1 |
    # |---|
    # | 0 |
    # |---|---
    def test_1x3_bt(self, kivy_clock):
        assert {0: (0, 0), 1: (0, 100), 2: (0, 300), } == \
            self.compute_layout(n_data=3, ori='bt', clock=kivy_clock)


class Test_children_pos_when_only_a_part_of_the_data_is_visible:
    def compute_layout(self, *, ori, n_data, scroll_to, clock):
        '''Returns {view-index: pos, view-index: pos, ...}'''
        from textwrap import dedent
        from kivy.lang import Builder

        # Use Kvlang because RecycleView cannot be constructed from python
        rv = Builder.load_string(dedent(f'''
            RecycleView:
                viewclass: 'Widget'
                size: 100, 100
                data: ({{}} for __ in range({n_data}))
                RecycleBoxLayout:
                    id: layout
                    orientation: '{ori}'
                    default_size_hint: None, None
                    default_size: 100, 100
                    size_hint: None, None
                    size: 400, 400
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

    # |
    # |---|---|---|---|
    # |   | 1 | 2 |   |
    # |---|---|---|---|---
    @pytest.mark.parametrize('ori', ['horizontal', 'lr', ])
    def test_4x1_lr(self, kivy_clock, ori):
        assert {1: (100, 0), 2: (200, 0), } == self.compute_layout(
            n_data=4, ori=ori, scroll_to=(150, 0), clock=kivy_clock)

    # |
    # |---|---|---|---|
    # |   | 2 | 1 |   |
    # |---|---|---|---|---
    def test_4x1_rl(self, kivy_clock):
        assert {1: (200, 0), 2: (100, 0), } == self.compute_layout(
            n_data=4, ori='rl', scroll_to=(150, 0), clock=kivy_clock)

    # |
    # |---|
    # |   |
    # |---|
    # | 1 |
    # |---|
    # | 2 |
    # |---|
    # |   |
    # |---|---
    @pytest.mark.parametrize('ori', ['vertical', 'tb', ])
    def test_1x4_tb(self, kivy_clock, ori):
        assert {1: (0, 200), 2: (0, 100), } == self.compute_layout(
            n_data=4, ori=ori, scroll_to=(0, 150), clock=kivy_clock)

    # |
    # |---|
    # |   |
    # |---|
    # | 2 |
    # |---|
    # | 1 |
    # |---|
    # |   |
    # |---|---
    def test_1x4_bt(self, kivy_clock):
        assert {1: (0, 100), 2: (0, 200), } == self.compute_layout(
            n_data=4, ori='bt', scroll_to=(0, 150), clock=kivy_clock)


class Test_spacing:
    def compute_layout(self, *, ori, n_data, clock):
        '''Returns {view-index: pos, view-index: pos, ...}'''
        from textwrap import dedent
        from kivy.lang import Builder

        # Use Kvlang because RecycleView cannot be constructed from python
        rv = Builder.load_string(dedent(f'''
            RecycleView:
                viewclass: 'Widget'
                size: 1000, 1000
                data: ({{}} for __ in range({n_data}))
                RecycleBoxLayout:
                    id: layout
                    orientation: '{ori}'
                    spacing: 10
                    default_size_hint: None, None
                    default_size: 100, 100
            '''))
        clock.tick()
        clock.tick()
        layout = rv.ids.layout
        return {
            layout.get_view_index_at(c.center): tuple(c.pos)
            for c in layout.children
        }

    @pytest.mark.parametrize('ori', ['horizontal', 'lr', ])
    def test_3x1_lr(self, kivy_clock, ori):
        assert {0: (0, 0), 1: (110, 0), 2: (220, 0), } == self.compute_layout(
            n_data=3, ori=ori, clock=kivy_clock)

    def test_3x1_rl(self, kivy_clock):
        assert {2: (0, 0), 1: (110, 0), 0: (220, 0), } == self.compute_layout(
            n_data=3, ori='rl', clock=kivy_clock)

    @pytest.mark.parametrize('ori', ['vertical', 'tb', ])
    def test_1x3_tb(self, kivy_clock, ori):
        assert {0: (0, 220), 1: (0, 110), 2: (0, 0), } == self.compute_layout(
            n_data=3, ori=ori, clock=kivy_clock)

    def test_1x3_bt(self, kivy_clock):
        assert {0: (0, 0), 1: (0, 110), 2: (0, 220), } == self.compute_layout(
            n_data=3, ori='bt', clock=kivy_clock)
