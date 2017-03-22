
__all__ = ('LabelHarfBuzz',)

from kivy.core.image import ImageData
from kivy.core.text import LabelBase
from kivy.compat import PY2

try:
    import qahirah as qah
    from qahirah import \
         CAIRO, \
         Colour, \
         Glyph, \
         Vector
    import harfbuzz as hb
except:
    raise


class LabelHarfBuzz(LabelBase):
    def _get_font_id(self):
        if PY2:
            try:
                return '|'.join([unicode(self.options[x]) for x
                    in ('font_size', 'font_name_r', 'bold',
                        'italic', 'underline', 'strikethrough')])
            except UnicodeDecodeError:
                pass
        return '|'.join([str(self.options[x]) for x
            in ('font_size', 'font_name_r', 'bold',
                'italic', 'underline', 'strikethrough')])

    def _get_font(self):
        return qah.get_ft_lib()

    def get_extents(self, text):
        pass

    def _render_begin(self):
        self.ft = self._get_font()
        self.text_size = self.options['font_size']
        self.label_font = \
            (qah.Context.create_for_dummy()
                .set_font_face(qah.FontFace.create_for_pattern("DejaVu Serif"))
                .set_font_size(self.text_size / 2)
            ).scaled_font
        self.buf = hb.Buffer.create()
        self.line_pos = Vector(0, 0)
        self.ft_face = self.ft.find_face(_font)
        self.ft_face.set_char_size(size = self.text_size, resolution = qah.base_dpi)
        self.hb_font = hb.Font.ft_create(self.ft_face)

    def _render_text(self, text, x, y):
        self.buf.reset()
        self.buf.add_str(text)
        self.buf.guess_segment_properties()
        hb.shape(self.hb_font, self.buf)
        line, line_end = self.buf.get_glyphs(self.line_pos)
        self.lines =\
            {
                "font" :
                    (qah.Context.create_for_dummy()
                        .set_font_face(qah.FontFace.create_for_ft_face(ft_face))
                        .set_font_size(self.text_size)
                    ).scaled_font,
                "text" : line,
            }
        self.line_pos = Vector(0, self.line_pos.y + ft_face.size["metrics"]["height"])
        margin = Vector(10, 10)
        figure_size = Vector(line_end.x, self.line_pos.y) + 2 * margin
        self.img = qah.ImageSurface.create \
          (
            format = CAIRO.FORMAT_RGB24,
            dimensions = round(figure_size)
          )
        self.ctx = \
            (qah.Context.create(img)
                .translate(margin + Vector(0, self.text_size ))
                .set_source_colour(Colour.grey(1))
                .paint()
                .set_source_colour(Colour.grey(0))
            )

    def _render_end(self):
        self.ctx.set_scaled_font(label_font)
        self.ctx.set_scaled_font(self.lines["font"])
        self.ctx.show_glyphs(tuple(qah.offset_glyphs(self.lines["text"], Vector(0, 0))))
        Imgdata = img.data #exprimental fix
        # https://www.cairographics.org/manual/cairo-Image-Surfaces.html#cairo-image-surface-get-data
        # https://cairographics.org/documentation/pycairo/2/reference/surfaces.html#class-imagesurface-surface
        # img.flush().write_to_png("output.png")
        self.hb_font = None # prevents crash at end?
        return ImageData(self._size[0], self._size[1], 'rgba', Imgdata)

