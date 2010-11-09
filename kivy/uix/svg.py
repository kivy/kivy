
'''
SVG widget
'''

__all__ = ('SVG', )

from xml.dom.minidom import parse
from kivy.uix.widget import Widget
from kivy.resources import resource_find
from kivy.c_ext.properties import StringProperty, ObjectProperty, ListProperty
from kivy.c_ext.graphics import *

def t(*args):
    print "ASASASAS", args

class SVG(Widget):


    #: Filename of the image
    fname = StringProperty("")


    def __init__(self, **kwargs):
        super(SVG, self).__init__()


        with self.canvas:

            Color(1,0,0 ,1)
            doc = parse('examples/test.svg') 
            root = doc.documentElement

            path = root.getElementsByTagName("path")[0]
            attribs = dict(path.attributes.items())
            svg_data = attribs['d']

            instruction = ""
            origin = (0,0)
            pos = None
            for command in svg_data.split(' '):
                if command.isalpha():
                    if command.isupper():
                        origin = (0,0)
                    else:
                        print "setting pos, fpor relative"
                        origin = pos

                    instruction = command
                else:
                    npos = tuple(map(float, command.split(',')))
                    pos = npos
                    x = (origin[0]+ pos[0]) *0.5
                    y = (origin[1]+ pos[1]) *0.5
                    print "#######  ", instruction, (x,y)
                    #instruction(x,y)
                    
                    
