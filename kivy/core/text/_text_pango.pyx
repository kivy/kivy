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

# Map text direction to pango constant - neutral is considered auto, anything
# else will call pango_layout_set_auto_dir(the_layout, FALSE)
cdef dict kivy_pango_text_direction = {
    'ltr': PANGO_DIRECTION_LTR,
    'rtl': PANGO_DIRECTION_RTL,
    'weak_ltr': PANGO_DIRECTION_WEAK_LTR,
    'weak_rtl': PANGO_DIRECTION_WEAK_RTL,
    'neutral': PANGO_DIRECTION_NEUTRAL,
    'auto': PANGO_DIRECTION_NEUTRAL}


# Fontconfig and pango structures (one per loaded font). Can't use
# ctypedef struct here, because that won't fit in the cache dict
cdef class ContextContainer:
    cdef PangoContext *context
    cdef PangoFontMap *fontmap
    cdef PangoFontDescription *fontdesc
    cdef PangoFontMetrics *metrics
    cdef PangoLanguage *metrics_lang # do not free, see docs
    cdef PangoLayout *layout
    cdef FcConfig *fc_config

    # Note: calling a method from __dealloc__ can lead to revived object
    def __dealloc__(self):
        if self.metrics:
            pango_font_metrics_unref(self.metrics)
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
cdef inline _add_pango_cache(unicode fontid, ContextContainer cc):
    global kivy_pango_cache, kivy_pango_cache_order

    cdef unicode popid
    while len(kivy_pango_cache_order) >= 64:
        popid = kivy_pango_cache_order.pop(0)
        del kivy_pango_cache[popid]

    kivy_pango_cache[fontid] = cc
    kivy_pango_cache_order.append(fontid)


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
        Logger.warn("_text_pango: Error loadinging font '{}'".format(filename))
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

    # Finally create our pango context from the fontmap
    cc.context = pango_font_map_create_context(cc.fontmap)
    if not cc.context:
        Logger.warn("_text_pango: Could not create pango context")
        return

    # Configure the context's base direction. If user specified something
    # explicit, force it. Otherwise (auto/neutral), let pango decide.
    # FIXME: add text_direction externally so it's available.
    cdef PangoDirection text_dir = kivy_pango_text_direction.get(
            options.get('text_direction', 'neutral'), PANGO_DIRECTION_NEUTRAL)
    pango_context_set_base_dir(cc.context, text_dir)

    # FIXME: pango_language_from_string(kivylabel.text_language)
    # FIXME: cc.metrics_pango_scale needed?
    cc.metrics_lang = pango_language_get_default()
    cc.metrics = pango_context_get_metrics(cc.context, cc.fontdesc,
                                           pango_language_get_default())
    if not cc.metrics:
        Logger.warn("_text_pango: Could not get context metrics")
        return

    # Create layout from context
    cc.layout = pango_layout_new(cc.context)
    if not cc.layout:
        Logger.warn("_text_pango: Could not create pango layout")
        return

    # If autodir is false, the context's base direction is used (set above)
    if text_dir == PANGO_DIRECTION_NEUTRAL:
        pango_layout_set_auto_dir(cc.layout, TRUE)
    else:
        pango_layout_set_auto_dir(cc.layout, FALSE)

    # The actual font size is specified in pango markup, and the
    # actual font is whatever TTF is loaded in this context. This
    # may not be needed at all.
    cc.fontdesc = pango_font_description_from_string("Arial")
    pango_layout_set_font_description(cc.layout, cc.fontdesc)

    # FIXME: does this need to change w/label settings?
    #pango_layout_set_alignment(cc.layout, PANGO_ALIGN_LEFT)
    #pango_layout_set_spacing(cc.layout, n)

    _add_pango_cache(fontid, cc)
    return cc


# Renders the pango layout to a grayscale bitmap, and blits RGBA at x, y
@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
@cython.nonecheck(False)
cdef _render_context(ContextContainer cc, unsigned char *dstbuf,
                     int x, int y, int final_w, int final_h,
                     unsigned char textcolor[]):
    if not dstbuf or final_w <= 0 or final_h <= 0 or x > final_w or y > final_h:
        Logger.warn('_text_pango: Invalid blit: final={}x{} x={} y={}'
                    .format(final_w, final_h, x, y))
        return

    # Note, w/h refers to the current subimage size, final_w/h is end result
    cdef int w, h
    pango_layout_get_pixel_size(cc.layout, &w, &h)
    if w <= 0 or h <= 0 or x + w > final_w or y + h > final_h:
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
        Logger.warn('_text_pango: Ignoring out of bounds blit: final={}x{} '
                    'x={} y={} w={} h={} maxpos={}'.format(
                    final_w, final_h, x, y, w, h, maxpos))
        return

    with nogil:
        # Prepare ft2 bitmap for pango's grayscale data
        FT_Bitmap_Init(&bitmap)
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
        # /nogil blit


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

        # Set markup, this could use kivylabel.options + attrs
        markup = <bytes>text.encode('UTF-8')
        pango_layout_set_markup(cc.layout, markup, len(markup))

        # Kivy normalized text color -> 0-255 rgba
        cdef unsigned char textcolor[4]
        textcolor[:] = [ min(255, int(c * 255)) for c in kivylabel.options['color'] ]

        # Finally render the layout and blit it to self.pixels
        _render_context(cc, self.pixels, x, y, self.w, self.h, textcolor)
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
    cdef ContextContainer cc = _get_context_container(kivylabel)
    cdef int w, h
    if not cc:
        Logger.warn('_text_pango: Could not get container for extents: {}'
                    .format(kivylabel.options['font_name_r']))
        return 0, 0

    markup = <bytes>text.encode('UTF-8')
    pango_layout_set_markup(cc.layout, markup, len(markup))
    pango_layout_get_pixel_size(cc.layout, &w, &h)
    return w, h


def kpango_get_metrics(kivylabel):
    cdef ContextContainer cc = _get_context_container(kivylabel)
    if not cc:
        Logger.warn('_text_pango: Could not get container for metrics: {}'
                    .format(kivylabel.options['font_name_r']))
        return (0, 0)

    # FIXME: pango_language_from_string(kivylabel.text_language)
    cdef PangoLanguage *lang = pango_language_get_default()
    if lang != cc.metrics_lang:
        if cc.metrics:
            pango_font_metrics_unref(cc.metrics)
        cc.metrics = pango_context_get_metrics(cc.context, cc.fontdesc, lang)
        if cc.metrics:
            cc.metrics_lang = lang

    if not cc.metrics:
        Logger.warn('_text_pango: Could not get context metrics: {}'
                    .format(kivylabel.options['font_name_r']))
        return (0, 0)

    return (<double>(pango_font_metrics_get_ascent(cc.metrics) / PANGO_SCALE),
            <double>(pango_font_metrics_get_descent(cc.metrics) / PANGO_SCALE))
