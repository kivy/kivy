'''
Slider
======

'''
__all__ = ('Slider', )

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, AliasProperty


class Slider(Widget):

    def __init__(self, **kwargs):
        super(Slider, self).__init__(**kwargs)

        def update_pos(*args):
            self.value_pos = (self.x+1, self.y)
        self.bind(pos=update_pos)
        self.bind(size=update_pos)

    #: Value of the slider
    value = NumericProperty(0)

    #: Minimum value of the slider (used for rendering)
    min = NumericProperty(0)

    #: Maximum value of the slider (used for rendering)
    max = NumericProperty(100)

    #: Range of the slider. same as (self.min, self.max)
    def get_range(self):
        return (self.min, self.max)

    def set_range(self, range):
        self.min, self.max = range
    range = AliasProperty(get_range, set_range, bind=('min', 'max'))

    #: The value of the slide normalized to the range [min - max]
    def get_norm_value(self):
        d = self.max - self.min
        if d == 0:
            return 0
        return (self.value - self.min) / float(d)

    def set_norm_value(self, n_val):
        self.value = n_val*(self.max-self.min) + self.min
    value_normalized = AliasProperty(get_norm_value, set_norm_value,
                                     bind=('value', 'min', 'max'))

    #: The value of the slider mapped to the screen position
    #  between self.x and self.right
    def get_value_pos(self):
        return  (self.x + self.value_normalized*self.width, self.y)

    def set_value_pos(self, pos):
        x = min(self.right, max(pos[0], self.x))
        y = min(self.top, max(pos[1], self.y))
        if self.width == 0:
            self.value_normalized = 0
        else:
            self.value_normalized = (x - self.x) / float(self.width)
    value_pos = AliasProperty(get_value_pos, set_value_pos,
                              bind=('value', 'min', 'max', 'value_normalized'))


    #: on touch_down handler. If inside slider:
    #  grab touch, set value based on touch pos
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            self.value_pos = touch.pos
            return True

    #: on_touch_move handler.  set value based on where the touch occured
    def on_touch_move(self, touch):
        if touch.grab_current == self:
            self.value_pos = touch.pos
            return True

    #: on_touch_up handler. set value based on touch pos, and ungrab touch
    def on_touch_up(self, touch):
        if touch.grab_current == self:
            self.value_pos = touch.pos
            return True


