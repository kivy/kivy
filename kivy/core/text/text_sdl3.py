'''
SDL3 text provider
==================

Based on SDL3 + SDL3_ttf
'''

__all__ = ('LabelSDL3', )

from kivy.core.text import LabelBase
try:
    from kivy.core.text._text_sdl3 import (
        _SurfaceContainer,
        _get_extents,
        _get_tight_extents,
        _get_fontdescent,
        _get_fontascent,
    )
except ImportError:
    from kivy.core import handle_win_lib_import_error
    handle_win_lib_import_error(
        'text', 'sdl3', 'kivy.core.text._text_sdl3')
    raise


class LabelSDL3(LabelBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._baseline_offset = 0

    def _get_font_id(self):
        return '|'.join([str(self.options[x]) for x
            in ('font_size', 'font_name_r', 'bold',
                'italic', 'underline', 'strikethrough')])

    def get_extents(self, text):
        if self.options['limit_render_to_text_bbox']:
            return _get_tight_extents(self, text)
        else:
            return _get_extents(self, text)

    def get_descent(self):
        return _get_fontdescent(self)

    def get_ascent(self):
        return _get_fontascent(self)

    def _render_begin(self):
        self._surface = _SurfaceContainer(self._size[0], self._size[1])

    def _render_text(self, text, x, y):
        if self.options['limit_render_to_text_bbox']:
            y-= self._baseline_offset

        self._surface.render(self, text, x, y)

    def _render_end(self):
        return self._surface.get_data()
