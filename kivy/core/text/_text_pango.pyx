# TODO:
# - We only render lines, can we use line-level pango layout functionality??
# - Support style/weight/different underlines and fix metrics
# - Figure out way to constant fold PANGO_VERSION_CHECK/avoid warning
cimport cython
from libc.stdint cimport uint32_t
from libc.string cimport memset
from cpython.mem cimport PyMem_Malloc, PyMem_Free

include "../../lib/pangoft2.pxi"
from kivy.logger import Logger
from kivy.core.image import ImageData

# Global FreeType2 library instance + state flags. This is used for detecting
# font family names, since FcConfigAppAddFontFile() doesn't give us a ref to
# the font. So we load the file using FreeType2 to query the resulting face
# using FontConfig (since we depend on it anyway, this is very cumbersome
# to do with ft2 directly due to vast number of encodings + huge tables etc)
cdef FT_Library kivy_ft_library
cdef int kivy_ft_init
cdef int kivy_ft_error

# Since fontfiles can be reused in different contexts (or purged), cache family
# name(s) so the file doesn't have to be opened twice for every future load to
# a different context.
cdef dict kivy_fontfamily_cache = {}
cdef list kivy_fontfamily_cache_order = []

# Cache of isolated font contexts, ie with a single font loaded and no
# fallback support. This is backwards-compatible with existing Kivy text
# providers (we will draw with the user-specified font file, no risk
# of conflict)
cdef dict kivy_isolated_cache = {}
cdef list kivy_isolated_cache_order = []

# Fallback contexts have one or more font files loaded, and are at risk of
# family name collision (Pango handles fallback)
# FIXME: These are not purged, maybe they should be... ?
cdef dict kivy_fallback_cache = {}


# Used for fontfamily/isolated caches
cdef inline void _purge_cache(dict cache, list order, int limit):
    cdef bytes popid
    while len(order) >= limit:
        popid = order.pop(0)
        del cache[popid]


# Map text direction to pango constant, auto resets context direction to
# weak_ltr and enabled pango auto_dir. It doesn't make sense to specify
# neutral as a desired text direction.
cdef dict kivy_pango_base_direction = {
    'ltr': PANGO_DIRECTION_LTR,
    'rtl': PANGO_DIRECTION_RTL,
    'weak_ltr': PANGO_DIRECTION_WEAK_LTR,
    'weak_rtl': PANGO_DIRECTION_WEAK_RTL}

# Inverse, for kpango_find_base_dir
cdef dict pango_kivy_base_direction = {
    PANGO_DIRECTION_LTR: 'ltr',
    PANGO_DIRECTION_RTL: 'rtl',
    PANGO_DIRECTION_WEAK_LTR: 'weak_ltr',
    PANGO_DIRECTION_WEAK_RTL: 'weak_rtl'}


# Helper for label's string options
cdef inline bytes _byte_option(opt):
    if opt is None:
        return
    if isinstance(opt, bytes):
        return opt
    return opt.encode('UTF-8')


# Get PangoDirection from options
cdef inline PangoDirection _get_options_base_direction(dict options):
    global kivy_pango_base_direction
    cdef bytes direction = _byte_option(options['base_direction'])
    return kivy_pango_base_direction.get(direction, PANGO_DIRECTION_NEUTRAL)


# Get PangoLanguage from options
cdef inline PangoLanguage *_get_options_text_language(dict options):
    cdef bytes txtlang = _byte_option(options['text_language'])
    if txtlang:
        return pango_language_from_string(txtlang)
    return pango_language_get_default()


# Fontconfig and pango structures (one per font context). Instances of
# this class are stored in the kivy_pango_isolated_cache (no font_context)
# and kivy_pango_fallback_cache.
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

    # Set of options['font_name_r'] filename strings loaded to fc_config
    cdef set loaded_fonts
    def __cinit__(self):
        self.loaded_fonts = set()

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


# Return a string that can be used to (hopefully) render with the font
# file later (font family name, or as close to it as we can get).
# This could be done with pango_fontmap_list_families, but it would
# require a separate FcConfig + adding file, etc. It doesn't seem like
# we can rely on the returned order to avoid double-scanning. I assume
# this is the most lightweight way to do it, but...
cdef bytes _ft2_scan_fontfile_to_fontfamily_cache(fontfile):
    global kivy_fontfamily_cache, kivy_fontfamily_cache_order
    global kivy_ft_library, kivy_ft_init, kivy_ft_error
    if not kivy_ft_init:
        if kivy_ft_error:
            return
        kivy_ft_error = FT_Init_FreeType(&kivy_ft_library)
        if kivy_ft_error:
            Logger.warn("_text_pango: Failed to initialize FreeType2 "
                        "library. Error code: {}".format(kivy_ft_error))
            return
        kivy_ft_init = 1
    # Return from cache if this file has been loaded before
    cdef bytes filename = _byte_option(fontfile)
    if filename in kivy_fontfamily_cache:
        return kivy_fontfamily_cache[filename]

    # Load font file and get family name(s) for use in font description.
    # (there is no way to resolve conflicts for same family name)
    cdef FT_Face face
    cdef FT_Error error = FT_New_Face(kivy_ft_library, filename, 0, &face)
    if error:
        Logger.warn("_text_pango: Detecting family for '{}' failed: "
                    "Could not load/create face 0. Error code: ".format(filename, error))
        return
    unique = set()
    cdef bytes order = b''
    cdef int e = 0
    cdef char *family
    cdef FcResult result
    cdef FcPattern *pat = FcFreeTypeQueryFace(face, <FcChar8 *>filename, 0, NULL)
    while True:
        if FcResultMatch == FcPatternGetString(pat, FC_FAMILY, e, <FcChar8 **>&family):
            if family and family not in unique:
                order += len(order) and b','+family or family
                unique.update([family])
                # FIXME: Enumerate multiple families, if present. I deactivated
                #        this because support for setting a comma-delimited list in
                #        font description / layout attr is a bit unclear, not sure
                #        if it can lead to problems, versions, etc.
                break  # Remove when clarified
            e += 1
        else:
            break
    if not order:
        order = FT_Get_Postscript_Name(face)
        if order:
            # This is not supposed to happen since query falls back to it
            Logger.warn("_text_pango: Detecting family for '{}' warning: "
                        "Query failed, but found PostScript name: {}."
                        .format(filename, order))
        else:
            Logger.warn("_text_pango: Detecting family for '{}' warning: "
                        "No family name found in font, using Sans.".format(filename))
            order = b"Sans"

    FcPatternDestroy(pat)
    if FT_Done_Face(face) != 0:
        Logger.warn("_text_pango: Detecting family for '{}' warning: "
                    "Could not clean up ft2 font face.".format(filename))

    _purge_cache(kivy_fontfamily_cache, kivy_fontfamily_cache_order, 200)
    kivy_fontfamily_cache[filename] = order
    kivy_fontfamily_cache_order.append(filename)
    return order


# Configure ContextContainer with options from kivylabel.
# Underline, strikethrough, OpenType Font features (...) are not part of font
# description. I'm not 100% sure how this fits together, but apparently none
# of this impact metrics?
# FIXME: Figure out the minimum needed for fontdesc/attrs here
cdef _set_context_options(ContextContainer cc, dict options):
    global kivy_fontfamily_cache
    cdef PangoAttrList *attrs = pango_attr_list_new()
    cdef bytes font_name_r = _byte_option(options['font_name_r'])
    cdef bytes font_context = _byte_option(options['font_context'])

    # Set the current FcConfig, needed for Pango to see the contained fonts.
    # Versions 1.38+ use a call to pango_fc_font_map_set_config() instead.
    if not PANGO_VERSION_CHECK(1, 38, 0):
        if FcConfigGetCurrent() != cc.fc_config:
            if FcConfigSetCurrent(cc.fc_config) == FcFalse:
                Logger.warn("_text_pango: set_context_options(): Failed to set "
                            "current fc_config for font_name_r='{}', font_context='{}'"
                            .format(font_name_r, font_context))

    # Specify font family for fallback contexts; we don't care for isolated,
    # there is only one font to choose from.
    cdef bytes family_attr = b'Sans'
    if font_context:
        if font_name_r:
            family_attr = kivy_fontfamily_cache.get(font_name_r)
            if not family_attr:  # Purged from cache
                family_attr = _ft2_scan_fontfile_to_fontfamily_cache(font_name_r)
                if not family_attr:  # Warnings issued in function call
                    family_attr = b'Sans'
        elif options['font_name']:
            family_attr = _byte_option(options['font_name'])
        pango_font_description_set_family(cc.fontdesc, family_attr)
        pango_attr_list_insert(attrs, pango_attr_family_new(family_attr))

    cdef int font_size = int(options['font_size'] * PANGO_SCALE)
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

    if PANGO_VERSION_CHECK(1, 38, 0):
        if options['font_features']:
            features = _byte_option(options['font_features'])
            pango_attr_list_insert(attrs, pango_attr_font_features_new(features))

    # Base direction (at the moment, this probably has no impact)
    cdef PangoDirection base_dir = _get_options_base_direction(options)
    if base_dir == PANGO_DIRECTION_NEUTRAL:
        pango_layout_set_auto_dir(cc.layout, TRUE)
        pango_context_set_base_dir(cc.context, PANGO_DIRECTION_WEAK_LTR)
    else:
        # If autodir is false, the context's base direction is used
        pango_layout_set_auto_dir(cc.layout, FALSE)
        pango_context_set_base_dir(cc.context, base_dir)

    # Apply font description to context before getting metrics
    pango_context_set_font_description(cc.context, cc.fontdesc)

    # The language tag is not necessarily the same as the
    # one we have cached, or the locale could have changed.
    cdef PangoLanguage *new_lang = _get_options_text_language(options)
    cdef PangoFontMetrics *metrics
    if new_lang != cc.lang or font_size != cc.metrics_font_size:
        cc.lang = new_lang
        cc.metrics_font_size = font_size
        metrics = pango_context_get_metrics(cc.context, cc.fontdesc, cc.lang)
        if metrics:
            cc.ascent = <double>(pango_font_metrics_get_ascent(metrics) / PANGO_SCALE)
            cc.descent = <double>(pango_font_metrics_get_descent(metrics) / PANGO_SCALE)
            pango_font_metrics_unref(metrics)
        else:
            Logger.warn('_text_pango: Could not get font metrics: {}'
                        .format(options['font_name_r']))

    pango_attr_list_insert(attrs, pango_attr_language_new(cc.lang))
    pango_layout_set_attributes(cc.layout, attrs)
    pango_attr_list_unref(attrs)  # Layout owns it now
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
cdef ContextContainer _get_context_container(dict options):
    global kivy_isolated_cache
    global kivy_isolated_cache_order
    global kivy_fallback_cache

    cdef ContextContainer cc
    cdef bytes font_name_r = _byte_option(options['font_name_r'])
    cdef bytes font_context = _byte_option(options['font_context'])

    # Check for cached context container
    cdef bint creating_new_context = True
    if font_context:
        if font_context in kivy_fallback_cache:
            cc = kivy_fallback_cache[font_context]
            if not font_name_r:
                return kivy_fallback_cache[font_context]
            if font_name_r in cc.loaded_fonts:
                return cc
            creating_new_context = False
            # <-- Pass here == exit early after adding new font to fallback context
        # <-- Pass here == create + cache new fallback context (maybe adding a new font)
    elif not font_name_r:
        raise Exception('_text_pango: Attempt to load empty font_name_r in an'
                        'isolated context. This is not possible.')
    elif font_name_r in kivy_isolated_cache:
        return kivy_isolated_cache[font_name_r]
    # <-- Pass here == create + cache new isolated context

    cdef bytes custom_context_source
    if creating_new_context:
        cc = ContextContainer()
        if font_context:
            if font_context.startswith(b'plain://'):
                cc.fc_config = FcConfigCreate()
            elif font_context.startswith(b'system://'):
                cc.fc_config = FcInitLoadConfigAndFonts()
            elif font_context.startswith('directory://'):
                cc.fc_config = FcInitLoadConfig()
                custom_context_source = font_context[11:]
                if FcConfigAppFontAddDir(cc.fc_config, font_context[11:]) == FcFalse:
                    Logger.warn("_text_pango: Error loading fonts for directory context "
                                "'{}'".format(font_context))
            elif font_context.startswith('fontconfig://'):
                cc.fc_config = FcConfigCreate()
                custom_context_source = font_context[13:]
                if FcTrue != FcConfigParseAndLoad(cc.fc_config, <FcChar8 *>custom_context_source, FcTrue):
                    Logger.warning("_text_pango: Error loading FontConfig configuration"
                                   "for font_context {}: {}".format(font_context, custom_context_source))
                    return
        else:  # normal shared context
            cc.fc_config = FcInitLoadConfig()

    # Add the specified font file to context, if any.
    cdef bytes resolved_families
    if font_name_r:
        if FcConfigAppFontAddFile(cc.fc_config, <FcChar8 *>font_name_r) == FcFalse:
            Logger.warn("_text_pango: Error loading font '{}'".format(font_name_r))
            return
        if font_name_r not in kivy_fontfamily_cache:
            resolved_families = _ft2_scan_fontfile_to_fontfamily_cache(font_name_r)
        cc.loaded_fonts.update([font_name_r])
        if not creating_new_context:
            # Older versions swap the FcConfig in _set_context_options()
            if PANGO_VERSION_CHECK(1, 38, 0):
                pango_fc_font_map_config_changed(PANGO_FC_FONT_MAP(cc.fontmap))
            return cc

    # Create a blank font map and assign the config from above (one TTF file)
    cc.fontmap = pango_ft2_font_map_new()
    if not cc.fontmap:
        Logger.warn("_text_pango: Could not create new font map")
        return

    # In 1.38+ we can do this (+ config_changed above) instead of swapping the
    # current FcConfig each time we use the Pango context
    if PANGO_VERSION_CHECK(1, 38, 0):
        pango_fc_font_map_set_config(PANGO_FC_FONT_MAP(cc.fontmap), cc.fc_config)

    # FIXME: Can we avoid deprecation warning? I guess Cython can't fold this..
    if PANGO_VERSION_CHECK(1, 22, 0):
        cc.context = pango_font_map_create_context(cc.fontmap)
    else:
        cc.context = pango_ft2_font_map_create_context(PANGO_FT2_FONT_MAP(cc.fontmap))

    if not cc.context:
        Logger.warn("_text_pango: Could not create pango context")
        return
    cc.layout = pango_layout_new(cc.context)
    if not cc.layout:
        Logger.warn("_text_pango: Could not create pango layout")
        return

    if not creating_new_context:
        _set_context_options(cc, options)
        return cc
    cc.fontdesc = pango_font_description_new()
    _set_context_options(cc, options)

    # FIXME: This may become relevant, leaving for now
    #pango_ft2_font_map_set_default_substitute(
    #                PANGO_FT2_FONT_MAP(cc.fontmap),
    #                &_configure_pattern_callback,
    #                cc.callback_data_ptr,
    #                &_configure_pattern_destroy_data)

    # Fallback context
    if font_context:
        kivy_fallback_cache[font_context] = cc
        return cc
    # Isolated context
    _purge_cache(kivy_isolated_cache, kivy_isolated_cache_order, 64)
    kivy_isolated_cache[font_name_r] = cc
    kivy_isolated_cache_order.append(font_name_r)
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

# ----------------------------------------------------------------------------
# Public API from this point
# ----------------------------------------------------------------------------
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
        cdef dict options = kivylabel.options
        cdef ContextContainer cc = _get_context_container(options)
        if not cc:
            Logger.warn('_text_pango: Could not get context container, aborting')
            return

        _set_context_options(cc, options)
        cdef bytes utf = _byte_option(text)
        pango_layout_set_text(cc.layout, utf, len(utf))

        # Kivy normalized text color -> 0-255 rgba for nogil
        cdef unsigned char textcolor[4]
        color = options['color']
        textcolor[0] = min(255, int(color[0] * 255))
        textcolor[1] = min(255, int(color[1] * 255))
        textcolor[2] = min(255, int(color[2] * 255))
        if len(color) > 3:
            textcolor[3] = min(255, int(color[3] * 255))
        else:
            textcolor[3] = 255

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
    cdef ContextContainer cc = _get_context_container(options)
    if not cc:
        Logger.warn('_text_pango: Could not get container for extents: {}'
                    .format(options['font_name_r']))
        return 0, 0

    _set_context_options(cc, options)

    cdef bytes utf = _byte_option(text)
    pango_layout_set_text(cc.layout, utf, len(utf))

    cdef int w, h
    pango_layout_get_pixel_size(cc.layout, &w, &h)
    return w, h


# FIXME: does weight/style need to invalidate ascent/descent?
def kpango_get_ascent(kivylabel):
    cdef dict options = kivylabel.options
    cdef ContextContainer cc = _get_context_container(options)
    if not cc:
        Logger.warn('_text_pango: Could not get container for ascent: {}'
                    .format(options['font_name_r']))
        return 0

    cdef PangoLanguage *new_lang = _get_options_text_language(options)
    cdef int new_font_size = int(options['font_size'] * PANGO_SCALE)
    if new_lang != cc.lang or new_font_size != cc.metrics_font_size:
        _set_context_options(cc, options)
    return cc.ascent


# FIXME: does weight/style need to invalidate ascent/descent?
def kpango_get_descent(kivylabel):
    cdef dict options = kivylabel.options
    cdef ContextContainer cc = _get_context_container(options)
    if not cc:
        Logger.warn('_text_pango: Could not get container for descent: {}'
                    .format(options['font_name_r']))
        return 0

    cdef PangoLanguage *new_lang = _get_options_text_language(options)
    cdef int new_font_size = int(options['font_size'] * PANGO_SCALE)
    if new_lang != cc.lang or new_font_size != cc.metrics_font_size:
        _set_context_options(cc, options)
    return cc.descent


cdef list _kpango_get_font_families(ContextContainer cc):
    cdef PangoFontFamily **families
    cdef int n, i
    cdef bytes famname
    cdef list out = list()
    pango_font_map_list_families(cc.fontmap, &families, &n)
    for i in range(n):
        out.append(pango_font_family_get_name(families[i]))
    g_free(families)
    return out


def kpango_get_font_families(kivylabel):
    cdef dict options = kivylabel.options
    cdef ContextContainer cc = _get_context_container(options)
    _set_context_options(cc, options)
    return _kpango_get_font_families(cc)


def kpango_find_base_dir(text):
    global pango_kivy_base_direction
    cdef bytes t = _byte_option(text)
    return pango_kivy_base_direction.get(pango_find_base_dir(t, len(t)))
