'''
Graphics tests
==============

Testing the simple vertex instructions
'''

import sys
import pytest
import itertools
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

    def test_canvas_management(self):
        from kivy.graphics.boxshadow import BoxShadow
        from kivy.uix.widget import Widget
        from kivy.graphics import Color

        r = self.render

        wid = Widget()
        with wid.canvas:
            bs = BoxShadow()
        r(wid)
        assert bs in wid.canvas.children

        wid = Widget()
        bs = BoxShadow()
        wid.canvas.add(Color(1, 0, 0, 1))
        wid.canvas.add(bs)
        r(wid)
        assert bs in wid.canvas.children

        wid.canvas.remove(bs)
        assert bs not in wid.canvas.children

        wid.canvas.insert(1, bs)
        assert bs in wid.canvas.children
        assert wid.canvas.children.index(bs) == 1


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

    def test_enlarged_line(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Line, Color, PushMatrix, PopMatrix, Scale, \
            Translate
        r = self.render
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1)

            # Normal line with width 1
            Line(
                points=(10, 10, 10, 90),
                width=1
            )

            # Normal line with width 3
            Line(
                points=(20, 10, 20, 90),
                width=3
            )

            # Enlarged line that should look width 3
            PushMatrix()
            Translate(30, 10, 1)  # So the enlargement goes around 0, 0, 0
            Scale(3, 1, 1)  # X scaled by 3 so the line width should become 3
            Line(
                points=(0, 0, 0, 80),
                width=1,
                force_custom_drawing_method=True
            )
            PopMatrix()

        r(wid)


class SmoothVertexInstructionTest(GraphicUnitTest):

    # Code defined in the points setter of AntiAliasingLine class.
    def _convert_points(self, points):
        if points and isinstance(points[0], (list, tuple)):
            return list(itertools.chain(*points))
        else:
            return list(points)

    # The same function present in the AntiAliasingLine code,
    # externalized for testing.
    def _filtered_points(self, points):
        index = 0
        p = self._convert_points(points)

        # At least 3 points are required, otherwise we will return an empty
        # list, which means there are no valid points.
        if len(p) < 6:
            return []

        while index < len(p) - 2:
            x1, y1 = p[index], p[index + 1]
            x2, y2 = p[index + 2], p[index + 3]
            if abs(x2 - x1) < 1.0 and abs(y2 - y1) < 1.0:
                del p[index + 2: index + 4]
            else:
                index += 2
        if abs(p[0] - p[-2]) < 1.0 and abs(p[1] - p[-1]) < 1.0:
            del p[:2]
        return p

    def _get_texture(self):
        from kivy.graphics.texture import Texture
        return Texture.create()

    def test_antialiasing_line(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Rectangle, Instruction
        from kivy.graphics.vertex_instructions import AntiAliasingLine

        r = self.render

        # We expect a type error to be thrown if stencil_mask is not an object
        # of type Instruction.
        with pytest.raises(TypeError):
            AntiAliasingLine(None, points=[10, 20, 30, 20, 30, 10])

        # No TypeError here.
        target_rect = Rectangle()
        AntiAliasingLine(target_rect, points=[10, 20, 30, 40, 50, 60])

        # Test the gradient responsible for the "smooth line" effect.
        pixels = b"\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\x00"
        instruction = Instruction()
        aa_line = AntiAliasingLine(instruction)
        assert aa_line.texture.pixels == pixels
        # check the width, defined through tests with the custom texture.
        assert aa_line.width == 2.5

        # This set of points must remain unchanged.
        points_1 = [51.0, 649.0, 199.0, 649.0, 199.0, 501.0, 51.0, 501.0]

        # This set of points should be reduced from 16 to 8.
        points_2 = [
            261.0, 275.0,
            335.0, 349.0,
            335.0, 349.0,
            409.0, 275.0,
            409.0, 275.0,
            335.0, 201.0,
            335.0, 201.0,
            261.0, 275.0
        ]

        # This set of points should be reduced from 72 to 50.
        points_3 = [
            260.0, 275.0,
            261.0, 275.0,
            261.0, 275.0,
            261.999999999999, 275.99999999,
            261.06667650085353, 278.14064903651496,
            261.26658584785304, 281.2756384111877,
            261.56658584785305, 281.3756384111877,
            261.5993677908431, 284.39931866126904,
            262.0644226342696, 287.50606070381684,
            262.0644226342696, 287.50606070381684,
            262.6609123178712, 290.59026597968375,
            263.3877619269211, 293.6463765424993,
            264.2436616292954, 296.66888507446475,
            265.22706903587977, 299.65234481091227,
            265.22706903587977, 299.65234481091227,
            266.3362119800583, 302.59137935574284,
            267.5690917112779, 305.48069237005546,
            268.9234864969319, 308.31507711650784,
            270.39695562607204, 311.089425842209,
            270.89695562607204, 311.589425842209,
            271.98684380773494, 313.7987389832352,
            273.69028595595563, 316.4381341741821,
            275.50421235284637, 319.00285504651725,
            275.50421235284637, 319.00285504651725,
            277.4253541804354, 321.48827979987755,
            279.45024941129833, 323.8899295308661,
            281.57524904736516, 326.20347630433844,
            283.79652369566156, 328.4247509526349,
            283.99652369566156, 328.7247509526349,
            286.1100704691339, 330.54975058870167,
            288.5117202001224, 332.5746458195646,
            288.5117202001224, 332.5746458195646,
            290.99714495348275, 334.4957876471537,
            293.5618658258179, 336.3097140440444,
            293.5618658258179, 336.3097140440444,
            293.2618658258179, 336.1097140440444
        ]

        # This set of points should be reduced to [].
        points_4 = [100, 100, 200, 100]

        # line closed (default)
        for points in (points_1, points_2, points_3, points_4):
            wid = Widget()
            with wid.canvas:
                Color(1, 1, 1, 0.5)
                inst = Instruction()
                aa_line = AntiAliasingLine(inst, points=points)
            r(wid)
            filtered_points = self._filtered_points(points)
            assert aa_line.points == filtered_points + filtered_points[:2]

        # without closing the line
        for points in (points_1, points_2, points_3, points_4):
            wid = Widget()
            with wid.canvas:
                Color(1, 1, 1, 0.5)
                inst = Instruction()
                aa_line = AntiAliasingLine(inst, points=points, close=0)
            r(wid)
            assert aa_line.points == self._filtered_points(points)

    def test_smoothrectangle(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, SmoothRectangle

        r = self.render

        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1, 0.5)
            rect = SmoothRectangle(pos=(100, 100), size=(150, 150))
        r(wid)
        filtered_points = self._filtered_points(rect.points)
        assert (
            rect.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # test if antialiasing is disabled if the graphic has one of its
        # dimensions decreased to less than 4px.
        rect.size = (150, -2)
        r(wid)
        assert rect.antialiasing_line_points == []

        rect.size = (150, 2)
        r(wid)
        assert rect.antialiasing_line_points == []

        # re-enable antialiasing line rendering.
        rect.size = (150, 150)
        r(wid)
        assert (
            rect.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # disabling antialiasing.
        rect.texture = self._get_texture()
        r(wid)
        assert rect.antialiasing_line_points == []

        # re-enable antialiasing.
        rect.source = ""
        r(wid)
        assert (
            rect.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # test if antialiasing is disabled if the graphic is initialized with
        # at least one of its dimensions less than 4px.
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1, 0.5)
            rect = SmoothRectangle(pos=(100, 100), size=(150, -3))
        r(wid)
        assert rect.antialiasing_line_points == []

        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1, 0.5)
            rect = SmoothRectangle(pos=(100, 100), size=(3.99, 3.99))
        r(wid)
        assert rect.antialiasing_line_points == []

    def test_smoothroundedrectangle(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, SmoothRoundedRectangle

        r = self.render

        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1, 0.5)
            rounded_rect = SmoothRoundedRectangle(
                pos=(100, 100),
                size=(150, 150),
                radius=[(10, 50), (100, 50), (0, 150), (200, 50)],
                segments=60,
            )
        r(wid)
        filtered_points = self._filtered_points(rounded_rect.points)
        assert (
            rounded_rect.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # test if antialiasing is disabled if the graphic has one of its
        # dimensions decreased to less than 4px.
        rounded_rect.size = (150, -2)
        r(wid)
        assert rounded_rect.antialiasing_line_points == []

        rounded_rect.size = (150, 2)
        r(wid)
        assert rounded_rect.antialiasing_line_points == []

        # re-enable antialiasing line rendering.
        rounded_rect.size = (150, 150)
        r(wid)
        assert (
            rounded_rect.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # disabling antialiasing.
        rounded_rect.texture = self._get_texture()
        r(wid)
        assert rounded_rect.antialiasing_line_points == []

        # re-enable antialiasing.
        rounded_rect.source = ""
        r(wid)
        assert (
            rounded_rect.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1, 0.5)
            rounded_rect = SmoothRoundedRectangle(
                pos=(100, 100), size=(150, 150), segments=0
            )
        r(wid)
        filtered_points = self._filtered_points(rounded_rect.points)
        assert (
            rounded_rect.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # test if antialiasing is disabled if the graphic is initialized with
        # at least one of its dimensions less than 4px.
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1, 0.5)
            rounded_rect = SmoothRoundedRectangle(
                pos=(100, 100), size=(150, -3)
            )
        r(wid)
        assert rounded_rect.antialiasing_line_points == []

        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1, 0.5)
            rounded_rect = SmoothRoundedRectangle(
                pos=(100, 100), size=(3.99, 3.99)
            )
        r(wid)
        assert rounded_rect.antialiasing_line_points == []

    def test_smoothellipse(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, SmoothEllipse

        r = self.render

        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1, 0.5)
            ellipse = SmoothEllipse(pos=(100, 100), size=(150, 150))
        r(wid)
        ellipse_center = [
            ellipse.pos[0] + ellipse.size[0] / 2,
            ellipse.pos[1] + ellipse.size[1] / 2,
        ]
        filtered_points = self._filtered_points(
            ellipse.points + ellipse_center
        )
        assert (
            ellipse.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # test if antialiasing is disabled if the graphic has one of its
        # dimensions decreased to less than 4px
        ellipse.size = (150, -2)
        r(wid)
        assert ellipse.antialiasing_line_points == []

        ellipse.size = (150, 2)
        r(wid)
        assert ellipse.antialiasing_line_points == []

        # re-enable antialiasing line rendering.
        ellipse.size = (150, 150)
        r(wid)
        assert (
            ellipse.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # disabling antialiasing.
        ellipse.texture = self._get_texture()
        r(wid)
        assert ellipse.antialiasing_line_points == []

        # re-enable antialiasing.
        ellipse.source = ""
        r(wid)
        assert (
            ellipse.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1, 0.5)
            ellipse = SmoothEllipse(
                pos=(100, 100), size=(150, 150), angle_start=90, angle_end=-120
            )
        r(wid)
        ellipse_center = [
            ellipse.pos[0] + ellipse.size[0] / 2,
            ellipse.pos[1] + ellipse.size[1] / 2,
        ]
        filtered_points = self._filtered_points(
            ellipse.points + ellipse_center
        )
        assert (
            ellipse.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # test if antialiasing is disabled if the graphic is initialized with
        # at least one of its dimensions less than 4px.
        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1, 0.5)
            ellipse = SmoothEllipse(pos=(100, 100), size=(150, -3))
        r(wid)
        assert ellipse.antialiasing_line_points == []

        wid = Widget()
        with wid.canvas:
            Color(1, 1, 1, 0.5)
            ellipse = SmoothEllipse(pos=(100, 100), size=(3.99, 3.99))
        r(wid)
        assert ellipse.antialiasing_line_points == []

    def test_smoothtriangle(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, SmoothTriangle

        r = self.render

        wid = Widget()
        with wid.canvas:
            Color(1, 0, 0, 0.5)
            triangle = SmoothTriangle(
                points=[
                    100, 100,
                    200, 100,
                    150, 200,
                    500, 500, 400, 400  # Irrelevant, just for testing purposes
                ]
            )
        r(wid)
        filtered_points = self._filtered_points(triangle.points[:6])
        assert (
            triangle.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        wid = Widget()
        with wid.canvas:
            Color(0, 0, 1, 0.5)
            triangle = SmoothTriangle(
                points=[
                    125, 200,
                    200, 100,
                    100, 100,
                    500, 500, 400, 400  # Irrelevant, just for testing purposes
                ]
            )
        r(wid)
        filtered_points = self._filtered_points(triangle.points[:6])
        assert (
            triangle.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # Test disabling antialiasing if the points are very close.
        wid = Widget()
        with wid.canvas:
            Color(0, 1, 0, 0.5)
            triangle = SmoothTriangle(
                points=[100, 100, 100.5, 100, 100, 100.5]
            )
        r(wid)
        assert triangle.antialiasing_line_points == []

        # re-enable antialiasing line rendering.
        triangle.points = [125, 200, 200, 100, 100, 100]
        r(wid)
        assert (
            triangle.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # disabling antialiasing.
        triangle.texture = self._get_texture()
        r(wid)
        assert triangle.antialiasing_line_points == []

        # re-enable antialiasing.
        triangle.source = ""
        r(wid)
        assert (
            triangle.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

    def test_smoothquad(self):
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, SmoothQuad

        r = self.render

        wid = Widget()
        with wid.canvas:
            Color(1, 0, 0, 0.5)
            quad = SmoothQuad(points=[100, 100, 100, 200, 200, 200, 200, 100])
        r(wid)
        filtered_points = self._filtered_points(quad.points)
        assert (
            quad.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        wid = Widget()
        with wid.canvas:
            Color(1, 0, 0, 0.5)
            quad = SmoothQuad(points=[200, 100, 200, 200, 100, 200, 100, 100])
        r(wid)
        filtered_points = self._filtered_points(quad.points)
        assert (
            quad.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # Test disabling antialiasing if the points are very close.
        wid = Widget()
        with wid.canvas:
            Color(0, 1, 0, 0.5)
            quad = SmoothQuad(
                points=[200, 100, 200, 100.8, 100, 100.8, 100, 100]
            )
        r(wid)
        assert quad.antialiasing_line_points == []

        # re-enable antialiasing line rendering.
        quad.points = [200, 100, 200, 200, 100, 200, 100, 100]
        r(wid)
        assert (
            quad.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )

        # disabling antialiasing.
        quad.texture = self._get_texture()
        r(wid)
        assert quad.antialiasing_line_points == []

        # re-enable antialiasing.
        quad.source = ""
        r(wid)
        assert (
            quad.antialiasing_line_points
            == filtered_points + filtered_points[:2]
        )


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

    def check_transform_works(self, transform_type):
        # Normal args
        transform = transform_type(0, 1, 2)
        self.assertEqual(transform.x, 0)
        self.assertEqual(transform.y, 1)
        self.assertEqual(transform.z, 2)

        # Key word args
        transform = transform_type(x=0, y=1)
        self.assertEqual(transform.x, 0)
        self.assertEqual(transform.y, 1)

        transform = transform_type(x=0, y=1, z=2)
        self.assertEqual(transform.x, 0)
        self.assertEqual(transform.y, 1)
        self.assertEqual(transform.z, 2)

    def test_translate_creation(self):
        from kivy.graphics import Translate
        self.check_transform_works(Translate)

    def test_scale_creation(self):
        from kivy.graphics import Scale
        self.check_transform_works(Scale)


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
