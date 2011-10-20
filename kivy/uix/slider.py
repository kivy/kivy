'''
Slider
======

.. image:: images/slider.jpg

The :class:`Slider` widget looks like a scrollbar. It supports horizontal and
vertical orientation, min/max and a default value.

To create a slider from -100 to 100 starting at 25 ::

    from kivy.uix.slider import Slider
    s = Slider(min=-100, max=100, value=25)

To create a vertical slider ::

    from kivy.uix.slider import Slider
    s = Slider(orientation='vertical')

'''
__all__ = ('Slider', )

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, AliasProperty, OptionProperty, \
        ReferenceListProperty


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
    and interaction. It prevent the cursor to go out of the bounds of the slider
    bounding box.

    By default, padding is 10. The range of the slider is reduced from padding *
    2 on the screen. It allow to draw a cursor of 20px width, without having the
    cursor going out of the widget.

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
    '''Range of the slider, in the format (minimum value, maximum value). ::

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

    def get_norm_value(self):
        vmin = self.min
        d = self.max - vmin
        if d == 0:
            return 0
        return (self.value - vmin) / float(d)

    def set_norm_value(self, value):
        vmin = self.min
        self.value = value * (self.max - vmin) + vmin
    value_normalized = AliasProperty(get_norm_value, set_norm_value,
                                     bind=('value', 'min', 'max'))
    '''Normalized value inside the :data:`range` (min/max) to 0-1 range. ::

        >>> slider = Slider(value=50, min=0, max=100)
        >>> slider.value
        50
        >>> slider.value_normalized
        0.5
        >>> slider.value = 0
        >>> slider.value_normalized
        0
        >>> slider.value = 1
        >>> slider.value_normalized
        1

    You can also use it for setting the real value without knowing the minimum
    and maximum. ::

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
        x = min(self.right, max(pos[0], self.x))
        y = min(self.top, max(pos[1], self.y))
        if self.orientation == 'horizontal':
            if self.width == 0:
                self.value_normalized = 0
            else:
                self.value_normalized = (x - self.x) / float(self.width)
        else:
            if self.height == 0:
                self.value_normalized = 0
            else:
                self.value_normalized = (y - self.y) / float(self.height)
    value_pos = AliasProperty(get_value_pos, set_value_pos,
                              bind=('x', 'y', 'width', 'height', 'min',
                                    'max', 'value_normalized', 'orientation'))
    '''Position of the internal cursor, based on the normalized value.

    :data:`value_pos` is an :class:`~kivy.properties.AliasProperty`.
    '''

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
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

