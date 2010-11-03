'''
Text Cairo: Draw text with cairo
'''

__all__ = ('LabelCairo', )

import kivy
from . import LabelBase

try:
    import cairo
except:
    raise

FONT_EXTENTS_ASCENT_IDX         = 0
FONT_EXTENTS_DESCENT_IDX        = 1
FONT_EXTENTS_HEIGHT_IDX         = 2
FONT_EXTENTS_MAX_X_ADVANCE_IDX  = 3
FONT_EXTENTS_MAX_Y_ADVANCE_IDX  = 4

TEXT_EXTENTS_X_BEARING_IDX      = 0
TEXT_EXTENTS_Y_BEARING_IDX      = 1
TEXT_EXTENTS_WIDTH_IDX          = 2
TEXT_EXTENTS_HEIGHT_IDX         = 3
TEXT_EXTENTS_X_ADVANCE_IDX      = 4
TEXT_EXTENTS_Y_ADVANCE_IDX      = 5

# used for fetching extends before creature image surface
cairo_default_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
cairo_default_context = cairo.Context(cairo_default_surface)

class LabelCairo(LabelBase):
    def _select_font(self, context):
        italic = cairo.FONT_SLANT_NORMAL
        bold = cairo.FONT_WEIGHT_NORMAL
        fontsize = self.options['font_size'] * 1.333
        fontname = self.options['font_name'].split(',')[0]
        if self.options['bold']:
            bold = cairo.FONT_WEIGHT_BOLD
        if self.options['italic']:
            italic = cairo.FONT_SLANT_ITALIC

        context.select_font_face(fontname, italic, bold)
        context.set_font_size(fontsize)
        font_options = context.get_font_options()
        font_options.set_hint_style(cairo.HINT_STYLE_FULL)
        context.set_font_options(font_options)

        # get maximum height for font
        font_extents = context.font_extents()
        self._font_extents = font_extents
        self._height = \
            self._font_extents[FONT_EXTENTS_DESCENT_IDX] + \
            self._font_extents[FONT_EXTENTS_ASCENT_IDX]

    def get_extents(self, text):
        self._select_font(cairo_default_context)
        extents = cairo_default_context.text_extents(text)
        return (extents[4], self._height)

    def _render_begin(self):
        # create a surface, context, font...
        self._cairo_surface = cairo.ImageSurface(
                cairo.FORMAT_ARGB32, *self.size)
        self._cairo_context = cairo.Context(self._cairo_surface)

        self._select_font(self._cairo_context)

    def _render_text(self, text, x, y):
        color = map(lambda x: x * 255, self.options['color'])
        self._cairo_context.set_source_rgba(*color)
        self._cairo_context.move_to(x,
            y + self._font_extents[FONT_EXTENTS_ASCENT_IDX])
        self._cairo_context.show_text(text)

    def _render_end(self):
        data = kivy.ImageData(self.width, self.height,
            'RGBA', buffer(self._cairo_surface.get_data())[:])

        del self._cairo_surface
        del self._cairo_context

        return data
