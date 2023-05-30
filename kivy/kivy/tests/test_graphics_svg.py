'''
Svg tests
==============

Testing Svg rendering.
'''

from kivy.tests.common import GraphicUnitTest


SIMPLE_SVG = """<?xml version="1.0" standalone="no"?>
<svg width="256" height="256" viewBox="0 0 256 256" version="1.1"
    xmlns="http://www.w3.org/2000/svg">
<rect stroke="blue" stroke-width="4" x="24" y="30" width="92" height="166"
    fill="none" stroke-opacity="0.5" />
</svg>
"""

SCALE_SVG = """<?xml version="1.0" standalone="no"?>
<svg width="256" height="256" viewBox="0 0 256 256" version="1.1"
    xmlns="http://www.w3.org/2000/svg">
<rect stroke="red" stroke-width="4" x="24" y="30" width="10" height="10"
    fill="none" stroke-opacity="0.5" transform="scale(2, 3)"/>
</svg>
"""

ROTATE_SVG = """<?xml version="1.0" standalone="no"?>
<svg width="256" height="256" viewBox="0 0 256 256" version="1.1"
    xmlns="http://www.w3.org/2000/svg">
<rect stroke="green" stroke-width="4" x="24" y="30" width="50" height="100"
    stroke-opacity="0.75" transform="rotate(60 128 128)" />
</svg>
"""


class SvgTest(GraphicUnitTest):

    def test_simple(self):
        import xml.etree.ElementTree as ET
        from kivy.uix.widget import Widget
        from kivy.graphics.svg import Svg

        # create a root widget
        wid = Widget()

        # put some graphics instruction on it
        with wid.canvas:
            svg = Svg()
            svg.set_tree(ET.ElementTree(ET.fromstring(SIMPLE_SVG)))

        # render, and capture it directly
        self.render(wid)

    def test_scale(self):
        import xml.etree.ElementTree as ET
        from kivy.uix.widget import Widget
        from kivy.graphics.svg import Svg

        # create a root widget
        wid = Widget()

        # put some graphics instruction on it
        with wid.canvas:
            svg = Svg()
            svg.set_tree(ET.ElementTree(ET.fromstring(SCALE_SVG)))

        # render, and capture it directly
        self.render(wid)

    def test_rotate(self):
        import xml.etree.ElementTree as ET
        from kivy.uix.widget import Widget
        from kivy.graphics.svg import Svg

        # create a root widget
        wid = Widget()

        # put some graphics instruction on it
        with wid.canvas:
            svg = Svg()
            svg.set_tree(ET.ElementTree(ET.fromstring(ROTATE_SVG)))

        # render, and capture it directly
        self.render(wid)
