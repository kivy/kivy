'''
Pango text provider
===================

.. versionadded:: 1.11.0

.. warning::
    The low-level Pango API is experimental, and subject to change without
    notice for as long as this warning is present.


Installation
------------

1. Install pangoft2 (`apt install libfreetype6-dev libpango1.0-dev
   libpangoft2-1.0-0`) or ensure it is available in pkg-config
2. Recompile kivy. Check that pangoft2 is found `use_pangoft2 = 1`
3. Test it! Enforce the text core renderer to pango using environment variable:
   `export KIVY_TEXT=pango`

This has been tested on OSX and Linux, Python 3.6.


Font context types for FontConfig+FreeType2 backend
---------------------------------------------------

* `system://` - `FcInitLoadConfigAndFonts()`
* `systemconfig://` - `FcInitLoadConfig()`
* `directory://<PATH>` - `FcInitLoadConfig()` + `FcAppFontAddDir()`
* `fontconfig://<PATH>` - `FcConfigCreate()` + `FcConfigParseAndLoad()`
* Any other context name - `FcConfigCreate()`


Low-level Pango access
----------------------

Since Kivy currently does its own text layout, the Label and TextInput widgets
do not take full advantage of Pango. For example, line breaks do not take
language/script into account, and switching alignment per paragraph (for bi-
directional text) is not supported. For advanced i18n requirements, we provide
a simple wrapper around PangoLayout that you can use to render text.

* https://developer.gnome.org/pango/1.40/pango-Layout-Objects.html
* https://developer.gnome.org/pango/1.40/PangoMarkupFormat.html
* See the `kivy/core/text/_text_pango.pyx` file @ `cdef class KivyPangoLayout`
  for more information. Not all features of PangoLayout are implemented.

.. python::
    from kivy.core.window import Window  # OpenGL must be initialized
    from kivy.core.text._text_pango import KivyPangoLayout
    layout = KivyPangoLayout('system://')
    layout.set_markup('<span font="20">Hello <b>World!</b></span>')
    tex = layout.render_as_Texture()


Known limitations
-----------------

* Pango versions older than v1.38 has not been tested. It may work on
  some systems with older pango and newer FontConfig/FreeType2 versions.
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
        kpango_font_context_create,
        kpango_font_context_destroy,
        kpango_font_context_add_font,
        kpango_font_context_list,
        kpango_font_context_list_custom,
        kpango_font_context_list_families)


class LabelPango(LabelBase):

    _font_family_support = True

    def __init__(self, *largs, **kwargs):
        self.get_extents = MethodType(kpango_get_extents, self)
        self.get_ascent = MethodType(kpango_get_ascent, self)
        self.get_descent = MethodType(kpango_get_descent, self)
        super(LabelPango, self).__init__(*largs, **kwargs)

    find_base_direction = staticmethod(kpango_find_base_dir)

    def _render_begin(self):
        self._rdr = KivyPangoRenderer(*self._size)

    def _render_text(self, text, x, y):
        self._rdr.render(self, text, x, y)

    def _render_end(self):
        imgdata = self._rdr.get_ImageData()
        del self._rdr
        return imgdata


class PangoFontContextManager(FontContextManagerBase):
    create = staticmethod(kpango_font_context_create)
    exists = staticmethod(kpango_font_context_exists)
    destroy = staticmethod(kpango_font_context_destroy)
    list = staticmethod(kpango_font_context_list)
    list_families = staticmethod(kpango_font_context_list_families)
    list_custom = staticmethod(kpango_font_context_list_custom)

    @staticmethod
    def add_font(font_context, filename, autocreate=True, family=None):
        if not autocreate and not PangoFontContextManager.exists(font_context):
            raise Exception("FontContextManager: Attempt to add font file "
                            "'{}' to non-existing context '{}' without "
                            "autocreate.".format(filename, font_context))
        if not filename:
            raise Exception("FontContextManager: Cannot add empty font file")
        if not isfile(filename):
            filename = resource_find(filename)
        if not isfile(filename):
            if not filename.endswith('.ttf'):
                filename = resource_find('{}.ttf'.format(filename))
        if filename and isfile(filename):
            return kpango_font_context_add_font(font_context, filename)
        raise Exception("FontContextManager: Attempt to add non-existant "
                        "font file: '{}' to context '{}'"
                        .format(filename, font_context))
