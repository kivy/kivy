# NOTE: We could probably use a single global FcConfig, but it's not obvious
# how since adding a font doesn't give you back something that can be directly
# used to render with. Apparently you must look it up via a font description.
# Where do you get that from? I don't know... maybe FcConfigGetFonts then
# pango_fc_font_description_from_pattern(), somehow?
#
# The current implementation uses pango_fc_font_map_set_config() to force the
# loaded TTF to be used, seems to work. As far as I can tell alternative is:
#
#     cdef FcConfig *oldconfig = FcConfigGetCurrent()
#     FcConfigSetCurrent(context.fc_config)
#     <-- render -->
#     FcConfigSetCurrent(oldconfig)
#

cimport cython
from libc.stdint cimport uint32_t
from libc.string cimport memset
from cpython.mem cimport PyMem_Malloc, PyMem_Free

include "../../lib/pangoft2.pxi"
from kivy.logger import Logger
from kivy.core.image import ImageData

# Cached contexts; dict key + list value is font filename ("font_name_r")
# Dict values are ContextContainer instances, one for each font.
cdef dict kivy_pango_cache = {}
cdef list kivy_pango_cache_order = []

# Map text direction to pango constant, auto resets context direction to
# weak_ltr and enabled pango auto_dir. It doesn't make sense to specify
# neutral as a desired text direction.
cdef dict kivy_pango_text_direction = {
    'ltr': PANGO_DIRECTION_LTR,
    'rtl': PANGO_DIRECTION_RTL,
    'weak_ltr': PANGO_DIRECTION_WEAK_LTR,
    'weak_rtl': PANGO_DIRECTION_WEAK_RTL,
    'auto': PANGO_DIRECTION_NEUTRAL}


# Fontconfig and pango structures (one per loaded font). Can't use
# ctypedef struct here, because that won't fit in the cache dict
cdef class ContextContainer:
    cdef FcConfig *fc_config
    cdef PangoLayout *layout
    cdef PangoContext *context
    cdef PangoFontMap *fontmap
    cdef PangoFontDescription *fontdesc

    # lang + metric_font_size determine validity of ascent/descent.
    # (lang is also used to set a text attribute)
    cdef PangoLanguage *lang # do not free, see docs
    cdef int metrics_font_size
    cdef double ascent
    cdef double descent

    # Note: calling a method from __dealloc__ can lead to revived object
    def __dealloc__(self):
        if self.fontdesc:
            pango_font_description_free(self.fontdesc)
        if self.layout:
            g_object_unref(self.layout)
        if self.context:
            g_object_unref(self.context)
        if self.fontmap:
            g_object_unref(self.fontmap)
        if self.fc_config:
            FcConfigDestroy(self.fc_config)


# Add a contextcontainer to cache + keep max 64 open fonts
cdef inline _add_context_to_cache(unicode fontid, ContextContainer cc):
    global kivy_pango_cache, kivy_pango_cache_order

    cdef unicode popid
    while len(kivy_pango_cache_order) >= 64:
        popid = kivy_pango_cache_order.pop(0)
        del kivy_pango_cache[popid]

    kivy_pango_cache[fontid] = cc
    kivy_pango_cache_order.append(fontid)

# Get PangoLanguage from options
cdef PangoLanguage *_get_kivylabel_options_text_language(dict options):
    txtlang = options['text_language']
    if txtlang:
        if not isinstance(txtlang, bytes):
            txtlang = txtlang.encode('UTF-8')
        return pango_language_from_string(txtlang)
    return pango_language_get_default()


# Configure the context with options from kivylabel
cdef _set_context_options(ContextContainer cc, dict options):
    global kivy_pango_text_direction
    cdef int font_size = int(options['font_size'] * PANGO_SCALE)

    # Underline, strikethrough, OpenType Font features (...) are not part of font
    # description. I'm not 100% sure how this fits together, but apparently none
    # of this impact metrics?
    # FIXME: do we even need a font description??? I'm not sure if metrics will
    #        be correct without it.
    cdef PangoAttrList *attrs = pango_attr_list_new()

    if PANGO_VERSION_CHECK(1, 8, 0):
        pango_attr_list_insert(attrs, pango_attr_size_new_absolute(font_size))
        pango_font_description_set_absolute_size(cc.fontdesc, font_size)
    else:
        pango_attr_list_insert(attrs, pango_attr_size_new(font_size))
        pango_font_description_set_size(cc.fontdesc, font_size)

    if options['bold']:
        pango_attr_list_insert(attrs, pango_attr_weight_new(PANGO_WEIGHT_BOLD))
        pango_font_description_set_weight(cc.fontdesc, PANGO_WEIGHT_BOLD)
    else:
        pango_font_description_set_weight(cc.fontdesc, PANGO_WEIGHT_NORMAL)

    if options['italic']:
        pango_attr_list_insert(attrs, pango_attr_style_new(PANGO_STYLE_ITALIC))
        pango_font_description_set_style(cc.fontdesc, PANGO_STYLE_ITALIC)
    else:
        pango_font_description_set_style(cc.fontdesc, PANGO_STYLE_NORMAL)

    if options['underline']:
        pango_attr_list_insert(attrs, pango_attr_underline_new(PANGO_UNDERLINE_SINGLE))
    if options['strikethrough']:
        pango_attr_list_insert(attrs, pango_attr_strikethrough_new(1))

    if PANGO_VERSION_CHECK(1, 38, 0) and options['font_features']:
        features = bytes(options['font_features'], encoding='UTF-8')
        pango_attr_list_insert(attrs, pango_attr_font_features_new(features))

    # Text direction
    cdef PangoDirection text_dir = kivy_pango_text_direction.get(
            options.get('text_direction', 'auto'), PANGO_DIRECTION_NEUTRAL)
    if text_dir == PANGO_DIRECTION_NEUTRAL:
        pango_layout_set_auto_dir(cc.layout, TRUE)
        pango_context_set_base_dir(cc.context, PANGO_DIRECTION_WEAK_LTR)
    else:
        # If autodir is false, the context's base direction is used
        pango_layout_set_auto_dir(cc.layout, FALSE)
        pango_context_set_base_dir(cc.context, text_dir)

    # The language tag is not necessarily the same as the
    # one we have cached, or the locale could have changed.
    cdef PangoLanguage *new_lang = _get_kivylabel_options_text_language(options)
    cdef PangoFontMetrics *metrics
    if new_lang != cc.lang or font_size != cc.metrics_font_size:
        cc.lang = new_lang
        cc.metrics_font_size = font_size
        # Get font metrics
        metrics = pango_context_get_metrics(cc.context, cc.fontdesc, cc.lang)
        if metrics:
            cc.ascent = <double>(pango_font_metrics_get_ascent(metrics) / PANGO_SCALE)
            cc.descent = <double>(pango_font_metrics_get_descent(metrics) / PANGO_SCALE)
            pango_font_metrics_unref(metrics)
        else:
            Logger.warn('_text_pango: Could not get font metrics: {}'
                        .format(options['font_name_r']))

    # Finalize
    pango_attr_list_insert(attrs, pango_attr_language_new(cc.lang))
    pango_layout_set_font_description(cc.layout, cc.fontdesc)
    pango_layout_set_attributes(cc.layout, attrs)
    # Layout keeps a ref to attributes now
    pango_attr_list_unref(attrs)
    pango_layout_context_changed(cc.layout)


# NOTE: for future, this applies to font selection, irrelevant with one font
# Or maybe it is relevant, it's not clear. The callback didn't execute with
# null for data/destroy callback. I was planning on testing with flags
# packed in a gpointer, but this is still on todo. If anyone knows more
# about fontconfig and can clarify how this should be done, that'd be great

#cdef _configure_pattern_destroy_data(gpointer data):
#    print("_configure_pattern_destroy_data()!")

#cdef _configure_pattern_callback(FcPattern *pattern, gpointer data):
#    cdef unsigned int flags = GPOINTER_TO_UINT(data)
#    print("_configure_pattern_callback()!")
#    FcPatternDel(pattern, FC_HINTING)
#    FcPatternAddBool(pattern, FC_HINTING, ...)
#    FcPatternDel(pattern, FC_AUTOHINT)
#    FcPatternAddBool(pattern, FC_AUTOHINT, ...)
#    FcPatternDel(pattern, FC_HINT_STYLE)
#    FcPatternAddInteger(pattern, FC_HINT_STYLE, ...)
#    FcPatternDel(pattern, FC_ANTIALIAS)
#    FcPatternAddBool(pattern, FC_ANTIALIAS, ...)


# Creates a ContextContainer for the font_name_r of the label
cdef _get_context_container(kivylabel):
    global kivy_pango_text_direction
    cdef dict options = kivylabel.options
    cdef unicode fontid = <unicode>options['font_name_r']
    if fontid in kivy_pango_cache:
        return kivy_pango_cache.get(fontid)

    # Creat a new context
    cdef ContextContainer cc = ContextContainer()

    # Create blank FcConfig (fontconfig), and load the TTF file
    cc.fc_config = FcInitLoadConfig()
    cdef bytes filename = options['font_name_r'].encode('UTF-8')
    if FcConfigAppFontAddFile(cc.fc_config, <FcChar8 *>filename) == FcFalse:
        Logger.warn("_text_pango: Error loading font '{}'".format(filename))
        return

    # Create a blank font map and assign the config from above (one TTF file)
    cc.fontmap = pango_ft2_font_map_new()
    if not cc.fontmap:
        Logger.warn("_text_pango: Could not create new font map")
        return
    pango_fc_font_map_set_config(PANGO_FC_FONT_MAP(cc.fontmap), cc.fc_config)

    # FIXME: should we configure this?
    #pango_ft2_font_map_set_resolution(cc.fontmap, n, n)

    # FIXME: This may become relevant, leaving for now
    #cc.callback_data_ptr = GUINT_TO_POINTER(flags)
    #pango_ft2_font_map_set_default_substitute(
    #                PANGO_FT2_FONT_MAP(cc.fontmap),
    #                &_configure_pattern_callback,
    #                cc.callback_data_ptr,
    #                &_configure_pattern_destroy_data)

    # Create pango context from the fontmap
    cc.context = pango_font_map_create_context(cc.fontmap)
    if not cc.context:
        Logger.warn("_text_pango: Could not create pango context")
        return

    # Create pango layout from context
    cc.layout = pango_layout_new(cc.context)
    if not cc.layout:
        Logger.warn("_text_pango: Could not create pango layout")
        return

    # We use the context's font description, because it makes it easy
    # to get the metrics with pango_context_get_metrics(). It's possible
    # we could do this with PangoLayoutLine instead. The font description
    # is updated each time the font is used.
    # FIXME: OpenType font features are not part of font description. Do
    #        they not matter for metrics? This needs research/confirmation.
    cc.fontdesc = pango_font_description_new()

    _set_context_options(cc, options)
    _add_context_to_cache(fontid, cc)
    return cc


# Renders the pango layout to a grayscale bitmap, and blits RGBA at x, y
@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
cdef void _render_context(ContextContainer cc, unsigned char *dstbuf,
                     int x, int y, int final_w, int final_h,
                     unsigned char textcolor[]) nogil:
    if not dstbuf or final_w <= 0 or final_h <= 0 or x > final_w or y > final_h:
        with gil:
            Logger.warn('_text_pango: Invalid blit: final={}x{} x={} y={}'
                        .format(final_w, final_h, x, y))
            return

    # Note, w/h refers to the current subimage size, final_w/h is end result
    cdef int w, h
    pango_layout_get_pixel_size(cc.layout, &w, &h)
    if w <= 0 or h <= 0 or x + w > final_w or y + h > final_h:
        with gil:
            Logger.warn('_text_pango: Invalid blit: final={}x{} x={} y={} w={} h={}'
                        .format(final_w, final_h, x, y, w, h))
            return

    cdef FT_Bitmap bitmap
    cdef int xi, yi
    cdef unsigned char graysrc
    cdef unsigned long grayidx
    cdef unsigned long yi_w
    cdef unsigned long offset
    cdef unsigned long offset_fixed = x + (y * final_w)
    cdef unsigned long offset_yi = final_w - w
    cdef unsigned long maxpos = final_w * final_h

    # Sanity check that we don't go out of bounds here, should not happen
    if offset_fixed + ((h-1)*offset_yi) + ((h-1)*w) + w - 1 > maxpos:
        with gil:
            Logger.warn('_text_pango: Ignoring out of bounds blit: final={}x{} '
                        'x={} y={} w={} h={} maxpos={}'.format(
                        final_w, final_h, x, y, w, h, maxpos))
            return

    # Prepare ft2 bitmap for pango's grayscale data
    # In ft2 2.5 and older, function is called FT_Bitmap_New
    if FREETYPE_MAJOR == 2:
        if FREETYPE_MINOR <= 5:
            FT_Bitmap_New(&bitmap)
        else:
            FT_Bitmap_Init(&bitmap)
    else:
        with gil:
            Logger.warn('_text_pango: Unsupported FreeType library version. '
                        'Abort rendering.')
            return

    bitmap.width = w
    bitmap.rows = h
    bitmap.pitch = w # 1-byte grayscale
    bitmap.pixel_mode = FT_PIXEL_MODE_GRAY # no BGRA in pango (ft2 has it)
    bitmap.num_grays = 256
    bitmap.buffer = <unsigned char *>g_malloc0(w * h)
    if not bitmap.buffer:
        with gil:
            Logger.warn('_text_pango: Could not malloc FT_Bitmap.buffer')
            return

    # Render the layout as 1 byte per pixel grayscale bitmap
    # FIXME: does render_layout_subpixel() do us any good?
    pango_ft2_render_layout(&bitmap, cc.layout, 0, 0)

    # Blit the bitmap as RGBA at x, y in dstbuf (w/h is the ft2 bitmap)
    for yi in range(0, h):
        offset = offset_fixed + (yi * offset_yi)
        yi_w = yi * w

        # FIXME: Handle big endian - either use variable shifts here, or
        # return as abgr + handle elsewhere
        for xi in range(0, w):
            grayidx = yi_w + xi
            graysrc = (bitmap.buffer)[grayidx]
            (<uint32_t *>dstbuf)[offset + grayidx] = (
                    (((textcolor[0] * graysrc) / 255)) |
                    (((textcolor[1] * graysrc) / 255) << 8) |
                    (((textcolor[2] * graysrc) / 255) << 16) |
                    (((textcolor[3] * graysrc) / 255) << 24) )
    g_free(bitmap.buffer)
    # /nogil _render_context()


cdef class KivyPangoRenderer:
    # w, h is the final bitmap size, drawn by 1+ render() calls in *pixels
    cdef int w, h
    cdef int canary, rdrcount
    cdef unsigned char *pixels

    def __cinit__(self, int w, int h):
        self.w = w
        self.h = h
        self.canary = 0
        self.rdrcount = 0
        self.pixels = <unsigned char *>PyMem_Malloc(w * h * 4)
        if self.pixels:
            memset(self.pixels, 0, w * h * 4)

    # Free pixels if dealloc'd before get_ImageData(), this is just a failsafe,
    # should not happen during normal operations.
    def __dealloc__(self):
        if not self.canary and self.pixels:
            Logger.warn("_text_pango: Dead canary in __dealloc__()")
            PyMem_Free(self.pixels)

    # Kivy's markup system breaks labels down to smaller chunks and render
    # separately. In that case, we get several calls to render() with misc
    # options and x/y positions. End result is stored in self.pixels.
    def render(self, kivylabel, text, x, y):
        if not self.pixels:
            Logger.warn('_text_pango: render() called, but self.pixels is NULL')
            return
        cdef ContextContainer cc = _get_context_container(kivylabel)
        if not cc:
            Logger.warn('_text_pango: Could not get context container, aborting')
            return

        _set_context_options(cc, kivylabel.options)

        if isinstance(text, bytes):
            utf = text
        else:
            utf = <bytes>text.encode('UTF-8')
        pango_layout_set_text(cc.layout, utf, len(utf))

        # Kivy normalized text color -> 0-255 rgba for nogil
        cdef unsigned char textcolor[4]
        color = kivylabel.options['color']
        textcolor[0] = min(255, int(color[0] * 255))
        textcolor[1] = min(255, int(color[1] * 255))
        textcolor[2] = min(255, int(color[2] * 255))
        if len(color) > 3:
            textcolor[3] = min(255, int(color[3] * 255))
        else:
            textcolor[3] = 1

        # Finally render the layout and blit it to self.pixels
        cdef int xx = x
        cdef int yy = y
        with nogil:
            _render_context(cc, self.pixels, xx, yy, self.w, self.h, textcolor)
        self.rdrcount += 1

    # Return ImageData instance with the rendered pixels
    def get_ImageData(self):
        if not self.pixels:
            Logger.warn('_text_pango: get_ImageData() self.pixels == NULL')
            return
        if not self.rdrcount:
            Logger.warn('_text_pango: get_ImageData() without render() call')
            return
        if self.canary:
            Logger.warn("_text_pango: Dead canary in get_ImageData()")
            return
        self.canary = 1

        try:
            b_pixels = <bytes>self.pixels[:self.w * self.h * 4]
            return ImageData(self.w, self.h, 'rgba', b_pixels)
        finally:
            PyMem_Free(self.pixels)


def kpango_get_extents(kivylabel, text):
    if not text:
        return 0, 0
    cdef dict options = kivylabel.options
    cdef ContextContainer cc = _get_context_container(kivylabel)
    if not cc:
        Logger.warn('_text_pango: Could not get container for extents: {}'
                    .format(options['font_name_r']))
        return 0, 0

    _set_context_options(cc, options)

    if isinstance(text, bytes):
        utf = text
    else:
        utf = <bytes>text.encode('UTF-8')
    pango_layout_set_text(cc.layout, utf, len(utf))

    cdef int w, h
    pango_layout_get_pixel_size(cc.layout, &w, &h)
    return w, h


# FIXME: does weight/style need to invalidate ascent/descent?
def kpango_get_ascent(kivylabel):
    cdef dict options = kivylabel.options
    cdef ContextContainer cc = _get_context_container(kivylabel)
    if not cc:
        Logger.warn('_text_pango: Could not get container for ascent: {}'
                    .format(options['font_name_r']))
        return 0

    cdef PangoLanguage *new_lang = _get_kivylabel_options_text_language(options)
    cdef int new_font_size = int(options['font_size'] * PANGO_SCALE)
    if new_lang != cc.lang or new_font_size != cc.metrics_font_size:
        _set_context_options(cc, options)
    return cc.ascent


# FIXME: does weight/style need to invalidate ascent/descent?
def kpango_get_descent(kivylabel):
    cdef dict options = kivylabel.options
    cdef ContextContainer cc = _get_context_container(kivylabel)
    if not cc:
        Logger.warn('_text_pango: Could not get container for descent: {}'
                    .format(options['font_name_r']))
        return 0

    cdef PangoLanguage *new_lang = _get_kivylabel_options_text_language(options)
    cdef int new_font_size = int(options['font_size'] * PANGO_SCALE)
    if new_lang != cc.lang or new_font_size != cc.metrics_font_size:
        _set_context_options(cc, options)
    return cc.descent
