'''
Pango text provider
===================

'''

__all__ = ('LabelPango', )

from kivy.compat import PY2
from kivy.core.text import LabelBase
from kivy.core.text._text_pango import (KivyPangoRenderer, kpango_get_extents,
                                        kpango_get_metrics)


class LabelPango(LabelBase):

    # This is a hack to avoid dealing with glib attrs to configure layout,
    # we just create markup out of the options and let pango set attrs
    def _pango_markup(self, text):
        markup = (text.replace('&', '&amp;')
                      .replace('<', '&lt;')
                      .replace('>', '&gt;'))
        options = self.options
        tags = []
        if options['bold']:
            markup = '<b>{}</b>'.format(markup)
        if options['underline']:
            markup = '<u>{}</u>'.format(markup)
        if options['strikethrough']:
            markup = '<s>{}</s>'.format(markup)

        span_attrs = ''
        if options['font_features']:
            span_attrs += 'font_features="{}" '.format(options['font_features'])
        if options['text_language']:
            span_attrs += 'lang="{}" '.format(options['text_language'])

        return '<span font_size="{}"{}>{}</span>'.format(
                int(self.options['font_size']),
                span_attr,
                markup)

    def get_extents(self, text):
        if not text:
            return (0, 0)
        w, h = kpango_get_extents(self, self._pango_markup(text))
        return (w, h)

    def get_ascent(self):
        return kpango_get_metrics(self)[0]

    def get_descent(self):
        return kpango_get_metrics(self)[1]

    def _render_begin(self):
        self._rdr = KivyPangoRenderer(self._size[0], self._size[1])

    def _render_text(self, text, x, y):
        self._rdr.render(self, self._pango_markup(text), x, y)

    def _render_end(self):
        imgdata = self._rdr.get_ImageData()
        del self._rdr
        return imgdata
