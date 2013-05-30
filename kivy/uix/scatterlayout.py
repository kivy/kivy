'''
Scatter Layout
===============

.. versionadded:: 1.6.0


This layout allows you to set relative coordinates for children. If you want
absolute positioning, check :class:`~kivy.uix.floatlayout.FloatLayout`.

The :class:`ScatterLayout` class behaves just like the regular Float
Layout, except that its child widgets are positioned relative to the layout.

For example, if you create a :class:`ScatterLayout`, add a widget with
position = (0,0), the child widget will also move, when you change the
position of the :class:`ScatterLayout`.  The child widget's coordinates remain
(0,0), i.e. they are relative to the containing layout. Since
:class:`ScatterLayout` is implemented using a :class:`Scatter` widget, you can
also translate and scale the layout like a normal :class:`Scatter` widget,
and the child widgets will behave as expected.

..note::

    The :class:`ScatterLayout` is implemented as a :class`FloatLayout`
    inside a :class:`Scatter`.

.. warning::

    Since the actual :class:`ScatterLayout` is a :class:`Scatter`, its
    add_widget and remove_widget functions are overwritten to add children
    to the embedded :class:`FloatLayout` (accessible as `content` property of
    :class:`Scatter`) automatically. So if you want to access the added
    child elements, you need self.content.children, instead of self.children.

.. warning::

    The :class:`ScatterLayout` was introduced in 1.7.0 and was called
    :class:`~kivy.uix.relativelayout.RelativeLayout` in prior versions.
    :class:`~kivy.uix.relativelayout.RelativeLayout` is now an optimized
    implementation that uses only a positional transform, to avoid some of the
    heavier calculation involved for :class:`Scatter`.

'''

__all__ = ('ScatterLayout', )

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.properties import ObjectProperty


class ScatterLayout(Scatter):
    '''RelativeLayout class, see module documentation for more information.
    '''

    content = ObjectProperty()

    def __init__(self, **kw):
        self.content = FloatLayout()
        super(ScatterLayout, self).__init__(**kw)
        if self.content.size != self.size:
            self.content.size = self.size
        super(ScatterLayout, self).add_widget(self.content)
        self.bind(size=self.update_size)

    def update_size(self, instance, size):
        self.content.size = size

    def add_widget(self, *l):
        self.content.add_widget(*l)

    def remove_widget(self, *l):
        self.content.remove_widget(*l)

    def clear_widgets(self):
        self.content.clear_widgets()

