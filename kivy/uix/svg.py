
'''
SVG widget
'''

__all__ = ('SVG', )

import xml.dom.minidom
from kivy.uix.widget import Widget
from kivy.resources import resource_find
from kivy.c_ext.properties import StringProperty, ObjectProperty, ListProperty
from kivy.c_ext.graphics import *
from kivy.logger import Logger
from kivy.svg import SVGData


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








