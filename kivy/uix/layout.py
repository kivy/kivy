'''
Layout
======

Layouts are used to calculate and assign widget positions.

The :class:`Layout` class itself cannot be used directly. You must use one of:

- Anchor layout : :class:`kivy.uix.anchorlayout.AnchorLayout`
- Box layout : :class:`kivy.uix.boxlayout.BoxLayout`
- Float layout : :class:`kivy.uix.floatlayout.FloatLayout`
- Grid layout : :class:`kivy.uix.gridlayout.GridLayout`
- Stack layout : :class:`kivy.uix.stacklayout.StackLayout`

Understanding `size_hint` property in `Widget`
----------------------------------------------

The :data:`~kivy.uix.Widget.size_hint` is mostly used in Layout. This is the
size in percent, not in pixels. The format is::

    widget.size_hint = (width_percent, height_percent)

The percent is specified as a floating point number in the range 0-1, ie 0.5
is 50%, 1 is 100%.

If you want a widget's width to be half of the parent's and their heights to
be identical, you can do::

    widget.size_hint = (0.5, 1.0)

If you don't want to use size_hint for one of width or height, set the value to
None. For example, to make a widget that is 250px wide and 30% of the parent's
height, you can write::

    widget.size_hint = (None, 0.3)
    widget.width = 250

'''

__all__ = ('Layout', )

from kivy.clock import Clock
from kivy.uix.widget import Widget


class Layout(Widget):
    '''Layout interface class, used to implement every layout. Check module
    documentation for more information.
    '''

    def __init__(self, **kwargs):
        if self.__class__ == Layout:
            raise Exception('The Layout class cannot be used.')
        self._trigger_layout = Clock.create_trigger(self.do_layout, -1)
        super(Layout, self).__init__(**kwargs)

    def reposition_child(self, child, **kwargs):
        '''Force the child to be repositioned on the screen. This method is used
        internally in boxlayout.
        '''
        for prop in kwargs:
            child.__setattr__(prop, kwargs[prop])

    def do_layout(self, *largs):
        '''This function is called when a layout is needed, with by a trigger.
        If you are doing a new Layout subclass, don't call this function
        directly, use :data:`_trigger_layout` instead.

        .. versionadded:: 1.0.8
        '''
        pass

    def add_widget(self, widget, index=0):
        widget.bind(
            size = self._trigger_layout,
            size_hint = self._trigger_layout)
        return super(Layout, self).add_widget(widget, index)

    def remove_widget(self, widget):
        widget.unbind(
            size = self._trigger_layout,
            size_hint = self._trigger_layout)
        return super(Layout, self).remove_widget(widget)

