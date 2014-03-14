'''
Layout
======

Layouts are used to calculate and assign widget positions.

The :class:`Layout` class itself cannot be used directly. You should use one of
the concrete layout classes:

- Anchor layout : :class:`kivy.uix.anchorlayout.AnchorLayout`
- Box layout : :class:`kivy.uix.boxlayout.BoxLayout`
- Float layout : :class:`kivy.uix.floatlayout.FloatLayout`
- Grid layout : :class:`kivy.uix.gridlayout.GridLayout`
- Stack layout : :class:`kivy.uix.stacklayout.StackLayout`

Understanding the `size_hint` Property in `Widget`
--------------------------------------------------

The :attr:`~kivy.uix.Widget.size_hint` is a tuple of values used by
layouts to manage the sizes of their children. It indicates the size
relative to the layout's size instead of an absolute size (in
pixels/points/cm/etc). The format is::

    widget.size_hint = (width_percent, height_percent)

The percent is specified as a floating point number in the range 0-1. For
example, 0.5 is 50%, 1 is 100%.

If you want a widget's width to be half of the parent's width and the
height to be identical to the parent's height, you would do::

    widget.size_hint = (0.5, 1.0)

If you don't want to use a size_hint for either the width or height, set the
value to
None. For example, to make a widget that is 250px wide and 30% of the parent's
height, do::

    widget.size_hint = (None, 0.3)
    widget.width = 250

.. versionchanged:: 1.4.1
    The `reposition_child` internal method (made public by mistake) has
    been removed.

'''

__all__ = ('Layout', )

from kivy.clock import Clock
from kivy.uix.widget import Widget


class Layout(Widget):
    '''Layout interface class, used to implement every layout. See module
    documentation for more information.
    '''

    def __init__(self, **kwargs):
        if self.__class__ == Layout:
            raise Exception('The Layout class cannot be used.')
        self._trigger_layout = Clock.create_trigger(self.do_layout, -1)
        super(Layout, self).__init__(**kwargs)

    def do_layout(self, *largs):
        '''This function is called when a layout is needed by a trigger.
        If you are writing a new Layout subclass, don't call this function
        directly but use :meth:`_trigger_layout` instead.

        .. versionadded:: 1.0.8
        '''
        pass

    def add_widget(self, widget, index=0):
        widget.bind(
            size=self._trigger_layout,
            size_hint=self._trigger_layout)
        return super(Layout, self).add_widget(widget, index)

    def remove_widget(self, widget):
        widget.unbind(
            size=self._trigger_layout,
            size_hint=self._trigger_layout)
        return super(Layout, self).remove_widget(widget)
