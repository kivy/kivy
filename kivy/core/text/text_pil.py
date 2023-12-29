'''
Text PIL: Draw text with PIL
'''

__all__ = ('LabelPIL', )

from PIL import Image, ImageFont, ImageDraw


from kivy.compat import text_type
from kivy.core.text import LabelBase
from kivy.core.image import ImageData

# used for fetching extends before creature image surface
default_font = ImageFont.load_default()


class LabelPIL(LabelBase):
    _cache = {}

    def _select_font(self):
        if self.options['font_size'] < 1:
            return None

        fontsize = int(self.options['font_size'])
        fontname = self.options['font_name_r']
        try:
            id = '%s.%s' % (text_type(fontname), text_type(fontsize))
        except UnicodeDecodeError:
            id = '%s.%s' % (fontname, fontsize)

        if id not in self._cache:
            font = ImageFont.truetype(fontname, fontsize)
            self._cache[id] = font

        return self._cache[id]

    def get_extents(self, text):
        font = self._select_font()
        if not font:
            return 0, 0

        left, top, right, bottom = font.getbbox(text)
        ascent, descent = font.getmetrics()

        if self.options['limit_render_to_text_bbox']:
            h = bottom - top
        else:
            h = ascent + descent
        w = right - left

        return w, h

    def get_cached_extents(self):
        return self.get_extents

    def _render_begin(self):
        # create a surface, context, font...
        self._pil_im = Image.new('RGBA', self._size, color=(255, 255, 255, 0))
        self._pil_draw = ImageDraw.Draw(self._pil_im)

    def _render_text(self, text, x, y):
        font = self._select_font()
        if not font:
            return

        color = tuple([int(c * 255) for c in self.options['color']])

        # Adjust x and y position to avoid text cutoff
        if self.options['limit_render_to_text_bbox']:
            bbox = font.getbbox(text)
            x -= bbox[0]
            y -= bbox[1]

        self._pil_draw.text((int(x), int(y)), text, font=font, fill=color)

    def _render_end(self):
        data = ImageData(self._size[0], self._size[1],
                         self._pil_im.mode.lower(), self._pil_im.tobytes())

        del self._pil_im
        del self._pil_draw

        return data
