#cython: c_string_type=unicode, c_string_encoding=utf8
'''
TODO:
    - ensure that we correctly check allocation
    - remove compat sdl usage (like SDL_SetAlpha must be replaced with sdl 1.3
      call, not 1.2)
'''

include '../../lib/sdl3.pxi'

from kivy.core.image import ImageData

cdef dict sdl3_cache = {}
cdef list sdl3_cache_order = []

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
        self.surface = SDL_CreateSurface(
            w,
            h,
            SDL_GetPixelFormatForMasks(
                32, 0x000000FF, 0x0000FF00, 0x00FF0000, 0xFF000000
            ),
        )

    def __dealloc__(self):
        if self.surface != NULL:
            SDL_DestroySurface(self.surface)
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

        c.a = oc.a = 255
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

        direction = container.options['font_direction']
        if direction == 'ltr':
            TTF_SetFontDirection(font, TTF_DIRECTION_LTR)
        elif direction == 'rtl':
            TTF_SetFontDirection(font, TTF_DIRECTION_RTL)
        elif direction == 'ttb':
            TTF_SetFontDirection(font, TTF_DIRECTION_TTB)
        elif direction == 'btt':
            TTF_SetFontDirection(font, TTF_DIRECTION_BTT)

        TTF_SetFontScript(font, TTF_StringToTag(container.options["font_script_name"]))

        if outline_width:
            TTF_SetFontOutline(font, outline_width)
            oc.r = <int>(outline_color[0] * 255)
            oc.g = <int>(outline_color[1] * 255)
            oc.b = <int>(outline_color[2] * 255)
            st = (
                TTF_RenderText_Blended(font, <char *>bytes_text, 0, oc)
                if container.options['font_blended']
                else TTF_RenderText_Blended(font, <char *>bytes_text, 0, oc)
                )
            TTF_SetFontOutline(font, 0)
        else:
            st = (
                TTF_RenderText_Blended(font, <char *>bytes_text, 0, c)
                if container.options['font_blended']
                else TTF_RenderText_Solid(font, <char *>bytes_text, 0, c)
                )
        if st == NULL:
            return
        if outline_width:
            fgst = (
                TTF_RenderText_Blended(font, <char *>bytes_text, 0, c)
                if container.options['font_blended']
                else TTF_RenderText_Solid(font, <char *>bytes_text, 0, c)
                )
            if fgst == NULL:
                SDL_DestroySurface(st)
                return
            fgr.x = outline_width
            fgr.y = outline_width
            fgr.w = fgst.w
            fgr.h = fgst.h
            SDL_SetSurfaceBlendMode(fgst, SDL_BLENDMODE_BLEND)
            SDL_BlitSurface(fgst, NULL, st, &fgr)
            SDL_DestroySurface(fgst)

        r.x = x
        r.y = y
        r.w = st.w
        r.h = st.h
        SDL_SetSurfaceAlphaMod(st, <int>(color[3] * 255))
        if container.options['line_height'] < 1:
            """
            We are using SDL_BLENDMODE_BLEND only when line_height < 1 as a workaround.
            Previously, We enabled SDL_BLENDMODE_BLEND also for text w/ line_height >= 1,
            but created an unexpected behavior (See PR #6507 and issue #6508).
            """
            SDL_SetSurfaceBlendMode(st, SDL_BLENDMODE_BLEND)
        else:
            SDL_SetSurfaceBlendMode(st, SDL_BLENDMODE_NONE)
        SDL_BlitSurface(st, NULL, self.surface, &r)
        SDL_DestroySurface(st)

    def get_data(self):
        cdef int datalen = self.surface.w * self.surface.h * 4
        cdef bytes pixels = (<char *>self.surface.pixels)[:datalen]
        data = ImageData(self.w, self.h, 'rgba', pixels)
        return data


cdef TTF_Font *_get_font(self) except *:
    cdef TTF_Font *fontobject = NULL
    cdef _TTFContainer ttfc
    cdef char *error
    cdef str s_error
    cdef bytes bytes_fontname

    # fast path
    fontid = self._get_font_id()
    if fontid in sdl3_cache:
        ttfc = sdl3_cache[fontid]
        return ttfc.font

    # ensure ttf is init.
    if not TTF_WasInit():
        TTF_Init()

    # try first the file if it's a filename
    fontname = self.options['font_name_r']
    bytes_fontname = <bytes>fontname.encode('utf-8')
    ext = fontname.rsplit('.', 1)
    if len(ext) == 2:
        # try to open the font if it has an extension
        fontobject = TTF_OpenFont(bytes_fontname,
                                  int(self.options['font_size']))
    # fallback to search a system font
    if fontobject == NULL:
        s_error = SDL_GetError()
        raise ValueError('{}: for font {}'.format(s_error, fontname))

    # set underline and strikethrough style
    style = TTF_STYLE_NORMAL
    if self.options['underline']:
        style = style | TTF_STYLE_UNDERLINE
    if self.options['strikethrough']:
        style = style | TTF_STYLE_STRIKETHROUGH
    TTF_SetFontStyle(fontobject, style)

    sdl3_cache[fontid] = ttfc = _TTFContainer()
    ttfc.font = fontobject
    sdl3_cache_order.append(fontid)

    # to prevent too much file open, limit the number of opened fonts to 64

    while len(sdl3_cache_order) > 64:
        popid = sdl3_cache_order.pop(0)
        ttfc = sdl3_cache[popid]
        del sdl3_cache[popid]

    ttfc = sdl3_cache[fontid]

    return ttfc.font

cpdef _get_tight_extents(container, text):
    cdef TTF_Font *font = _get_font(container)
    outline_width = container.options['outline_width']
    if font == NULL:
        return 0, 0

    if outline_width:
        TTF_SetFontOutline(font, outline_width)

    cdef int min_y = 0, max_y = 0, total_width = 0
    cdef int minx, maxx, miny, maxy, advance
    cdef bint first_char = True
    cdef int ascent = TTF_GetFontAscent(font)  # Get baseline reference

    text = text.encode('utf-8')

    # Iterate through each character
    for char in text.decode('utf-8'):
        char_code = ord(char)

        if TTF_GetGlyphMetrics(font, char_code, &minx, &maxx, &miny, &maxy, &advance):
            total_width += advance

            # Convert glyph coordinates to absolute coordinates from baseline
            abs_miny = ascent - maxy
            abs_maxy = ascent - miny

            if first_char:
                min_y = abs_miny
                max_y = abs_maxy
                first_char = False
            else:
                min_y = min(min_y, abs_miny)
                max_y = max(max_y, abs_maxy)

    tight_height = max_y - min_y

    # Store the baseline offset for positioning
    container._baseline_offset = min_y

    if outline_width:
        TTF_SetFontOutline(font, 0)

    return total_width, tight_height


def _get_extents(container, text):
    cdef TTF_Font *font = _get_font(container)
    cdef int w, h
    outline_width = container.options['outline_width']
    if font == NULL:
        return 0, 0
    text = text.encode('utf-8')
    bytes_text = <bytes>text
    if outline_width:
        TTF_SetFontOutline(font, outline_width)
    TTF_GetStringSize(font, <char *>bytes_text, 0, &w, &h)
    if outline_width:
        TTF_SetFontOutline(font, 0)
    return w, h

def _get_fontdescent(container):
    return TTF_GetFontDescent(_get_font(container))

def _get_fontascent(container):
    return TTF_GetFontAscent(_get_font(container))
