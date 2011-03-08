'''
Stencil widgets
'''

__all__ = ('StencilView', )

from kivy.graphics import StencilCanvas, Color, Rectangle
from kivy.uix.widget import Widget


class StencilView(Widget):
    '''
    StencilView:
        limits drawing of its child widgets
        to inside its bounding box / stencil area. Using the stencil
        buffer / test provides an efficient way to clipp the drawing area
        of its children.
    '''

    def __init__(self, **kwargs):
        self._clip_region = None
        super(StencilView, self).__init__(**kwargs)

        self.canvas = StencilCanvas()
        with self.canvas.stencil:
            Color(1, 1, 1)
            self._clip_region = Rectangle(pos=self.pos, size=self.size)

    def on_pos(self, *args):
        if self._clip_region:
            self._clip_region.pos = self.pos

    def on_size(self, *args):
        if self._clip_region:
            self._clip_region.size = self.size
