'''
Layout
======

Layouts is a way to calculate and assign position of widgets.
The :class:`Layout` class itself cannot be used directly. You must use one of:

- Anchor layout : :class:`kivy.uix.anchorlayout.AnchorLayout`
- Box layout : :class:`kivy.uix.boxlayout.BoxLayout`
- Grid layout : :class:`kivy.uix.gridlayout.GridLayout`
- Screen layout : :class:`kivy.uix.screenlayout.ScreenLayout`

Understanding `size_hint` property in `Widget`
----------------------------------------------

The :data:`~kivy.uix.Widget.size_hint` is mostly used in Layout. This is the
size, in percent, not in pixels. The format is: ::

    widget.size_hint = (width_percent, height_percent)

The percent is between the range 0-1: 1 mean 100%.

So, if you want a widget width to be only the half of the parent, and his height
to be the same as his parent, you can do: ::

    widget.size_hint = (0.5, 1.0)

If you don't want to use size_hint for one of width or height, set his value to
None. For example, if you want a widget width to be 250px, and his height to 30%
of his parent, you can write: ::

    widget.size_hint = (None, 0.3)
    widget.width = 250

'''

__all__ = ('Layout', )

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import AliasProperty


class Layout(Widget):
    '''Layout interface class, used to implement every layout. Check module
    documentation for more information.
    '''

    def __init__(self, **kwargs):
        if self.__class__ == Layout:
            raise Exception('The Layout class cannot be used.')
        kwargs.setdefault('size', (1, 1))
        self._minimum_size = (0, 0)
        self._trigger_minimum_size = Clock.create_trigger(
            self.update_minimum_size, -1)
        self.bind(children=self._trigger_minimum_size)
        super(Layout, self).__init__(**kwargs)

    def _get_minimum_size(self):
        return self._minimum_size

    def _set_minimum_size(self, size):
        self._minimum_size = size
        if self.width < size[0]:
            self.width = size[0]
        if self.height < size[1]:
            self.height = size[1]
    minimum_size = AliasProperty(_get_minimum_size, _set_minimum_size)
    '''Minimum size required by the layout. This property is used by
    :class:`Layout` to perfom his layout calculations. If the widgets size
    (width or height) is smaller than the minimum size, it will be resized to be
    at least minimum size.

    :data:`minimum_size` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def reposition_child(self, child, **kwargs):
        '''Force the child to be repositioned on the screen. This method is used
        internally in boxlayout.
        '''
        for prop in kwargs:
            child.__setattr__(prop, kwargs[prop])

    def update_minimum_size(self, instance, *largs):
        self.minimum_size = self.size

    def add_widget(self, widget, index=0):
        widget.bind(
                size = self._trigger_minimum_size,
                size_hint = self._trigger_minimum_size)
        return super(Layout, self).add_widget(widget, index)

    def remove_widget(self, widget):
        widget.unbind(
                size = self._trigger_minimum_size,
                size_hint = self._trigger_minimum_size)
        return super(Layout, self).remove_widget(widget)

