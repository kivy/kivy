'''
Relative Layout
===============

.. versionadded:: 1.4.0

This layout allows you to set relative coordinate for children. If you want
absolute positioning, check :class:`~kivy.uix.floatlayout.FloatLayout`.

The :class:`RelativeLayout` class behaves just like the regular Float
Layout, except that its child widgets are positioned relative to the layout.

For example, if you create a RelativeLayout, add a widgets with
position = (0,0), the child widget will also move, when you change the
position of the RelativeLayout.  The child widgets coordiantes remain
(0,0), i.e. they are relative to the containing layout.

..note::

    The :class:`RelativeLayout` is implemented as a :class`FloatLayout`
    inside a :class:`Scatter`.

.. warning::

    Since the actual RelativeLayout is a Scatter, its add_widget and
    remove_widget functions are overwritten to add children to the embedded
    FloatLayout (accessible as `content` property of RelativeLayout)
    automatically. So if you want to access the added child elements,
    you need self.content.children, instead of self.children.
'''

from kivy.uix.scatter import Scatter
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty


class RelativeLayout(Scatter):
    '''RelativeLayout class, see module documentation for more information.
    '''

    content = ObjectProperty()

    def __init__(self, **kw):
        self.content = FloatLayout()
        super(RelativeLayout, self).__init__(**kw)
        super(RelativeLayout, self).add_widget(self.content)
        self.bind(size=self.update_size)

    def update_size(self, instance, size):
        self.content.size = size

    def add_widget(self, *l):
        self.content.add_widget(*l)

    def remove_widget(self, *l):
        self.content.remove_widget(*l)
