'''
Slider:

'''
__all__ = ('Slider', )


from kivy.uix.widget import Widget
from kivy.c_ext.properties import NumericProperty, AliasProperty




class Slider(Widget):
    def __init__(self, **kwargs):
        super(Slider, self).__init__(**kwargs)

    #: Value of the slider
    value = NumericProperty(0)

    #: Minimum value of the slider (used for rendering)
    min = NumericProperty(0)

    #: Maximum value of the slider (used for rendering)
    max = NumericProperty(100)

    def _handle_pos(self):
        'x,y position of the slider handle'
        offset = (self.value - self.min) / (self.width/(self.max-self.min)) 
        return [self.x+offset, self.x, self.y]
    handle_pos = AliasProperty(_handle_pos, None) 

