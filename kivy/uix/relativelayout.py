'''
Relative Layout
===============

.. versionadded:: 1.4.0

This layout allow you to set relative coordinate for children. If you want
absolute positioning, check :class:`~kivy.uix.floatlayout.FloatLayout`.
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
