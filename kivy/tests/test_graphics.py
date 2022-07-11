'''
Graphics tests
==============

Testing the simple vertex instructions
'''

import sys
import pytest
from threading import Thread
from kivy.tests.common import GraphicUnitTest, requires_graphics


class BoxShadowTest(GraphicUnitTest):

    def test_create(self):
        from kivy.graphics.boxshadow import BoxShadow
        from kivy.uix.widget import Widget
        from kivy.graphics import Color

        r = self.render

        # with initial arguments
        wid = Widget()
        with wid.canvas:
            Color(1, 0, 0, 1)
            bs = BoxShadow(
                pos=(50, 50),
                size=(150, 150),
                offset=(0, 10),
                spread_radius=(10, -10),
                border_radius=(10, 10, 10, 10),
                blur_radius=80,
            )
        r(wid)

        wid = Widget()
        with wid.canvas:
            Color(0, 1, 0, 1)
            bs = BoxShadow(
                inset=True,
                pos=(50, 50),
                size=(150, 150),
                offset=(0, 10),
                spread_radius=(10, -10),
                border_radius=(10, 10, 10, 10),
                blur_radius=80,
            )
        r(wid)

        # changing properties later
        wid = Widget()
        with wid.canvas:
            Color(0, 0, 1, 1)
            bs = BoxShadow()
        bs.inset = True
        bs.pos = [50, 50]
        bs.size = [150, 150]
        bs.offset = [0, 10]
        bs.spread_radius = [10, -10]
        bs.border_radius = [10, 10, 10, 10]
        bs.blur_radius = 40
        r(wid)

    def test_adjusted_size(self):
        from kivy.graphics.boxshadow import BoxShadow

        raw_size = 150, 150

        bs = BoxShadow()
        bs.pos = 50, 50
        bs.size = raw_size
        bs.blur_radius = 80
        bs.spread_radius = -10, 10

        # The size of the rectangle containing the FBO texture (shadow) needs
        # to be adjusted according to the size of the shadow, otherwise there
        # will be an unwanted cropping behavior.
        adjusted_size = (
            max(
                0,
                raw_size[0] + bs.blur_radius * 3 + bs.spread_radius[0] * 2,
            ),
            max(
                0,
                raw_size[1] + bs.blur_radius * 3 + bs.spread_radius[1] * 2,
            ),
        )

        assert bs.size == adjusted_size

        # Now we will turn on the inset mode, it is expected that
        # there will be no size adjustments.
        bs.inset = True
        assert bs.size == raw_size

        # Now turning off, and reverting back to the default mode.
        bs.inset = False
        assert bs.size == adjusted_size

        # Testing with initial arguments
        bs = BoxShadow(
            inset=True,
            pos=(50, 50),
            size=raw_size,
            blur_radius=80,
            spread_radius=(10, -10)
        )
        adjusted_size = (
            max(
                0,
                raw_size[0] + bs.blur_radius * 3 + bs.spread_radius[0] * 2,
            ),
            max(
                0,
                raw_size[1] + bs.blur_radius * 3 + bs.spread_radius[1] * 2,
            ),
        )

        assert bs.size == raw_size

        # Now turning off, and reverting back to the default mode.
        bs.inset = False
        assert bs.size == adjusted_size

        # Now we will turn on the inset mode, it is expected that
        # there will be no size adjustments.
        bs.inset = True
        assert bs.size == raw_size

    def test_adjusted_pos(self):
        from kivy.graphics.boxshadow import BoxShadow

        raw_pos = 50, 50
        raw_size = 150, 150
        offset = 10, -100

        bs = BoxShadow()
        bs.pos = raw_pos
        bs.size = raw_size
        bs.offset = offset
        bs.blur_radius = 80
        bs.spread_radius = -10, 10

        # If the size of the rectangle containing the FBO texture (shadow)
        # changes, its position will need to be adjusted.
        adjusted_pos = (
            raw_pos[0]
            - bs.blur_radius * 1.5
            - bs.spread_radius[0]
            + bs.offset[0],
            raw_pos[0]
            - bs.blur_radius * 1.5
            - bs.spread_radius[1]
            + bs.offset[1],
        )

        assert bs.pos == adjusted_pos

        # Now we will turn on the inset mode, it is expected that
        # there will be no position adjustments.
        bs.inset = True
        assert bs.pos == raw_pos

        # Now turning off, and reverting back to the default mode.
        bs.inset = False
        assert bs.pos == adjusted_pos

        # Testing with initial arguments
        bs = BoxShadow(
            inset=True,
            pos=raw_pos,
            size=raw_size,
            offset=offset,
            blur_radius=80,
            spread_radius=(10, -10)
        )
        adjusted_pos = (
            raw_pos[0]
            - bs.blur_radius * 1.5
            - bs.spread_radius[0]
            + bs.offset[0],
            raw_pos[0]
            - bs.blur_radius * 1.5
            - bs.spread_radius[1]
            + bs.offset[1],
        )

        assert bs.pos == raw_pos

        # Now turning off, and reverting back to the default mode.
        bs.inset = False
        assert bs.pos == adjusted_pos

        # Now we will turn on the inset mode, it is expected that
        # there will be no position adjustments.
        bs.inset = True
        assert bs.pos == raw_pos

    def test_bounded_properties(self):
        from kivy.graphics.boxshadow import BoxShadow

        bs = BoxShadow()
        bs.pos = 50, 50
        bs.size = 150, 150
        bs.offset = 10, -100
        bs.blur_radius = -80
        bs.spread_radius = -200, -100
        bs.border_radius = 0, 0, 100, 0

        assert bs.size == (0, 0)
        assert bs.blur_radius == 0

        # There is a bug in RoundedRectangle that distorts the texture if the
        # radius value is less than 1. Otherwise, it could be 0.
        assert bs.border_radius == tuple(
            map(
                lambda value: max(1.0, min(value, min(bs.size) / 2)),
                bs.border_radius,
            )
        )

        # Testing with initial arguments
        bs = BoxShadow(
            pos=(50, 50),
            size=(150, 150),
            offset=(10, -100),
            blur_radius=-80,
            spread_radius=(-200, -100),
            border_radius=(0, 0, 100, 0),
        )

        assert bs.size == (0, 0)
        assert bs.blur_radius == 0
        assert bs.border_radius == tuple(
            map(
                lambda value: max(1.0, min(value, min(bs.size) / 2)),
                bs.border_radius,
            )
        )


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

    def test_line_rounded_rectangle(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Line, Color
        r = self.render

        # basic rounded_rectangle
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            line = Line(
                rounded_rectangle=(100, 100, 100, 100, 10, 20, 30, 40, 100)
            )
        r(wid)
        assert line.rounded_rectangle == (
            100, 100, 100, 100, 10, 20, 30, 40, 100
        )

        # The largest angle allowed is equal to the smallest dimension (width
        # or height) minus the largest angle value between the anterior angle
        # and the posterior angle.
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            line = Line(
                rounded_rectangle=(
                    100, 100, 100, 100, 100, 20, 10, 30, 100
                )
            )
        r(wid)
        assert line.rounded_rectangle == (
            100, 100, 100, 100, 70, 20, 10, 30, 100
        )

        # Same approach as above
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            line = Line(
                rounded_rectangle=(
                    100, 100, 100, 100, 100, 25, 100, 50, 100
                )
            )
        r(wid)
        assert line.rounded_rectangle == (
            100, 100, 100, 100, 50, 25, 50, 50, 100
        )

        # A circle should be generated if width and height are equal, and all
        # angles passed are greater than or equal to the smallest dimension.
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            line = Line(
                rounded_rectangle=(
                    100, 100, 100, 100, 150, 50, 50.001, 51, 100
                )
            )
        r(wid)
        assert line.rounded_rectangle == (
            100, 100, 100, 100, 50, 50, 50, 50, 100
        )

        # Currently the minimum radius should be 1, to avoid rendering issues
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            line = Line(
                rounded_rectangle=(
                    100, 100, 100, 100, 0, 0, 0, 0, 100
                )
            )
        r(wid)
        assert line.rounded_rectangle == (
            100, 100, 100, 100, 1, 1, 1, 1, 100
        )

        # Angles adjustment + avoid issue if radius is less than 1
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            line = Line(
                rounded_rectangle=(
                    100, 100, 100, 100, 100, 0, 0, 0, 100
                )
            )
        r(wid)
        assert line.rounded_rectangle == (
            100, 100, 100, 100, 99, 1, 1, 1, 100
        )

    def test_smoothline_rounded_rectangle(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import SmoothLine, Color
        r = self.render

        # If width and/or height < 2px, the figure should not be rendered.
        # This avoids some known SmoothLine rendering issues.
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)
            line = SmoothLine(
                rounded_rectangle=(100, 100, 0.5, 1.99, 30, 30, 30, 30, 100)
            )
        r(wid)
        assert line.rounded_rectangle is None


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


@pytest.fixture
def widget_verify_thread(request):
    from kivy.uix.widget import Widget
    from kivy.config import Config

    original = Config.get('graphics', 'verify_gl_main_thread')
    Config.set('graphics', 'verify_gl_main_thread', request.param)

    widget = Widget()
    yield widget, request.param

    Config.set('graphics', 'verify_gl_main_thread', original)


@requires_graphics
@pytest.mark.parametrize('widget_verify_thread', ['0', '1'], indirect=True)
def test_graphics_main_thread(widget_verify_thread):
    from kivy.graphics import Color

    widget, verify_thread = widget_verify_thread
    with widget.canvas:
        color = Color()
    color.rgb = .1, .2, .3


@requires_graphics
@pytest.mark.parametrize('widget_verify_thread', ['0', '1'], indirect=True)
def test_create_graphics_second_thread(widget_verify_thread):
    from kivy.graphics import Color
    widget, verify_thread = widget_verify_thread
    exception = None

    def callback():
        nonlocal exception
        try:
            with widget.canvas:
                if verify_thread == '1':
                    with pytest.raises(TypeError):
                        Color()
                else:
                    Color()
        except BaseException as e:
            exception = e, sys.exc_info()[2]
            raise

    thread = Thread(target=callback)
    thread.start()
    thread.join()
    if exception is not None:
        raise exception[0].with_traceback(exception[1])


@requires_graphics
@pytest.mark.parametrize('widget_verify_thread', ['0', '1'], indirect=True)
def test_change_graphics_second_thread(widget_verify_thread):
    from kivy.graphics import Color
    widget, verify_thread = widget_verify_thread
    with widget.canvas:
        color = Color()

    exception = None

    def callback():
        nonlocal exception
        try:
            if verify_thread == '1':
                with pytest.raises(TypeError):
                    color.rgb = .1, .2, .3
            else:
                color.rgb = .1, .2, .3
        except BaseException as e:
            exception = e, sys.exc_info()[2]
            raise

    thread = Thread(target=callback)
    thread.start()
    thread.join()
    if exception is not None:
        raise exception[0].with_traceback(exception[1])
