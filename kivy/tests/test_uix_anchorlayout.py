'''
Anchor layout unit test
=======================
'''

from kivy.tests.common import GraphicUnitTest


class UIXAnchorLayoutTestcase(GraphicUnitTest):

    def box(self, r, g, b):
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Rectangle
        wid = Widget(size_hint=(None, None), size=(100, 100))
        with wid.canvas:
            Color(r, g, b)
            r = Rectangle(pos=wid.pos, size=wid.size)

        def linksp(instance, *largs):
            r.pos = instance.pos
            r.size = instance.size
        wid.bind(pos=linksp, size=linksp)
        return wid

    def test_anchorlayout_default(self):
        from kivy.uix.anchorlayout import AnchorLayout
        r = self.render
        b = self.box

        layout = AnchorLayout()
        layout.add_widget(b(1, 0, 0))
        r(layout)

    def test_anchorlayout_x(self):
        from kivy.uix.anchorlayout import AnchorLayout
        r = self.render
        b = self.box

        layout = AnchorLayout(anchor_x='left')
        layout.add_widget(b(1, 0, 0))
        r(layout)

        layout = AnchorLayout(anchor_x='center')
        layout.add_widget(b(1, 0, 0))
        r(layout)

        layout = AnchorLayout(anchor_x='right')
        layout.add_widget(b(1, 0, 0))
        r(layout)

    def test_anchorlayout_y(self):
        from kivy.uix.anchorlayout import AnchorLayout
        r = self.render
        b = self.box

        layout = AnchorLayout(anchor_y='bottom')
        layout.add_widget(b(1, 0, 0))
        r(layout)

        layout = AnchorLayout(anchor_y='center')
        layout.add_widget(b(1, 0, 0))
        r(layout)

        layout = AnchorLayout(anchor_y='top')
        layout.add_widget(b(1, 0, 0))
        r(layout)

    def test_anchor_layout_xy(self):
        from kivy.uix.anchorlayout import AnchorLayout
        r = self.render
        b = self.box

        layout = AnchorLayout(anchor_y='bottom', anchor_x='left')
        layout.add_widget(b(1, 0, 0))
        r(layout)

        layout = AnchorLayout(anchor_y='top', anchor_x='right')
        layout.add_widget(b(1, 0, 0))
        r(layout)


class TestAnchorLayout:

    def test_anchorlayout_no_height_control(self):
        from kivy.uix.widget import Widget
        from kivy.uix.anchorlayout import AnchorLayout

        def update_height(widget, value):
            widget.height = 2 * widget.width

        widget = Widget(size_hint=(1, None))
        widget.bind(width=update_height)
        layout = AnchorLayout(size=(1000, 1000))
        layout.add_widget(widget)

        layout.do_layout()

        assert widget.size == [1000, 2000]
        assert widget.pos == [0, -500]

    def test_anchorlayout_no_width_control(self):
        from kivy.uix.widget import Widget
        from kivy.uix.anchorlayout import AnchorLayout

        def update_width(widget, value):
            widget.width = 2 * widget.height

        widget = Widget(size_hint=(None, 1))
        widget.bind(height=update_width)
        layout = AnchorLayout(size=(1000, 1000))
        layout.add_widget(widget)

        layout.do_layout()

        assert widget.size == [2000, 1000]
        assert widget.pos == [-500, 0]
