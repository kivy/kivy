
__all__ = ('LabelPango',)

from kivy.core.image import ImageData
from kivy.core.text import LabelBase
from kivy.compat import PY2

try:
    import cairo
    import pango
    import pangocairo
except:
    raise

class LabelPango(LabelBase):
    def _get_font_id(self):
        if PY2:
            try:
                return '|'.join([unicode(self.options[x]) for x in
                                 ('font_size', 'font_name_r',
                                  'bold', 'italic')])
            except UnicodeDecodeError:
                pass
        return '|'.join([str(self.options[x]) for x in
                         ('font_size', 'font_name_r', 'bold', 'italic')])
    
    def _get_font(self):
        return pango.FontDescription(self._get_font_id())
    
    def get_extents(self, text):
        font = self._get_font()
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
        context = cairo.Context(surface)
        pangocairo_context = pangocairo.CairoContext(context)
        pangocairo_context.set_antialias(cairo.ANTIALIAS_DEFAULT)
        layout = pangocairo_context.create_layout()
        layout.set_font_description(font)
        layout.set_text(text)
        pangocairo_context.update_layout(layout)
        extents = layout.get_pixel_extents()[1]
        size = extents[2] - extents[0], extents[3] - extents[1]
        return size
    
    
    def _render_begin(self):
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *self._size)
        self.context = cairo.Context(self.surface)
        self.pangocairo_context = pangocairo.CairoContext(self.context)
        self.pangocairo_context.set_antialias(cairo.ANTIALIAS_SUBPIXEL)


    def _render_text(self, text, x, y):
        context = self.context
        pangocairo_context = self.pangocairo_context
        layout = pangocairo_context.create_layout()
        layout.set_font_description(self._get_font())
        layout.set_text(text)       
        context.set_source_rgba(*self.options['color'])
        pangocairo_context.update_layout(layout)
        pangocairo_context.show_layout(layout)
    
    def _render_end(self):
        Imgdata = self.surface.get_data()
        del self.pangocairo_context
        del self.context
        del self.surface
        return ImageData(self._size[0], self._size[1], 'rgba', Imgdata)

