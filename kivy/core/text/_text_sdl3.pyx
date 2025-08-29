#cython: c_string_type=unicode, c_string_encoding=utf8
'''
TODO:
    - ensure that we correctly check allocation
    - remove compat sdl usage (like SDL_SetAlpha must be replaced with sdl 1.3
      call, not 1.2)
'''

include '../../lib/sdl3.pxi'

from kivy.core.image import ImageData
from kivy.logger import Logger

cdef dict sdl3_cache = {}
cdef list sdl3_cache_order = []

cdef class _TTFContainer:
    cdef TTF_Font* font
    cdef list fallback_fonts
    
    def __cinit__(self):
        self.font = NULL
        self.fallback_fonts = []
    
    def __dealloc__(self):
        # Clean up fallback fonts first
        cdef _TTFContainer fallback_container
        for fallback_container in self.fallback_fonts:
            if fallback_container.font != NULL:
                TTF_CloseFont(fallback_container.font)
                fallback_container.font = NULL
        self.fallback_fonts.clear()
        
        if self.font != NULL:
            TTF_CloseFont(self.font)
            self.font = NULL

    cpdef add_fallback_font(self, fallback_fontname, fallback_size=None):
        """Add a fallback font to this font container"""
        cdef TTF_Font *fallback_fontobject = NULL
        cdef _TTFContainer fallback_ttfc
        cdef bytes bytes_fallback_fontname
        
        if not TTF_WasInit():
            TTF_Init()
            
        # Use same size as main font if not specified
        font_size = fallback_size if fallback_size is not None else self.get_font_size()
        
        bytes_fallback_fontname = <bytes>fallback_fontname.encode('utf-8')
        fallback_fontobject = TTF_OpenFont(bytes_fallback_fontname, font_size)
        
        if fallback_fontobject == NULL:
            s_error = SDL_GetError()
            raise ValueError('Failed to load fallback font {}: {}'.format(fallback_fontname, s_error))
        
        # Add fallback to main font
        if not TTF_AddFallbackFont(self.font, fallback_fontobject):
            TTF_CloseFont(fallback_fontobject)
            s_error = SDL_GetError()
            raise ValueError('Failed to add fallback font: {}'.format(s_error))
        
        # Store in container for cleanup
        fallback_ttfc = _TTFContainer()
        fallback_ttfc.font = fallback_fontobject
        self.fallback_fonts.append(fallback_ttfc)
        
        return True
    
    cpdef get_font_size(self):
        """Get the font size from the main font"""
        if self.font != NULL:
            return TTF_GetFontSize(self.font)
        return 0


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
    
    # Add fallback fonts if specified in options
    if 'fallback_fonts' in self.options and self.options['fallback_fonts']:
        for fallback_font in self.options['fallback_fonts']:
            try:
                ttfc.add_fallback_font(fallback_font)
                Logger.debug(f"Text: Fallback font '{fallback_font}' added to base font '{fontname}'")
            except ValueError as e:
                # Log warning but continue - fallback fonts are optional
                Logger.error(f"Text: Could not load fallback font {fallback_font}: {e}")
    
    sdl3_cache_order.append(fontid)

    # to prevent too much file open, limit the number of opened fonts to 64
    while len(sdl3_cache_order) > 64:
        popid = sdl3_cache_order.pop(0)
        ttfc = sdl3_cache[popid]
        del sdl3_cache[popid]

    ttfc = sdl3_cache[fontid]
    return ttfc.font


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
