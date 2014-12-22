'''
SDL2 text provider
==================

Based on SDL2 + SDL2_ttf
'''

__all__ = ('LabelSDL2', )

from kivy.compat import PY2
from kivy.core.text import LabelBase
from kivy.core.text._text_sdl2 import (_SurfaceContainer, _get_extents,
                                       _get_fontdescent, _get_fontascent)


class LabelSDL2(LabelBase):

    def _get_font_id(self):
        if PY2:
            try:
                return '|'.join([unicode(self.options[x]) for x
                    in ('font_size', 'font_name_r', 'bold', 'italic')])
            except UnicodeDecodeError:
                pass
        return '|'.join([str(self.options[x]) for x
            in ('font_size', 'font_name_r', 'bold', 'italic')])

    def get_extents(self, text):
        try:
            if PY2:
                text = text.encode('UTF-8')
        except:
            pass
        return _get_extents(self, text)

    def get_descent(self):
        return _get_fontdescent(self)

    def get_ascent(self):
        return _get_fontascent(self)

    def _render_begin(self):
        self._surface = _SurfaceContainer(self._size[0], self._size[1])

    def _render_text(self, text, x, y):
        self._surface.render(self, text, x, y)

    def _render_end(self):
        return self._surface.get_data()

