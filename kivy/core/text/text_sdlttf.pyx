#cython: c_string_type=unicode, c_string_encoding=utf8
'''
Text/SDL_ttf
============

TODO:
    - ensure that we correctly check allocation
    - remove compat sdl usage (like SDL_SetAlpha must be replaced with sdl 1.3
      call, not 1.2)

'''

__all__ = ('LabelSDLttf', )

from kivy.compat import PY2
from kivy.core.text import LabelBase
from kivy.core.image import ImageData
from kivy.resources import resource_paths
from os.path import exists, join

cdef extern from "Python.h":
    object PyString_FromStringAndSize(char *s, Py_ssize_t len)

cdef extern from "SDL.h":
    ctypedef struct SDL_Surface:
        int w
        int h
        void *pixels

    ctypedef struct SDL_Rect:
        int x
        int y
        int w
        int h

    SDL_Surface *SDL_CreateRGBSurface(
        unsigned int flags, int width, int height, int depth,
         unsigned int Rmask, unsigned int Gmask, unsigned int Bmask, unsigned int Amask)
    void SDL_FreeSurface(SDL_Surface *surface)
    int SDL_FillRect(SDL_Surface *dst, SDL_Rect *rect, unsigned int color)
    int SDL_SRCALPHA
    int SDL_BlitSurface(SDL_Surface * src, SDL_Rect * srcrect,
         SDL_Surface * dst, SDL_Rect * dstrect)
    char *SDL_GetError()
    int SDL_SetAlpha(SDL_Surface * surface, unsigned int flag, char alpha)

    int SDL_BLENDMODE_BLEND
    int SDL_BLENDMODE_ADD
    int SDL_BLENDMODE_NONE
    int SDL_SetSurfaceBlendMode(SDL_Surface * surface, int blendMode)
    int SDL_SetSurfaceAlphaMod(SDL_Surface * surface, char alpha)


cdef extern from "SDL_ttf.h":
    ctypedef struct TTF_Font:
        pass
    ctypedef struct SDL_Color:
        unsigned char r
        unsigned char g
        unsigned char b

    TTF_Font *TTF_OpenFont(char *filename, int ptsize)
    SDL_Surface *TTF_RenderUTF8_Blended(TTF_Font *font, char *text, SDL_Color fg)
    int TTF_SizeUTF8(TTF_Font *font, char *text, int *w, int *h)
    void TTF_CloseFont(TTF_Font *font)
    void TTF_Quit()
    int TTF_FontDescent(TTF_Font *font)
    int TTF_FontAscent(TTF_Font *font)
    int TTF_WasInit()
    int TTF_Init()

pygame_cache = {}
pygame_cache_order = []

cdef class _TTFContainer:
    cdef TTF_Font* font
    def __cinit__(self):
        self.font = NULL
    def __dealloc__(self):
        if self.font != NULL:
            TTF_CloseFont(self.font)
            self.font = NULL


cdef class _SurfaceContainer:
    cdef SDL_Surface* surface
    def __cinit__(self):
        self.surface = NULL
    def __dealloc__(self):
        if self.surface != NULL:
            SDL_FreeSurface(self.surface)
            self.surface = NULL

cdef TTF_Font *_get_font(self):
    cdef TTF_Font *fontobject = NULL
    cdef _TTFContainer ttfc
    cdef char *error
    cdef str s_error

    if not TTF_WasInit():
        TTF_Init()

    fontid = self._get_font_id()
    if fontid not in pygame_cache:
        # try first the file if it's a filename
        fontname = self.options['font_name_r']
        ext = fontname.split('.')[-1]
        if ext.lower() == 'ttf':
            fontobject = TTF_OpenFont(fontname, int(self.options['font_size']))

        # fallback to search a system font
        if fontobject == NULL:
            s_error = <bytes>SDL_GetError()
            print(s_error)
            assert(0)
        pygame_cache[fontid] = ttfc = _TTFContainer()
        ttfc.font = fontobject
        pygame_cache_order.append(fontid)

    # to prevent too much file open, limit the number of opened fonts to 64
    while len(pygame_cache_order) > 64:
        popid = pygame_cache_order.pop(0)
        ttfc = pygame_cache[popid]
        del pygame_cache[popid]

    ttfc = pygame_cache[fontid]
    return ttfc.font


class LabelSDLttf(LabelBase):

    def _get_font_id(self):
        if PY2:
            try:
                return '|'.join([unicode(self.options[x]) for x \
                    in ('font_size', 'font_name_r', 'bold', 'italic')])
            except UnicodeDecodeError:
                pass
        return '|'.join([self.options[x] for x \
            in ('font_size', 'font_name_r', 'bold', 'italic')])

    def get_extents(self, text):
        try:
            if PY2:
                text = text.encode('UTF-8')
        except:
            pass
        cdef TTF_Font *font = _get_font(self)
        cdef int w, h
        if font == NULL:
            return 0, 0
        TTF_SizeUTF8(font, <char *><bytes>text, &w, &h)
        return w, h

    def get_descent(self):
        return TTF_FontDescent(_get_font(self))

    def get_ascent(self):
        return TTF_FontAscent(_get_font(self))

    def _render_begin(self):
        cdef _SurfaceContainer sc = _SurfaceContainer()
        cdef SDL_Rect r
        sc.surface = SDL_CreateRGBSurface(0,
            self._size[0], self._size[1], 32,
            0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000)
        r.x = r.y = 0
        r.w, r.h = self._size
        SDL_FillRect(sc.surface, &r, 0x00000000)
        self._surface = sc

    def _render_text(self, text, x, y):
        try:
            if PY2:
                text = text.encode('UTF-8')
        except:
            pass
        cdef TTF_Font *font = _get_font(self)
        cdef SDL_Color c
        cdef _SurfaceContainer sc = self._surface
        cdef SDL_Surface *st
        cdef SDL_Rect r
        cdef list color = list(self.options['color'])
        if font == NULL:
            return
        c.r = <int>(color[0] * 255)
        c.g = <int>(color[1] * 255)
        c.b = <int>(color[2] * 255)
        st = TTF_RenderUTF8_Blended(font, <char *><bytes>text, c)
        if st == NULL:
            return
        r.x = x
        r.y = y
        r.w = st.w
        r.h = st.h
        SDL_SetSurfaceAlphaMod(st, 0xff);
        SDL_SetSurfaceBlendMode(st, SDL_BLENDMODE_NONE);
        SDL_BlitSurface(st, NULL, sc.surface, &r)
        SDL_FreeSurface(st)

    def _render_end(self):
        cdef _SurfaceContainer sc = self._surface
        cdef bytes pixels = PyString_FromStringAndSize(<char *>sc.surface.pixels,
                sc.surface.w * sc.surface.h * 4)
        data = ImageData(self._size[0], self._size[1],
            'rgba', pixels)
        del self._surface
        return data
