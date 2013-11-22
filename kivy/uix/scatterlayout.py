'''
Scatter Layout
===============

.. versionadded:: 1.6.0

This layout behaves just like a
:class:`~kivy.uix.relativelayout.RelativeLayout`.
For example, if you create a :class:`ScatterLayout`, add a widget with
position = (0,0), the child widget will also move when you change the
position of the :class:`ScatterLayout`.  The child widget's coordinates remain
(0,0), i.e. they are relative to the containing layout.

However, since :class:`ScatterLayout` is implemented using a
:class:`~kivy.uix.scatter.Scatter`
widget, you can also translate, rotate and scale the layout using touches
(mouse or fingers) just like a normal Scatter widget and the child
widgets will behave as expected.

In contrast to a Scatter, the Layout favours 'hint' properties, such as
size_hint, size_hint_x, size_hint_y and pos_hint.

.. note::

    The :class:`ScatterLayout` is implemented as a 
    :class:`~kivy.uix.floatlayout.FloatLayout`
    inside a :class:`~kivy.uix.scatter.Scatter`.

.. warning::

    Since the actual :class:`ScatterLayout` is a 
    :class:`~kivy.uix.scatter.Scatter`, its
    add_widget and remove_widget functions are overridden to add children
    to the embedded :class:`~kivy.uix.floatlayout.FloatLayout` (accessible as
    the `content` property of :class:`~kivy.uix.scatter.Scatter`) automatically.
    So if you want to access the added
    child elements, you need self.content.children instead of self.children.

.. warning::

    The :class:`ScatterLayout` was introduced in 1.7.0 and was called
    :class:`~kivy.uix.relativelayout.RelativeLayout` in prior versions.
    The :class:`~kivy.uix.relativelayout.RelativeLayout` is now an optimized
    implementation that uses only a positional transform to avoid some of the
    heavier calculation involved for :class:`~kivy.uix.scatter.Scatter`.

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

