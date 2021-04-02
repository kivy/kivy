'''
SDL2 text provider
==================

Based on SDL2 + SDL2_ttf
'''

__all__ = ('LabelSDL2', )

from kivy.core.text import LabelBase
try:
    from kivy.core.text._text_sdl2 import (
        _SurfaceContainer, _get_extents, _get_fontdescent, _get_fontascent)
except ImportError:
    from kivy.core import handle_win_lib_import_error
    handle_win_lib_import_error(
        'text', 'sdl2', 'kivy.core.text._text_sdl2')
    raise


class LabelSDL2(LabelBase):

    def _get_font_id(self):
        return '|'.join(
            [str(self.options[x]) for x in
             ('font_size', 'font_name_r', 'bold', 'italic', 'underline',
              'strikethrough')]
        )

    get_extents = _get_extents

    get_descent = _get_fontdescent

    get_ascent = _get_fontascent

    def _render_begin(self):
        self._surface = _SurfaceContainer(self._size[0], self._size[1])

    def _render_text(self, text, x, y):
        self._surface.render(self, text, x, y)

    def _render_end(self):
        return self._surface.get_data()
