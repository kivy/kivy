'''
Slider:

'''

from kivy.uix.widget import Widget
from kivy.c_ext.properties import NumericProperty

class Slider(Widget):
    def __init__(self, **kwargs):
        super(Slider, self).__init__(**kwargs)

    #: Value of the slider
    value = NumericProperty(0)

    #: Minimum value of the slider (used for rendering)
    min = NumericProperty(0)

    #: Maximum value of the slider (used for rendering)
    max = NumericProperty(100)


