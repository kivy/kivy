'''
Scroll View
===========

A ScrollView provides a scrollable/pannable viewport which is clipped to the
ScrollView's bounding box.
'''

__all__ = ('ScrollView', )

from kivy.uix.stencilview import StencilView
from kivy.uix.scatter import ScatterPlane


class ScrollView(StencilView):
    '''ScrollView class. See module documentation for more informations.
    '''

    def __init__(self, **kwargs):
        self.viewport = ScatterPlane()
        super(ScrollView, self).__init__(**kwargs)
        super(ScrollView, self).add_widget(self.viewport)

        self.viewport.bind(size=self.size)

    def add_widget(self, widget):
        self.viewport.add_widget(widget)

    def remove_widget(self, widget):
        self.viewport.remove_widget(widget)

    def clear_widgets(self):
        self.viewport.clear()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return super(ScrollView, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            return super(ScrollView, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            return super(ScrollView, self).on_touch_up(touch)

