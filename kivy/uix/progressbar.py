'''
Progress Bar
============

.. versionadded:: 1.0.8

.. image:: images/progressbar.jpg
    :align: right

The :class:`ProgressBar` widget is used to visualize progression. Only
horizontal mode is supported, vertical mode is not available yet.

The progress bar cannot be interacted with, it's a display-only widget.

To use it, simply assign a value to indicate the current progress ::

    from kivy.uix.progressbar import ProgressBar
    pb = ProgressBar(max=1000)

    # this will update the graphics automatically (75% done):
    pb.value = 750

'''

__all__ = ('ProgressBar', )

from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, AliasProperty


class ProgressBar(Widget):
    '''Class for creating a Progress bar widget.

    Check module documentation for more details.
    '''

    value = NumericProperty(0.)
    '''Current value used for the slider.

    :data:`value` is a :class:`~kivy.properties.NumericProperty`, default to 0.
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
    '''Normalized value inside the 0-max to 0-1 range::

        >>> pb = ProgressBar(value=50, max=100)
        >>> pb.value
        50
        >>> slider.value_normalized
        0.5

    :data:`value_normalized` is an :class:`~kivy.properties.AliasProperty`.
    '''

    max = NumericProperty(100.)
    '''Maximum value allowed for :data:`value`.

    :data:`max` is a :class:`~kivy.properties.NumericProperty`, default to 100.
    '''


if __name__ == '__main__':

    from kivy.base import runTouchApp
    runTouchApp(ProgressBar(value=50))
