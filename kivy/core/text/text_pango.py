'''
Pango text provider
===================

'''

__all__ = ('LabelPango', )

from kivy.compat import PY2
from kivy.core.text import LabelBase
from kivy.core.text._text_pango import (KivyPangoRenderer, kpango_get_extents,
                                        kpango_get_ascent, kpango_get_descent)


class LabelPango(LabelBase):

    # This is a hack to avoid dealing with glib attrs to configure layout,
    # we just create markup out of the options and let pango set attrs
    def _pango_markup(self, text):
        markup = text.replace('<', '&lt;').replace('>', '&gt;')
        options = self.options
        tags = []
        if options['bold']:
            markup = '<b>{}</b>'.format(markup)
        if options['underline']:
            markup = '<u>{}</u>'.format(markup)
        if options['strikethrough']:
            markup = '<s>{}</s>'.format(markup)
        if options['font_hinting'] == 'mono':
            markup = '<tt>{}</tt>'.format(markup)

        # FIXME: does this do the right thing? .. don't see much w/roboto
        weight_attr = ''
        if options['font_hinting'] in ('light', 'normal'):
            weight_attr = ' weight="{}"'.format(options['font_hinting'])

        return '<span font="{}"{}>{}</span>'.format(
                int(self.options['font_size']),
                weight_attr,
                markup)

    def get_extents(self, text):
        if not text:
            return (0, 0)
        w, h = kpango_get_extents(self, self._pango_markup(text))
        return (w, h)

    def get_ascent(self):
        return kpango_get_ascent(self)

    def get_descent(self):
        return kpango_get_descent(self)

    def _render_begin(self):
        self._rdr = KivyPangoRenderer(self._size[0], self._size[1])

    def _render_text(self, text, x, y):
        self._rdr.render(self, self._pango_markup(text), x, y)

    def _render_end(self):
        imgdata = self._rdr.get_ImageData()
        del self._rdr
        return imgdata
