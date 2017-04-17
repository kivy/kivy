#cython: c_string_type=unicode, c_string_encoding=utf8
'''
TODO:
    - ensure that we correctly check allocation
    - remove compat sdl usage (like SDL_SetAlpha must be replaced with sdl 1.3
      call, not 1.2)
'''

include '../../lib/sdl2.pxi'

from libc.string cimport memset
from kivy.core.image import ImageData
from kivy.compat import PY2

cdef dict sdl2_cache = {}
cdef list sdl2_cache_order = []

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
    cdef int w, h

    def __cinit__(self, w, h):
        self.surface = NULL
        self.w = w
        self.h = h

    def __init__(self, w, h):
        # XXX check on OSX to see if little endian/big endian make a difference
        # here.
        self.surface = SDL_CreateRGBSurface(0,
            w, h, 32,
            0x000000ff, 0x0000ff00, 0x00ff0000, 0xff000000)
        memset(self.surface.pixels, 0, w * h * 4)

    def __dealloc__(self):
        if self.surface != NULL:
            SDL_FreeSurface(self.surface)
            self.surface = NULL

    def render(self, container, text, x, y):
        cdef TTF_Font *font = _get_font(container)
        cdef SDL_Color c
        cdef SDL_Color oc
        cdef SDL_Surface *st
        cdef SDL_Surface *fgst
        cdef SDL_Rect r
        cdef SDL_Rect fgr
        cdef list color = list(container.options['color'])
        cdef list outline_color = list(container.options['outline_color'])
        outline_width = container.options['outline_width']
        if font == NULL:
            return
        c.r = <int>(color[0] * 255)
        c.g = <int>(color[1] * 255)
        c.b = <int>(color[2] * 255)
        bytes_text = <bytes>text.encode('utf-8')

        hinting = container.options['font_hinting']
        if hinting == 'normal':
            if TTF_GetFontHinting(font) != TTF_HINTING_NORMAL:
                TTF_SetFontHinting(font, TTF_HINTING_NORMAL)
        elif hinting == 'light':
            if TTF_GetFontHinting(font) != TTF_HINTING_LIGHT:
                TTF_SetFontHinting(font, TTF_HINTING_LIGHT)
        elif hinting == 'mono':
            if TTF_GetFontHinting(font) != TTF_HINTING_MONO:
                TTF_SetFontHinting(font, TTF_HINTING_MONO)
        elif hinting is None:
            if TTF_GetFontHinting(font) != TTF_HINTING_NONE:
                TTF_SetFontHinting(font, TTF_HINTING_NONE)

        if container.options['font_kerning']:
            if TTF_GetFontKerning(font) == 0:
                TTF_SetFontKerning(font, 1)
        else:
            if TTF_GetFontKerning(font) != 0:
                TTF_SetFontKerning(font, 0)

        if outline_width:
            TTF_SetFontOutline(font, outline_width)
            oc.r = <int>(outline_color[0] * 255)
            oc.g = <int>(outline_color[1] * 255)
            oc.b = <int>(outline_color[2] * 255)
            st = (
                TTF_RenderUTF8_Blended(font, <char *>bytes_text, oc)
                if container.options['font_blended']
                else TTF_RenderUTF8_Solid(font, <char *>bytes_text, oc)
                )
            TTF_SetFontOutline(font, 0)
        else:
            st = (
                TTF_RenderUTF8_Blended(font, <char *>bytes_text, c)
                if container.options['font_blended']
                else TTF_RenderUTF8_Solid(font, <char *>bytes_text, c)
                )
        if st == NULL:
            return
        if outline_width:
            fgst = (
                TTF_RenderUTF8_Blended(font, <char *>bytes_text, c)
                if container.options['font_blended']
                else TTF_RenderUTF8_Solid(font, <char *>bytes_text, c)
                )
            if fgst == NULL:
                return
            fgr.x = outline_width
            fgr.y = outline_width
            fgr.w = fgst.w
            fgr.h = fgst.h
            SDL_SetSurfaceBlendMode(fgst, SDL_BLENDMODE_BLEND)
            SDL_BlitSurface(fgst, NULL, st, &fgr)
            SDL_FreeSurface(fgst)

        r.x = x
        r.y = y
        r.w = st.w
        r.h = st.h
        SDL_SetSurfaceAlphaMod(st, <int>(color[3] * 255))
        SDL_SetSurfaceBlendMode(st, SDL_BLENDMODE_NONE)
        SDL_BlitSurface(st, NULL, self.surface, &r)
        SDL_FreeSurface(st)

    def get_data(self):
        cdef int datalen = self.surface.w * self.surface.h * 4
        cdef bytes pixels = (<char *>self.surface.pixels)[:datalen]
        data = ImageData(self.w, self.h, 'rgba', pixels)
        return data


cdef TTF_Font *_get_font(self):
    cdef TTF_Font *fontobject = NULL
    cdef _TTFContainer ttfc
    cdef char *error
    cdef str s_error

    # fast path
    fontid = self._get_font_id()
    if fontid in sdl2_cache:
        ttfc = sdl2_cache[fontid]
        return ttfc.font

    # ensure ttf is init.
    if not TTF_WasInit():
        TTF_Init()

    # try first the file if it's a filename
    fontname = self.options['font_name_r']
    bytes_fontname = <bytes>fontname.encode('utf-8')
    ext = fontname.rsplit('.', 1)
    if len(ext) == 2:
        # try to open the fount if it has an extension
        fontobject = TTF_OpenFont(bytes_fontname,
                                  int(self.options['font_size']))
    # fallback to search a system font
    if fontobject == NULL:
        s_error = (<bytes>SDL_GetError()).encode('utf-8')
        print(s_error)
        assert(0)

    # set underline and strikethrough style
    style = TTF_STYLE_NORMAL
    if self.options['underline']:
        style = style | TTF_STYLE_UNDERLINE
    if self.options['strikethrough']:
        style = style | TTF_STYLE_STRIKETHROUGH
    TTF_SetFontStyle(fontobject, style)

    sdl2_cache[fontid] = ttfc = _TTFContainer()
    ttfc.font = fontobject
    sdl2_cache_order.append(fontid)

    # to prevent too much file open, limit the number of opened fonts to 64

    while len(sdl2_cache_order) > 64:
        popid = sdl2_cache_order.pop(0)
        ttfc = sdl2_cache[popid]
        del sdl2_cache[popid]

    ttfc = sdl2_cache[fontid]

    return ttfc.font

def _get_extents(container, text):
    cdef TTF_Font *font = _get_font(container)
    cdef int w, h
    outline_width = container.options['outline_width']
    if font == NULL:
        return 0, 0
    if not PY2:
        text = text.encode('utf-8')
    bytes_text = <bytes>text
    if outline_width:
        TTF_SetFontOutline(font, outline_width)
    TTF_SizeUTF8(font, <char *>bytes_text, &w, &h)
    if outline_width:
        TTF_SetFontOutline(font, 0)
    return w, h

def _get_fontdescent(container):
    return TTF_FontDescent(_get_font(container))

def _get_fontascent(container):
    return TTF_FontAscent(_get_font(container))
