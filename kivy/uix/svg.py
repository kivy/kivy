
'''
SVG widget
'''

__all__ = ('SVG', )

from kivy.uix.widget import Widget
from kivy.properties import StringProperty
from kivy.graphics import SVGData


class SVG(Widget):
    """
    SVG Widget:  basic widget that reads an svg file and draws the contents
    """
    #: Filename of the svg graphic
    source = StringProperty(None)

    #: SVG data element
    def on_source(self, instance, value):
        print "laoding", value
        self.svg_data = SVGData(value)

