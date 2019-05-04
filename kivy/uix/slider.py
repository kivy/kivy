"""
Slider
======

.. image:: images/slider.jpg

The :class:`Slider` widget looks like a scrollbar. It supports horizontal and
vertical orientations, min/max values and a default value.

To create a slider from -100 to 100 starting from 25::

    from kivy.uix.slider import Slider
    s = Slider(min=-100, max=100, value=25)

To create a vertical slider::

    from kivy.uix.slider import Slider
    s = Slider(orientation='vertical')

To create a slider with a red line tracking the value::

    from kivy.uix.slider import Slider
    s = Slider(value_track=True, value_track_color=[1, 0, 0, 1])


Kv Example::

    BoxLayout:
        Slider:
            id: slider
            min: 0
            max: 100
            step: 1
            orientation: 'vertical'

        Label:
            text: str(slider.value)

"""
__all__ = ('Slider', )

from kivy.uix.widget import Widget
from kivy.properties import (NumericProperty, AliasProperty, OptionProperty,
                             ReferenceListProperty, BoundedNumericProperty,
                             StringProperty, ListProperty, BooleanProperty)


class Slider(Widget):
    """Class for creating a Slider widget.

    Check module documentation for more details.
    """

    value = NumericProperty(0.)
    '''Current value used for the slider.

    :attr:`value` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0.'''

    min = NumericProperty(0.)
    '''Minimum value allowed for :attr:`value`.

    :attr:`min` is a :class:`~kivy.properties.NumericProperty` and defaults to
    0.'''

    max = NumericProperty(100.)
    '''Maximum value allowed for :attr:`value`.

    :attr:`max` is a :class:`~kivy.properties.NumericProperty` and defaults to
    100.'''

    padding = NumericProperty('16sp')
    '''Padding of the slider. The padding is used for graphical representation
    and interaction. It prevents the cursor from going out of the bounds of the
    slider bounding box.

    By default, padding is 16sp. The range of the slider is reduced from
    padding \*2 on the screen. It allows drawing the default cursor of 32sp
    width without having the cursor go out of the widget.

    :attr:`padding` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 16sp.'''

    orientation = OptionProperty('horizontal', options=(
        'vertical', 'horizontal'))
    '''Orientation of the slider.

    :attr:`orientation` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'horizontal'. Can take a value of 'vertical' or 'horizontal'.
    '''

    range = ReferenceListProperty(min, max)
    '''Range of the slider in the format (minimum value, maximum value)::

        >>> slider = Slider(min=10, max=80)
        >>> slider.range
        [10, 80]
        >>> slider.range = (20, 100)
        >>> slider.min
        20
        >>> slider.max
        100

    :attr:`range` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`min`, :attr:`max`) properties.
    '''

    step = BoundedNumericProperty(0, min=0)
    '''Step size of the slider.

    .. versionadded:: 1.4.0

    Determines the size of each interval or step the slider takes between
    min and max. If the value range can't be evenly divisible by step the
    last step will be capped by slider.max

    :attr:`step` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 1.'''

    background_horizontal = StringProperty(
        'atlas://data/images/defaulttheme/sliderh_background')
    """Background of the slider used in the horizontal orientation.

    .. versionadded:: 1.10.0

    :attr:`background_horizontal` is a :class:`~kivy.properties.StringProperty`
    and defaults to `atlas://data/images/defaulttheme/sliderh_background`.
    """

    background_disabled_horizontal = StringProperty(
        'atlas://data/images/defaulttheme/sliderh_background_disabled')
    """Background of the disabled slider used in the horizontal orientation.

    .. versionadded:: 1.10.0

    :attr:`background_disabled_horizontal` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    `atlas://data/images/defaulttheme/sliderh_background_disabled`.
    """

    background_vertical = StringProperty(
        'atlas://data/images/defaulttheme/sliderv_background')
    """Background of the slider used in the vertical orientation.

    .. versionadded:: 1.10.0

    :attr:`background_vertical` is a :class:`~kivy.properties.StringProperty`
    and defaults to `atlas://data/images/defaulttheme/sliderv_background`.
    """

    background_disabled_vertical = StringProperty(
        'atlas://data/images/defaulttheme/sliderv_background_disabled')
    """Background of the disabled slider used in the vertical orientation.

    .. versionadded:: 1.10.0

    :attr:`background_disabled_vertical` is a
    :class:`~kivy.properties.StringProperty` and defaults to
    `atlas://data/images/defaulttheme/sliderv_background_disabled`.
    """

    background_width = NumericProperty('36sp')
    """Slider's background's width (thickness), used in both horizontal
    and vertical orientations.

    .. versionadded 1.10.0

    :attr:`background_width` is a
    :class:`~kivy.properties.NumericProperty` and defaults to 36sp.
    """

    cursor_image = StringProperty(
        'atlas://data/images/defaulttheme/slider_cursor')
    """Path of the image used to draw the slider cursor.

    .. versionadded 1.10.0

    :attr:`cursor_image` is a :class:`~kivy.properties.StringProperty`
    and defaults to `atlas://data/images/defaulttheme/slider_cursor`.
    """

    cursor_disabled_image = StringProperty(
        'atlas://data/images/defaulttheme/slider_cursor_disabled')
    """Path of the image used to draw the disabled slider cursor.

    .. versionadded 1.10.0

    :attr:`cursor_image` is a :class:`~kivy.properties.StringProperty`
    and defaults to `atlas://data/images/defaulttheme/slider_cursor_disabled`.
    """

    cursor_width = NumericProperty('32sp')
    """Width of the cursor image.

    .. versionadded 1.10.0

    :attr:`cursor_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 32sp.
    """

    cursor_height = NumericProperty('32sp')
    """Height of the cursor image.

    .. versionadded 1.10.0

    :attr:`cursor_height` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 32sp.
    """

    cursor_size = ReferenceListProperty(cursor_width, cursor_height)
    """Size of the cursor image.

    .. versionadded 1.10.0

    :attr:`cursor_size` is a :class:`~kivy.properties.ReferenceListProperty`
    of (:attr:`cursor_width`, :attr:`cursor_height`) properties.
    """

    border_horizontal = ListProperty([0, 18, 0, 18])
    """Border used to draw the slider background in horizontal orientation.

    .. versionadded 1.10.0

    :attr:`border_horizontal` is a :class:`~kivy.properties.ListProperty`
    and defaults to [0, 18, 0, 18].
    """

    border_vertical = ListProperty([18, 0, 18, 0])
    """Border used to draw the slider background in vertical orientation.

    .. versionadded 1.10.0

    :attr:`border_horizontal` is a :class:`~kivy.properties.ListProperty`
    and defaults to [18, 0, 18, 0].
    """

    value_track = BooleanProperty(False)
    """Decides if slider should draw the line indicating the
    space between :attr:`min` and :attr:`value` properties values.

    .. versionadded 1.10.0

    :attr:`value_track` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.
    """

    value_track_color = ListProperty([1, 1, 1, 1])
    """Color of the :attr:`value_line` in rgba format.

    .. versionadded 1.10.0

    :attr:`value_track_color` is a :class:`~kivy.properties.ListProperty`
    and defaults to [1, 1, 1, 1].
    """

    value_track_width = NumericProperty('3dp')
    """Width of the track line.

    .. versionadded 1.10.0

    :attr:`value_track_width` is a :class:`~kivy.properties.NumericProperty`
    and defaults to 3dp.
    """

    sensitivity = OptionProperty('all', options=('all', 'handle'))
    """Whether the touch collides with the whole body of the widget
    or with the slider handle part only.

    .. versionadded:: 1.10.1

    :attr:`sensitivity` is a :class:`~kivy.properties.OptionProperty`
    and defaults to 'all'. Can take a value of 'all' or 'handle'.
    """

    # The following two methods constrain the slider's value
    # to range(min,max). Otherwise it may happen that self.value < self.min
    # at init.

    def on_min(self, *largs):
        self.value = min(self.max, max(self.min, self.value))

    def on_max(self, *largs):
        self.value = min(self.max, max(self.min, self.value))

    def get_norm_value(self):
        vmin = self.min
        d = self.max - vmin
        if d == 0:
            return 0
        return (self.value - vmin) / float(d)

    def set_norm_value(self, value):
        vmin = self.min
        vmax = self.max
        step = self.step
        val = min(value * (vmax - vmin) + vmin, vmax)
        if step == 0:
            self.value = val
        else:
            self.value = min(round((val - vmin) / step) * step + vmin,
                             vmax)

    value_normalized = AliasProperty(get_norm_value, set_norm_value,
                                     bind=('value', 'min', 'max'),
                                     cache=True)
    '''Normalized value inside the :attr:`range` (min/max) to 0-1 range::

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

    :attr:`value_normalized` is an :class:`~kivy.properties.AliasProperty`.
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
                              bind=('pos', 'size', 'min', 'max', 'padding',
                                    'value_normalized', 'orientation'),
                              cache=True)
    '''Position of the internal cursor, based on the normalized value.

    :attr:`value_pos` is an :class:`~kivy.properties.AliasProperty`.
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
        elif self.sensitivity == 'handle':
            if self.children[0].collide_point(*touch.pos):
                touch.grab(self)
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
