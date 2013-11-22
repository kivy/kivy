'''
Progress Bar
============

.. versionadded:: 1.0.8

.. image:: images/progressbar.jpg
    :align: right

The :class:`ProgressBar` widget is used to visualize the progress of some task.
Only the horizontal mode is currently supported: the vertical mode is not
yet available.

The progress bar has no interactive elements and is a display-only widget.

To use it, simply assign a value to indicate the current progress::

    from kivy.uix.progressbar import ProgressBar
    pb = ProgressBar(max=1000)

    # this will update the graphics automatically (75% done)
    pb.value = 750

'''

__all__ = ('ProgressBar', )

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, AliasProperty


class ProgressBar(Widget):
    '''Class for creating a Progress bar widget.

    See module documentation for more details.
    '''

    def __init__(self, **kwargs):
        self._value = 0.
        super(ProgressBar, self).__init__(**kwargs)

    def _get_value(self):
        return self._value

    def _set_value(self, value):
        value = max(0, min(self.max, value))
        if value != self._value:
            self._value = value
            return True

    value = AliasProperty(_get_value, _set_value)
    '''Current value used for the slider.

    :data:`value` is an :class:`~kivy.properties.AliasProperty` than returns the
    value of the progressbar. If the value is < 0 or > :data:`max`, it will be
    normalized to thoses boundaries.

    .. versionchanged:: 1.6.0
        The value is now limited to between 0 and :data:`max`.
    '''

    def get_norm_value(self):
        d = self.max
        if d == 0:
            return 0
        return self.value / float(d)

    def set_norm_value(self, value):
        self.value = value * self.max

    value_normalized = AliasProperty(get_norm_value, set_norm_value,
                                     bind=('value', 'max'))
    '''Normalized value inside the range 0-1::

        >>> pb = ProgressBar(value=50, max=100)
        >>> pb.value
        50
        >>> slider.value_normalized
        0.5

    :data:`value_normalized` is an :class:`~kivy.properties.AliasProperty`.
    '''

    max = NumericProperty(100.)
    '''Maximum value allowed for :data:`value`.

    :data:`max` is a :class:`~kivy.properties.NumericProperty` and defaults to
    100.
    '''


if __name__ == '__main__':

    from kivy.base import runTouchApp
    runTouchApp(ProgressBar(value=50))
