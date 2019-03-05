'''
Graphics tests
==============

Testing the simple vertex instructions
'''

from kivy.tests.common import GraphicUnitTest


class VertexInstructionTest(GraphicUnitTest):

    def test_circle(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Ellipse, Color
        r = self.render

        # basic circle
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            Ellipse(pos=(100, 100), size=(100, 100))
        r(wid)

        # reduced circle
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            Ellipse(pos=(100, 100), size=(100, 100), segments=10)
        r(wid)

        # moving circle
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            self.e = Ellipse(pos=(100, 100), size=(100, 100))
        self.e.pos = (10, 10)
        r(wid)

    def test_ellipse(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Ellipse, Color
        r = self.render

        # ellipse
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            self.e = Ellipse(pos=(100, 100), size=(200, 100))
        r(wid)

    def test_point(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Point, Color
        r = self.render

        # 1 point
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            Point(points=(10, 10))
        r(wid)

        # 25 points
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            Point(points=[x * 5 for x in range(50)])
        r(wid)

    def test_point_add(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Point, Color
        r = self.render

        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            p = Point(pointsize=10)

        p.add_point(10, 10)
        p.add_point(90, 10)
        p.add_point(10, 90)
        p.add_point(50, 50)
        p.add_point(10, 50)
        p.add_point(50, 10)

        r(wid)


class FBOInstructionTestCase(GraphicUnitTest):

    def test_fbo_pixels(self):
        from kivy.graphics import Fbo, ClearColor, ClearBuffers, Ellipse

        fbo = Fbo(size=(512, 512))
        with fbo:
            ClearColor(0, 0, 0, 1)
            ClearBuffers()
            Ellipse(pos=(100, 100), size=(100, 100))
        fbo.draw()
        data = fbo.pixels
        fbo.texture.save('results.png')


class TransformationsTestCase(GraphicUnitTest):

    def test_identity_creation(self):
        from kivy.graphics import LoadIdentity
        mat = LoadIdentity()
        self.assertTrue(mat.stack)


class CallbackInstructionTest(GraphicUnitTest):

    def test_from_kv(self):
        from textwrap import dedent
        from kivy.lang import Builder

        root = Builder.load_string(dedent("""\
        Widget:
            canvas:
                Callback:
                    callback: lambda __: setattr(self, 'callback_test', 'TEST')
        """))
        r = self.render
        r(root)
        self.assertTrue(root.callback_test == 'TEST')
