'''
Pango text provider
===================

.. versionadded:: 1.10.1


Font context types for FontConfig+FreeType2 backend
---------------------------------------------------

* `system://` - `FcInitLoadConfigAndFonts()`
* `systemconfig://` - `FcInitLoadConfig()`
* `directory://<PATH>` - `FcInitLoadConfig()` + `FcAppFontAddDir()`
* `fontconfig://<PATH>` - `FcConfigCreate()` + `FcConfigParseAndLoad()`
* Any other context name - `FcConfigCreate()`


Known limitations
-----------------

* Pango versions older than v1.38 has limited support, and is not widely
  tested or researched. It may work on some systems with older pango and
  newer FontConfig/FreeType2 versions.
* Kivy's text layout is used, not Pango. This means we do not use Pango's
  line-breaking feature (which is superior to Kivy's), and we can't use
  Pango's bidirectional cursor helpers in TextInput.
* Font family collissions can happen. For example, if you use a `system://`
  context and add a custom `Arial.ttf`, using `arial` as the `font_family`
  may or may not draw with your custom font (depending on whether or not
  there is already a system-wide "arial" font installed)
* Rendering is inefficient; the normal way to integrate Pango would be
  using a dedicated PangoLayout per widget. This is not currently practical
  due to missing abstractions in Kivy core (in the current implementation,
  we have a dedicated PangoLayout *per font context,* which is rendered
  once for each LayoutWord)
'''

__all__ = ('LabelPango', )

from types import MethodType
from os.path import isfile
from kivy.resources import resource_find
from kivy.core.text import LabelBase, FontContextManagerBase
from kivy.core.text._text_pango import (
        KivyPangoRenderer,
        kpango_get_extents,
        kpango_get_ascent,
        kpango_get_descent,
        kpango_find_base_dir,
        kpango_font_context_exists,
        kpango_font_context_update,
        kpango_font_context_destroy,
        kpango_font_context_list,
        kpango_font_context_list_custom,
        kpango_font_context_list_families)


class LabelPango(LabelBase):
    def __init__(self, *largs, **kwargs):
        self.get_extents = MethodType(kpango_get_extents, self)
        self.get_ascent = MethodType(kpango_get_ascent, self)
        self.get_descent = MethodType(kpango_get_descent, self)
        super(LabelPango, self).__init__(*largs, **kwargs)

    @staticmethod
    def find_base_direction(text):
        return kpango_find_base_dir(text)

    def _render_begin(self):
        self._rdr = KivyPangoRenderer(*self._size)

    def _render_text(self, text, x, y):
        self._rdr.render(self, text, x, y)

    def _render_end(self):
        imgdata = self._rdr.get_ImageData()
        del self._rdr
        return imgdata


class PangoFontContextManager(FontContextManagerBase):
    @staticmethod
    def create(font_context):
        if PangoFontContextManager.exists(font_context):
            return False
        kpango_font_context_update(font_context)
        return True

    @staticmethod
    def exists(font_context):
        return kpango_font_context_exists(font_context)

    @staticmethod
    def destroy(font_context):
        kpango_font_context_destroy(font_context)

    @staticmethod
    def list():
        return kpango_font_context_list()

    @staticmethod
    def list_families(font_context):
        return kpango_font_context_list_families(font_context)

    @staticmethod
    def list_custom(font_context):
        return kpango_font_context_list_custom(font_context)

    @staticmethod
    def add_font(font_context, filename, autocreate=True, family=None):
        if not autocreate and not PangoFontContextManager.exists(font_context):
            raise Exception("FontContextManager: Attempt to add font file "
                            "'{}' to non-existing context '{}' without "
                            "autocreate.".format(filename, font_context))
        if not isfile(filename):
            filename = resource_find(filename)
        if not isfile(filename):
            if not filename.endswith('.ttf'):
                filename = resource_find('{}.ttf'.format(filename))
        if filename and isfile(filename):
            pango_font_context_update(font_context, filename)
            result = kpango_font_context_update(font_context, filename)
            return result[0]
        raise Exception("FontContextManager: Attempt to add non-existant "
                        "font file: '{}' to context '{}'".format(filename, font_context))
