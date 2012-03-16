'''
Box layout unit test
====================

Order matter.
On the screen, most of example must have the red->blue->green order.
'''

from common import GraphicUnitTest


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
