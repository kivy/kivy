'''
Pango text provider
===================

'''

__all__ = ('LabelPango', )

from types import MethodType
from kivy.core.text import LabelBase
from kivy.core.text._text_pango import (KivyPangoRenderer, kpango_get_extents,
                                        kpango_get_ascent, kpango_get_descent,
                                        kpango_find_base_dir)


class LabelPango(LabelBase):
    def __init__(self, *largs, **kwargs):
        self.get_extents = MethodType(kpango_get_extents, self)
        self.get_ascent = MethodType(kpango_get_ascent, self)
        self.get_descent = MethodType(kpango_get_descent, self)
        super(LabelPango, self).__init__(*largs, **kwargs)

    @staticmethod
    def _find_base_direction(text):
        return kpango_find_base_dir(text)

    def _render_begin(self):
        self._rdr = KivyPangoRenderer(*self._size)

    def _render_text(self, text, x, y):
        self._rdr.render(self, text, x, y)

    def _render_end(self):
        imgdata = self._rdr.get_ImageData()
        del self._rdr
        return imgdata
