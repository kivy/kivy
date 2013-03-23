'''
Slider
======

.. image:: images/slider.jpg

The :class:`Slider` widget looks like a scrollbar. It supports horizontal and
vertical orientation, min/max and a default value.

To create a slider from -100 to 100 starting at 25::

    from kivy.uix.slider import Slider
    s = Slider(min=-100, max=100, value=25)

To create a slider from 0 to 100, with major ticks at every 25 units and
minor ticks dividing the 25 units into sub-intervals of 5::

    from kivy.uix.slider import Slider
    s = Slider(min=0, max=100, ticks_major=25, ticks_minor=5)

To create a vertical slider::

    from kivy.uix.slider import Slider
    s = Slider(orientation='vertical')

'''
__all__ = ('Slider', )

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, AliasProperty, OptionProperty, \
        ReferenceListProperty, BoundedNumericProperty, ObjectProperty
from kivy.graphics import Mesh
from math import floor


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

    ticks_major = BoundedNumericProperty(0, min=0)
    '''Distance between major tick marks.

    .. versionadded:: 1.6.1

    Determines the distance between the major tick marks. Major tick marks
    start from slider.min and re-occur at every ticks_major until slider.max.
    If slider.max doesn't overlap with a integer multiple of ticks_major,
    no tick will occur at slider.max. Zero indicates no tick marks.

    :data:`ticks_major` is a :class:`~kivy.properties.BoundedNumericProperty`,
    default to 0.
    '''

    ticks_minor = BoundedNumericProperty(0, min=0)
    '''The number of sub-intervals that divide ticks_major.

    .. versionadded:: 1.6.1

    Determines the number of sub-intervals into which ticks_major is divided,
    if non-zero. The actual number of minor ticks between the major ticks is
    ticks_minor - 1. Only used if ticks_major is non-zero. If there's no major
    tick at slider.max then the number of minor ticks after the last major
    tick will be however many ticks fit until slider.max.

    :data:`ticks_minor` is a :class:`~kivy.properties.BoundedNumericProperty`,
    default to 0.
    '''

    # Internals properties used for graphical representation.

    _mesh = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Slider, self).__init__(**kwargs)
        with self.canvas:
            self._mesh = Mesh(mode='lines')
        self.bind(center=self.set_ticks, ticks_major=self.set_ticks,
                  ticks_minor=self.set_ticks, padding=self.set_ticks,
                  range=self.set_ticks, orientation=self.set_ticks)

    def set_ticks(self, *args):
        mesh = self._mesh
        indices = mesh.indices
        vertices = mesh.vertices
        if self.ticks_major:
            ticks_minor = self.ticks_minor
            ticks_major = self.ticks_major
            padding = self.padding
            # distance between each tick
            tick_dist = ticks_major / float(ticks_minor if ticks_minor else 1.0)
            n_ticks = int(floor((self.max - self.min) / tick_dist) + 1)
            count = len(indices) / 2
            # adjust mesh size
            if count > n_ticks:
                del vertices[n_ticks * 8:]
                del indices[n_ticks * 2:]
            elif count < n_ticks:
                vertices.extend([0] * (8 * (n_ticks - count)))
                indices.extend(xrange(2 * count, 2 * n_ticks))

            if self.orientation == 'horizontal':
                center = self.center_y
            else:
                center = self.center_x
            maj_plus = center + 12
            maj_minus = center - 12
            min_plus = center + 6
            min_minus = center - 6
            if self.orientation == 'horizontal':
                # now, the distance between ticks in pixels
                tick_dist = (self.width - 2 * padding
                             ) / float(self.max - self.min) * tick_dist
                start = self.x + padding
                for k in xrange(0, n_ticks):
                    m = k * 8
                    vertices[m + 0] = start + k * tick_dist
                    vertices[m + 4] = vertices[m + 0]
                    if ticks_minor and k % ticks_minor:
                        vertices[m + 1] = min_plus
                        vertices[m + 5] = min_minus
                    else:
                        vertices[m + 1] = maj_plus
                        vertices[m + 5] = maj_minus
            else:
                tick_dist = (self.height - 2 * padding
                             ) / float(self.max - self.min) * tick_dist
                start = self.y + padding
                for k in xrange(0, n_ticks):
                    m = k * 8
                    vertices[m + 1] = start + k * tick_dist
                    vertices[m + 5] = vertices[m + 1]
                    if ticks_minor and k % ticks_minor:
                        vertices[m + 0] = min_plus
                        vertices[m + 4] = min_minus
                    else:
                        vertices[m + 0] = maj_plus
                        vertices[m + 4] = maj_minus
        else:
            if not len(indices):
                return
            del indices[:]
            del vertices[:]
        mesh.vertices = vertices
        mesh.indices = indices

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
        >>> slider.value = 1
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
        if self.collide_point(*touch.pos):
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
            return Slider(padding=25, ticks_major=25, ticks_minor=5)

    SliderApp().run()
