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

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, AliasProperty


class ProgressBar(Widget):
    '''Class for creating a progress bar widget.

    See module documentation for more details.
    '''

    def __init__(self, **kwargs):
        self._value = 0.
        self._relsize = 0.2
        self._period = 2.0
        super(ProgressBar, self).__init__(**kwargs)

    def _get_value(self):
        return self._value

    def _set_value(self, value):
        if value is None:
            self._value = value
            Clock.schedule_once(self._increment_time)
            return True
        value = max(0, min(self.max, value))
        if value != self._value:
            self._value = value
            return True

    value = AliasProperty(_get_value, _set_value)
    '''Current value used for the slider.

    :attr:`value` is an :class:`~kivy.properties.AliasProperty` that
    returns the value of the progress bar. If the value is < 0 or >
    :attr:`max`, it will be normalized to those boundaries.

    .. versionchanged:: 1.6.0
        The value is now limited to between 0 and :attr:`max`.
        
    .. versionchanged:: 2.0.0
        The value can now be None. Such value will set the :class:`ProgressBar`
        to indeterminate mode.
    '''
    
    _time = NumericProperty(0.)
    
    def _increment_time(self, dt):
        if self.value is None:
           self._time += Clock.frametime
           Clock.schedule_once(self._increment_time)
        else:
           self._time = 0
           

    def get_norm_value(self):
        if self.value is None:
            return self.value
        d = self.max
        if d == 0:
            return 0
        return self.value / float(d)

    def set_norm_value(self, value):
        if value is None:
            self.value = value
        self.value = value * self.max

    value_normalized = AliasProperty(get_norm_value, set_norm_value,
                                     bind=('value', 'max'))
    '''Normalized value inside the range 0-1::

        >>> pb = ProgressBar(value=50, max=100)
        >>> pb.value
        50
        >>> slider.value_normalized
        0.5

    :attr:`value_normalized` is an :class:`~kivy.properties.AliasProperty`.
    
    .. versionchanged:: 2.0.0
    The normalized value can now be None. Such value will set the
    :class:`ProgressBar` to indeterminate mode.
    '''

    max = NumericProperty(100.)
    '''Maximum value allowed for :attr:`value`.

    :attr:`max` is a :class:`~kivy.properties.NumericProperty` and defaults to
    100.
    '''


if __name__ == '__main__':
    from kivy.uix.boxlayout import BoxLayout
    from kivy.base import runTouchApp
    bl = BoxLayout(orientation='vertical')
    bl.add_widget(ProgressBar(value=50))
    bl.add_widget(ProgressBar(value=None))
    runTouchApp(bl)
