from kivy.core.text import LabelBase
from kivy.core.image import ImageData

try:
    from kivy.core.image import osxcoreimage
    from kivy.core.text import appletext
except:
    raise


class LabelAppleText(LabelBase):

    def get_extents(self, txt):
        size = self.options['font_size']
        return appletext.get_extents(txt, "Helvetica", size)

    def _render_begin(self):
        w, h = self._size
        self._label = osxcoreimage.Label(w, h, "Helvetica-Bold", #self.options['font_name'],
            self.options['font_size'])

    def _render_text(self, text, x, y):
        self._label.draw_at_pos(text, x, y)

    def _render_end(self):
        ret = self._label.get_image_data()
        return ImageData(*ret)

