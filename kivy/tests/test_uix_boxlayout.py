'''
Box layout unit test
====================

Order matter.
On the screen, most of example must have the red->blue->green order.
'''

import pytest
from kivy.tests.common import GraphicUnitTest


class UIXBoxLayoutTestcase(GraphicUnitTest):

    def box(self, r, g, b):
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Rectangle
        wid = Widget()
        with wid.canvas:
            Color(r, g, b)
            r = Rectangle(pos=wid.pos, size=wid.size)

        def linksp(instance, *largs):
            r.pos = instance.pos
            r.size = instance.size
        wid.bind(pos=linksp, size=linksp)
        return wid

    def test_boxlayout_orientation(self):
        from kivy.uix.boxlayout import BoxLayout
        r = self.render
        b = self.box

        layout = BoxLayout()
        layout.add_widget(b(1, 0, 0))
        layout.add_widget(b(0, 1, 0))
        layout.add_widget(b(0, 0, 1))
        r(layout)

        layout = BoxLayout(orientation='vertical')
        layout.add_widget(b(1, 0, 0))
        layout.add_widget(b(0, 1, 0))
        layout.add_widget(b(0, 0, 1))
        r(layout)

    def test_boxlayout_spacing(self):
        from kivy.uix.boxlayout import BoxLayout
        r = self.render
        b = self.box

        layout = BoxLayout(spacing=20)
        layout.add_widget(b(1, 0, 0))
        layout.add_widget(b(0, 1, 0))
        layout.add_widget(b(0, 0, 1))
        r(layout)

        layout = BoxLayout(spacing=20, orientation='vertical')
        layout.add_widget(b(1, 0, 0))
        layout.add_widget(b(0, 1, 0))
        layout.add_widget(b(0, 0, 1))
        r(layout)

    def test_boxlayout_padding(self):
        from kivy.uix.boxlayout import BoxLayout
        r = self.render
        b = self.box

        layout = BoxLayout(padding=20)
        layout.add_widget(b(1, 0, 0))
        layout.add_widget(b(0, 1, 0))
        layout.add_widget(b(0, 0, 1))
        r(layout)

        layout = BoxLayout(padding=20, orientation='vertical')
        layout.add_widget(b(1, 0, 0))
        layout.add_widget(b(0, 1, 0))
        layout.add_widget(b(0, 0, 1))
        r(layout)

    def test_boxlayout_padding_spacing(self):
        from kivy.uix.boxlayout import BoxLayout
        r = self.render
        b = self.box

        layout = BoxLayout(spacing=20, padding=20)
        layout.add_widget(b(1, 0, 0))
        layout.add_widget(b(0, 1, 0))
        layout.add_widget(b(0, 0, 1))
        r(layout)

        layout = BoxLayout(spacing=20, padding=20, orientation='vertical')
        layout.add_widget(b(1, 0, 0))
        layout.add_widget(b(0, 1, 0))
        layout.add_widget(b(0, 0, 1))
        r(layout)


class Test_internal_property:
    @pytest.mark.parametrize(
        "ori, expect", [
            ('horizontal', True, ),
            ('lr', True, ),
            ('rl', True, ),
            ('vertical', False, ),
            ('tb', False, ),
            ('bt', False, ),
        ]
    )
    def test_is_horizontal(self, ori, expect):
        from kivy.uix.boxlayout import BoxLayout
        box = BoxLayout(orientation=ori)
        assert box._is_horizontal is expect

    @pytest.mark.parametrize(
        "ori, expect", [
            ('horizontal', True, ),
            ('lr', True, ),
            ('rl', False, ),
            ('vertical', False, ),
            ('tb', False, ),
            ('bt', True, ),
        ]
    )
    def test_is_forward_direction(self, ori, expect):
        from kivy.uix.boxlayout import BoxLayout
        box = BoxLayout(orientation=ori)
        assert box._is_forward_direction is expect


class Test_children_pos:
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
    def compute_layout(cls, *, ori, n_children):
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout
        box = BoxLayout(orientation=ori, pos=(0, 0, ), size=(400, 400, ))
        size_iter = cls.gen_size(box._is_horizontal)
        for i, size in zip(range(n_children), size_iter):
            # Set the position of the children to a value other than the
            # default (0, 0) to ensure that the result is not affected by the
            # default position.
            box.add_widget(Label(
                text=str(i), size_hint=(None, None), size=size, pos=(8, 8)))
        box.do_layout()
        return {int(c.text): tuple(c.pos) for c in box.children}

    # |
    # |---|
    # | 0 |
    # |---|---
    def test_1x1(self):
        from kivy.uix.boxlayout import BoxLayout
        for ori in BoxLayout.orientation.options:
            assert {0: (0, 0), } == self.compute_layout(n_children=1, ori=ori)

    # |
    # |---|-----|-------|
    # | 0 |  1  |   2   |
    # |---|-----|-------|---
    @pytest.mark.parametrize('ori', ['horizontal', 'lr', ])
    def test_3x1_lr(self, ori):
        assert {0: (0, 0), 1: (100, 0), 2: (300, 0), } == \
            self.compute_layout(n_children=3, ori=ori)

    # |
    # |-------|-----|---|
    # |   2   |  1  | 0 |
    # |-------|-----|---|---
    def test_3x1_rl(self):
        assert {2: (0, 0), 1: (300, 0), 0: (500, 0), } == \
            self.compute_layout(n_children=3, ori='rl')

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
    def test_1x3_tb(self, ori):
        assert {2: (0, 0), 1: (0, 300), 0: (0, 500), } == \
            self.compute_layout(n_children=3, ori=ori)

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
    def test_1x3_bt(self):
        assert {0: (0, 0), 1: (0, 100), 2: (0, 300), } == \
            self.compute_layout(n_children=3, ori='bt')
