'''
Slider
======

.. image:: images/slider.jpg

The :class:`Slider` widget looks like a scrollbar. It supports horizontal and
vertical orientation, min/max and a default value.

To create a slider from -100 to 100 starting at 25::

    from kivy.uix.slider import Slider
    s = Slider(min=-100, max=100, value=25)

To create a vertical slider::

    from kivy.uix.slider import Slider
    s = Slider(orientation='vertical')

'''
__all__ = ('Slider', )

from kivy.uix.widget import Widget
from kivy.properties import (NumericProperty, AliasProperty, OptionProperty,
        ReferenceListProperty, BoundedNumericProperty, BooleanProperty)


class Slider(Widget):
    '''Class for creating Slider widget.

    Check module documentation for more details.
    '''

    value = NumericProperty(0.)
    '''Current value used for the slider.

    :data:`value` is a :class:`~kivy.properties.NumericProperty`, default to 0.
    '''

    min = NumericProperty(0.)
    '''Minimum value allowed for :data:`value`.

    :data:`min` is a :class:`~kivy.properties.NumericProperty`, default to 0.
    '''

    max = NumericProperty(100.)
    '''Maximum value allowed for :data:`value`.

    :data:`max` is a :class:`~kivy.properties.NumericProperty`, default to 100.
    '''

    padding = NumericProperty(10)
    '''Padding of the slider. The padding is used for graphical representation
    and interaction. It prevents the cursor from going out of the bounds of the
    slider bounding box.

    By default, padding is 10. The range of the slider is reduced from padding *
    2 on the screen. It allows drawing a cursor of 20px width, without having
    the cursor going out of the widget.

    :data:`padding` is a :class:`~kivy.properties.NumericProperty`, default to
    10.
    '''

    orientation = OptionProperty('horizontal', options=(
        'vertical', 'horizontal'))
    '''Orientation of the slider.

    :data:`orientation` is an :class:`~kivy.properties.OptionProperty`, default
    to 'horizontal'. Can take a value of 'vertical' or 'horizontal'.
    '''

    range = ReferenceListProperty(min, max)
    '''Range of the slider, in the format (minimum value, maximum value)::

        >>> slider = Slider(min=10, max=80)
        >>> slider.range
        [10, 80]
        >>> slider.range = (20, 100)
        >>> slider.min
        20
        >>> slider.max
        100

    :data:`range` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:data:`min`, :data:`max`)
    '''

    step = BoundedNumericProperty(0, min=0)
    '''Step size of the slider.

    .. versionadded:: 1.4.0

    Determines the size of each interval or step the slider takes between
    min and max. If the value range can't be evenly divisible by step the
    last step will be capped by slider.max

    :data:`step` is a :class:`~kivy.properties.NumericProperty`, default to 1.
    '''

    def get_norm_value(self):
        vmin = self.min
        d = self.max - vmin
        if d == 0:
            return 0
        return (self.value - vmin) / float(d)

    def set_norm_value(self, value):
        vmin = self.min
        step = self.step
        val = value * (self.max - vmin) + vmin
        if step == 0:
            self.value = val
        else:
            self.value = min(round((val - vmin) / step) * step + vmin, self.max)
    value_normalized = AliasProperty(get_norm_value, set_norm_value,
                                     bind=('value', 'min', 'max', 'step'))
    '''Normalized value inside the :data:`range` (min/max) to 0-1 range::

        >>> slider = Slider(value=50, min=0, max=100)
        >>> slider.value
        50
        >>> slider.value_normalized
        0.5
        >>> slider.value = 0
        >>> slider.value_normalized
        0
        >>> slider.value = 100
        >>> slider.value_normalized
        1

    You can also use it for setting the real value without knowing the minimum
    and maximum::

        >>> slider = Slider(min=0, max=200)
        >>> slider.value_normalized = .5
        >>> slider.value
        100
        >>> slider.value_normalized = 1.
        >>> slider.value
        200

    :data:`value_normalized` is an :class:`~kivy.properties.AliasProperty`.
    '''

    def get_value_pos(self):
        padding = self.padding
        x = self.x
        y = self.y
        nval = self.value_normalized
        if self.orientation == 'horizontal':
            return (x + padding + nval * (self.width - 2 * padding), y)
        else:
            return (x, y + padding + nval * (self.height - 2 * padding))

    def set_value_pos(self, pos):
        padding = self.padding
        x = min(self.right - padding, max(pos[0], self.x + padding))
        y = min(self.top - padding, max(pos[1], self.y + padding))
        if self.orientation == 'horizontal':
            if self.width == 0:
                self.value_normalized = 0
            else:
                self.value_normalized = (x - self.x - padding
                                         ) / float(self.width - 2 * padding)
        else:
            if self.height == 0:
                self.value_normalized = 0
            else:
                self.value_normalized = (y - self.y - padding
                                         ) / float(self.height - 2 * padding)
    value_pos = AliasProperty(get_value_pos, set_value_pos,
                              bind=('x', 'y', 'width', 'height', 'min',
                                    'max', 'value_normalized', 'orientation'))
    '''Position of the internal cursor, based on the normalized value.

    :data:`value_pos` is an :class:`~kivy.properties.AliasProperty`.
    '''

    def on_touch_down(self, touch):
        if self.disabled or not self.collide_point(*touch.pos):
            return
        if touch.is_mouse_scrolling:
            if 'down' in touch.button or 'left' in touch.button:
                if self.step:
                    self.value = min(self.max, self.value + self.step)
                else:
                    self.value = min(
                        self.max,
                        self.value + (self.max - self.min) / 20)
            if 'up' in touch.button or 'right' in touch.button:
                if self.step:
                    self.value = max(self.min, self.value - self.step)
                else:
                    self.value = max(
                        self.min,
                        self.value - (self.max - self.min) / 20)
        else:
            touch.grab(self)
            self.value_pos = touch.pos
        return True

    def on_touch_move(self, touch):
        if touch.grab_current == self:
            self.value_pos = touch.pos
            return True

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            self.value_pos = touch.pos
            return True

if __name__ == '__main__':
    from kivy.app import App

    class SliderApp(App):
        def build(self):
            return Slider(padding=25)

    SliderApp().run()
