"""
RangeSlider
======
"""


__all__ = ('RangeSlider', )

from kivy.uix.slider import Slider
from kivy.properties import (AliasProperty, ListProperty)


class RangeSlider(Slider):
    """Class for creating a RangeSlider widget.
    """

    value_range = ListProperty([0., 100.])
    '''Current value used for the rangeslider.

    :attr:`value_range` is a :class:`~kivy.properties.ListProperty` and
    defaults to [0, 100.].'''

    def on_min(self, *largs):
        self.value_range = [min(self.max, max(self.min, self.value_range[0])),
                    min(self.max, max(self.min, self.value_range[1]))]

    def on_max(self, *largs):
        self.value_range = [min(self.max, max(self.min, self.value_range[0])),
                    min(self.max, max(self.min, self.value_range[1]))]

    def get_norm_value(self):
        vmin = self.min
        d = self.max - vmin
        if d == 0:
            return 0
        return [(self.value_range[0] - vmin) / float(d),
                (self.value_range[1] - vmin) / float(d)]

    def set_norm_value(self, value):
        vmin = self.min
        vmax = self.max
        step = self.step
        val = [min(value[0] * (vmax - vmin) + vmin, vmax),
                min(value[1] * (vmax - vmin) + vmin, vmax)]
        if step == 0:
            self.value_range = val
        else:
            self.value_range = [min(round((val[0] - vmin) / step) * step +
                             vmin, vmax),
                             min(round((val[1] - vmin) / step) * step + vmin,
                             vmax)]

    value_normalized_slider = AliasProperty(get_norm_value, set_norm_value,
                                bind=('value_range', 'min', 'max', 'step'))

    def get_value_pos(self):
        padding = self.padding
        x = self.x
        y = self.y
        nval = self.value_normalized_slider
        if self.orientation == 'horizontal':
            return [(x + padding + nval[0] * (self.width - 2 * padding), y),
                    (x + padding + nval[1] * (self.width - 2 * padding), y)]
        else:
            return [(x, y + padding + nval[0] * (self.height - 2 * padding)),
                    (x, y + padding + nval[1] * (self.height - 2 * padding))]

    def set_value_pos(self, pos):
        padding = self.padding
        x_left = min(self.right - padding, max(pos[0][0], self.x + padding))
        y_bottom = min(self.top - padding, max(pos[0][1], self.y + padding))
        x_right = min(self.right - padding, max(pos[1][0], self.x + padding))
        y_top = min(self.top - padding, max(pos[1][1], self.y + padding))
        if self.orientation == 'horizontal':
            if self.width == 0:
                self.value_normalized_slider = [0, 1.]
            else:
                self.value_normalized_slider = [(x_left - self.x - padding) /
                                         float(self.width - 2 * padding),
                                         (x_right - self.x - padding) /
                                         float(self.width - 2 * padding)]
        else:
            if self.height == 0:
                self.value_normalized_slider = [0, 1.]
            else:
                self.value_normalized_slider = [(y_bottom - self.y - padding) /
                                         float(self.height - 2 * padding),
                                         (y_top - self.y - padding) /
                                         float(self.height - 2 * padding)]

    value_pos_slider = AliasProperty(get_value_pos, set_value_pos,
                              bind=('x', 'y', 'width', 'height', 'min',
                            'max', 'value_normalized_slider', 'orientation'))
    '''Position of the internal cursor, based on the normalized value.

    :attr:`value_pos_slider` is an :class:`~kivy.properties.AliasProperty`.
    '''

    def on_touch_down(self, touch):
        if self.disabled or not self.collide_point(*touch.pos):
            return
        if touch.is_mouse_scrolling:
            if 'down' in touch.button or 'left' in touch.button:
                if self.step:
                    self.value_range = min(self.max, self.value_range +
                                            self.step)
                else:
                    self.value_range = min(
                        self.max,
                        self.value_range + (self.max - self.min) / 20)
            if 'up' in touch.button or 'right' in touch.button:
                if self.step:
                    self.value_range = max(self.min, self.value_range -
                                            self.step)
                else:
                    self.value_range = max(
                        self.min,
                        self.value_range - (self.max - self.min) / 20)
        else:
            touch.grab(self)
            i = 0 if self.orientation == 'horizontal' else 1
            if abs(touch.pos[i] - self.value_pos_slider[0][i]) < abs(
                            touch.pos[i] - self.value_pos_slider[1][i]):
                self.value_pos_slider = [touch.pos, self.value_pos_slider[1]]
            else:
                self.value_pos_slider = [self.value_pos_slider[0], touch.pos]
        return True

    def on_touch_move(self, touch):
        if touch.grab_current == self:
            i = 0 if self.orientation == 'horizontal' else 1
            if abs(touch.pos[i] - self.value_pos_slider[0][i]) < abs(
                            touch.pos[i] - self.value_pos_slider[1][i]):
                self.value_pos_slider = [touch.pos, self.value_pos_slider[1]]
            else:
                self.value_pos_slider = [self.value_pos_slider[0], touch.pos]
            return True

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            i = 0 if self.orientation == 'horizontal' else 1
            if abs(touch.pos[i] - self.value_pos_slider[0][i]) < abs(
                            touch.pos[i] - self.value_pos_slider[1][i]):
                self.value_pos_slider = [touch.pos, self.value_pos_slider[1]]
            else:
                self.value_pos_slider = [self.value_pos_slider[0], touch.pos]
            return True


if __name__ == '__main__':
    from kivy.app import App

    class RangeSliderApp(App):
        def build(self):
            return RangeSlider(padding=25, value_track=True,
                value_track_color=[1, 0, 0, 1], value_range=[25, 75])
    RangeSliderApp().run()
