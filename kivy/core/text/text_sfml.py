'''
Text SFML: Draw text with SFML

.. warning::
    This class is still incomplete and not ready for production use.
    Issues with OpenGL on Intel based graphics cards prevent its completion.
'''

__all__ = () # empty until module is ready

try:
    import sfml.graphics as sf
except:
    raise

from kivy.core.text import LabelBase
from kivy.core.image import ImageData

class LabelSFML(LabelBase):
    _cache = {}

    def _select_font(self):
        font_name = self.options['font_name_r']
        font_size = int(self.options['font_size'] * 1.333)

        id_ = u'{0}.{1}'.format(font_name, font_size)

        if not id_ in self._cache:
            font = sf.Font.from_file(font_name)

            self._cache[id_] = font, font_size

        return self._cache[id_]

    def get_extents(self, text):
        font, size = self._select_font()
        text = sf.Text(text, font, size)
        _, _, w, h, = text.local_bounds

        return w, h

    def _render_begin(self):
        self._sfml_texture = sf.RenderTexture(*self._size)
        self._sfml_texture.clear()

    def _render_text(self, text, x, y):
        font, size = self._select_font()
        text = sf.Text(text, font, size)
        text.color = sf.Color(*self.options['color'])

        self._sfml_texture.draw(text)
        self._sfml_texture.display()

    def _render_end(self):
        w, h = self._size
        image = self._sfml_texture.texture.copy_to_image()
        data = ImageData(w, h, 'rgba', image.pixels.data)

        del self._sfml_texture

        return data
