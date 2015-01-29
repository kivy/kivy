'''
Text STB TrueType
'''

__all__ = ('LabelSTB', )

cdef extern from 'stb_truetype.h':
    cdef struct stbtt_fontinfo


from kivy.core.text import LabelBase
from kivy.core.image import ImageData

cdef class STBFont:
    cdef bytes filename
    cdef bytes ttf_buffer
    cdef stbtt_fontinfo font
    cdef dict c2g
    cdef dict gsize

    def __init__(self, filename):
        self.filename = <bytes>filename
        with open(filename) as fd:
            self.ttf_buffer = <bytes>fd.read()
        stbtt_InitFont(&self.font, <char *>self.ttf_buffer,
            stbtt_GetFontOffsetForIndex(<char *>self.ttf_buffer, 0))

    def getsize(self, text):
        cdef int och
        cdef int x0, y0, x1, y1
        cdef int g
        w = h = 0
        for ch in text:
            och = ord(ch)
            if och not in c2g:
                c2g[och] = g = stbtt_FindGlyphIndex(self.font, och)
                stbtt_GetGlyphBox(self.font, g, &x0, &y0, &x1, &y1)
                gzise[och] = (x0, y0, x1, y1)
            else:
                x0, y0, x1, y1 = gsize[och]



class LabelSTB(LabelBase):
    _cache = {}

    def _select_font(self):
        fontsize = int(self.options['font_size'])
        fontname = self.options['font_name_r']
        uid = '%s.%s' % (unicode(fontname), unicode(fontsize))
        if uid not in self._cache:
            font = STBFont(fontname)
            self._cache[uid] = font
        return self._cache[uid]

    def get_extents(self, text):
        font = self._select_font()
        w, h = font.getsize(text)
        return w, h

