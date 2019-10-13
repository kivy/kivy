# TODO:
# - We only render lines, can we use line-level pango layout functionality??
# - Support style/weight/different underlines
# - Investigate if we can use a serial in options dict to avoid reapply
# - Freeing isolated contexts seem to leak memory, though everything is
#   dealloc'd (it seems). May be an upstream issue, possibly related to the
#   loaded TTF file as I've only observed it by loading random fonts, some
#   of which do not render properly. Need to investigate + test with master
#   of fc/ft2/pango at some point. Bumped the max from 64 to 128 to compensate.
cimport cython
from libc.stdint cimport uint32_t
from libc.string cimport memset
from cpython.mem cimport PyMem_Malloc, PyMem_Free
from kivy.logger import Logger
from kivy.core.image import ImageData
from kivy.graphics.texture cimport Texture

include "../../lib/pango/pangoft2.pxi"
cdef extern from "../../lib/kivy_endian.h":
    const int KIVY_BYTEORDER
    const int KIVY_LIL_ENDIAN

# Since fontfiles can be reused in different contexts (or purged), cache family
# name(s) so the file doesn't have to be opened twice for every future load to
# a different context.
cdef dict kivy_fontfamily_cache = {}

# All font contexts (including isolated) are stored in a shared dictionary.
# Isolated contexts are added to the _cache_order in addition, and the
# oldest context will be purged from cache.
# FIXME: Fallback contexts are not purged, maybe they should be... ?
cdef dict kivy_font_context_cache = {}
cdef list kivy_isolated_cache_order = []

# Purge oldest items from cache dict + order list. This is not ideal,
# since the oldest item may still be the most used ...
cdef inline void _purge_ordered_cache(dict cache, list order, int limit):
    cdef bytes popid
    while len(order) >= limit:
        popid = order.pop(0)
        del cache[popid]


# Global FreeType2 library instance + state flags. This is used for detecting
# font family names, since FcConfigAppAddFontFile() doesn't give us a ref to
# the font. So we load the file using FreeType2 to query the resulting face
# using FontConfig (since we depend on it anyway, this is very cumbersome
# to do with ft2 directly due to vast number of encodings + huge tables etc)
cdef FT_Library kivy_ft_library
cdef int kivy_ft_error = FT_Init_FreeType(&kivy_ft_library)
if kivy_ft_error:
    Logger.warn("_text_pango: Failed to initialize FreeType2 "
                "library. Error code: {}".format(kivy_ft_error))

# Return a string that can be used to (hopefully) render with the font
# file later (font family name, or as close to it as we can get).
# This could be done with pango_fontmap_list_families, but it would
# require a separate FcConfig + adding file, etc. It doesn't seem like
# we can rely on the returned order to avoid double-scanning. I assume
# this is the most lightweight way to do it, but...
# FIXME: Investigate if we can use FC_FILE instead of this.
cdef bint _ft2_scan_fontfile_to_fontfamily_cache(bytes fontfile):
    global kivy_fontfamily_cache
    global kivy_ft_library
    global kivy_ft_error
    if kivy_ft_error:
        return False
    # Return from cache if this file has been loaded before
    cdef bytes filename = _byte_option(fontfile)
    if filename in kivy_fontfamily_cache:
        Logger.warn("_text_pango: _ft2_scan: Attempt to re-scan file '{}', "
                    "it is already cached with family name '{}'."
                    .format(filename, kivy_fontfamily_cache[filename]))
        return True

    # Load font file and get family name(s) for use in font description.
    # (there is no way to resolve conflicts for same family name)
    cdef FT_Face face
    cdef FT_Error error = FT_New_Face(kivy_ft_library, filename, 0, &face)
    if error:
        Logger.warn("_text_pango: Detecting family for '{}' failed: "
                    "Could not load/create face 0. Error code: ".format(filename, error))
        return False
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
                #        if it can lead to problems, versions, etc. It's also not
                #        clear when exactly a font has multiple families; one case
                #        is horizontal *and* vertical in the same file.
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

    kivy_fontfamily_cache[filename] = order
    return True


# Helper for label's string options
cdef inline bytes _byte_option(opt):
    if opt is None:
        return
    if isinstance(opt, bytes):
        return opt
    return opt.encode('UTF-8')


# Get PangoLanguage from options
cdef inline PangoLanguage *_get_options_text_language(dict options):
    cdef bytes txtlang = _byte_option(options['text_language'])
    if txtlang:
        return pango_language_from_string(txtlang)
    return pango_language_get_default()


# Callback data type, a gpointer (void *) to an instance stored in
# ContextContainer is passed to the default substitute function below.
# FIXME: If FC_FILE substitution works for font selection, add filename here.
#        At one point I came across a StackOverflow post where someone said
#        this is not reliable, but I can't find it now. I tested it with
#        cli tools, it seems to work. Needs to be investigated/tested.
ctypedef struct ft2subst_callback_data_t:
    int antialias
    int hintstyle


# Substitute callback, for `font_hinting` property originally implemented for sdl2
# https://github.com/SDL-mirror/SDL_ttf/blob/release-2.0.14/SDL_ttf.c#L2160-L2172
# https://github.com/GNOME/pango/blob/1.28/pango/pangoft2.c#L186-L222
cdef void _ft2subst_callback(FcPattern *pattern, gpointer data):
    cdef ft2subst_callback_data_t *cbdata = <ft2subst_callback_data_t *>data
    FcPatternDel(pattern, FC_ANTIALIAS)
    FcPatternAddBool(pattern, FC_ANTIALIAS, <FcBool>cbdata.antialias)
    FcPatternDel(pattern, FC_HINTING)
    FcPatternAddBool(pattern, FC_HINTING, <FcBool>(cbdata.hintstyle != 0))
    if cbdata.hintstyle != 0:
        FcPatternDel(pattern, FC_HINT_STYLE)
        FcPatternAddInteger(pattern, FC_HINT_STYLE, cbdata.hintstyle)
#    FcPatternDel(pattern, FC_AUTOHINT)
#    FcPatternAddBool(pattern, FC_AUTOHINT, ...)
#    if FC_MAJOR >= 2 and (FC_MINOR >= 12 or (FC_MINOR == 11 and FC_REVISION >= 91)):
#        FcPatternDel(pattern, FC_COLOR)
#        FcPatternAddBool(pattern, FC_COLOR, <FcBool>1)


# Fontconfig and pango structures (one per font context). Instances of
# this class are stored in the kivy_font_context_cache dict.
cdef class ContextContainer:
    cdef FcConfig *fc_config
    cdef PangoLayout *layout
    cdef PangoContext *context
    cdef PangoFontMap *fontmap
    cdef PangoFontDescription *fontdesc

    # FT2 default substitute data, used to pass 'font_hinting' to FontConfig
    cdef ft2subst_callback_data_t ft2subst_callback_data

    # Font metrics from most recent call to _set_cc_options()
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
            FcConfigAppFontClear(self.fc_config)
            FcConfigDestroy(self.fc_config)


# Create FcConfig object for initial cc setup
cdef inline bint _cc_fc_config_create(ContextContainer cc, bytes font_context):
    if cc.fc_config:
        Logger.warn("_text_pango: _cc_create_fcconfig(): cc.fc_config is not NULL")
        return False  # arguably True .. but should not happen

    cdef bytes context_source
    if font_context.startswith(b'systemconfig://'):
        cc.fc_config = FcInitLoadConfig()
    elif font_context.startswith(b'system://'):
        cc.fc_config = FcInitLoadConfigAndFonts()
    elif font_context.startswith(b'directory://'):
        cc.fc_config = FcInitLoadConfig()
        context_source = font_context[12:]
        if FcConfigAppFontAddDir(cc.fc_config, <FcChar8 *>context_source) == FcFalse:
            Logger.warn("_text_pango: Error loading font directory for font_context {}: {}"
                        .format(font_context, context_source))
    elif font_context.startswith(b'fontconfig://'):
        cc.fc_config = FcConfigCreate()
        context_source = font_context[13:]
        if FcTrue != FcConfigParseAndLoad(cc.fc_config, <FcChar8 *>context_source, FcTrue):
            Logger.warn("_text_pango: Error loading FontConfig configuration "
                        "for font_context {}: {}".format(font_context, context_source))
    else:  # isolated context
        cc.fc_config = FcConfigCreate()

    if not cc.fc_config:
        Logger.warn("_text_pango: Could not create new FcConfig object, out of memory?")
        return False
    # Disable rescan interval, maybe we shouldn't do this for system://?
    FcConfigSetRescanInterval(cc.fc_config, 0)
    return True


# Add a font to cc and return its family name for later use
cdef inline bytes _cc_add_font_file(ContextContainer cc, bytes font_name_r):
    global kivy_fontfamily_cache
    if font_name_r in cc.loaded_fonts:
        return kivy_fontfamily_cache[font_name_r]
    if FcConfigAppFontAddFile(cc.fc_config, <FcChar8 *>font_name_r) == FcFalse:
        Logger.warn("_text_pango: Error loading font '{}'".format(font_name_r))
        return
    cc.loaded_fonts.update([font_name_r])
    if font_name_r not in kivy_fontfamily_cache:
        if not _ft2_scan_fontfile_to_fontfamily_cache(font_name_r):
            return  # warnings issued in function call
    return kivy_fontfamily_cache[font_name_r]


# Return a list of all font family names available in cc
# NOTE: pango adds static "monospace", "sans" and "serif"
cdef list _cc_list_families(ContextContainer cc):
    cdef PangoFontFamily **families
    cdef int n, i
    cdef bytes famname
    cdef list out = list()
    pango_font_map_list_families(cc.fontmap, &families, &n)
    for i in range(n):
        out.append(pango_font_family_get_name(families[i]))
    g_free(families)
    return out


# Configure ContextContainer with options from kivylabel.
# Underline, strikethrough, OpenType Font features (...) are not part of font
# description. I'm not 100% sure how this fits together, but apparently none
# of this impact metrics?
# FIXME: Figure out the minimum needed for fontdesc/attrs here
cdef _set_cc_options(ContextContainer cc, dict options):
    global kivy_fontfamily_cache
    cdef PangoAttrList *attrs = pango_attr_list_new()
    cdef bytes font_name_r = _byte_option(options['font_name_r'])
    cdef bytes font_context = _byte_option(options['font_context'])

    # Set the current FcConfig, needed for Pango to see the contained fonts.
    # Versions 1.38+ use a call to pango_fc_font_map_set_config() instead.
    # FIXME: The fallback approach crashes for me, with 1.40.x and an old
    #        FontConfig version -- all crashes in FC, it may work with
    #        an older pango + newer fontconfig, or not.. need research
    if not PANGO_VERSION_CHECK(1, 38, 0):
        if FcConfigGetCurrent() != cc.fc_config:
            if FcConfigSetCurrent(cc.fc_config) == FcFalse:
                Logger.warn("_text_pango: set_cc_options(): Failed to set "
                            "current fc_config for font_name_r='{}', font_context='{}'"
                            .format(font_name_r, font_context))

    # Specify font family for fallback contexts; we don't care for isolated,
    # there is only one font to choose from.
    cdef bytes family_attr = b'Sans'
    if font_context:
        if options['font_family']:
            family_attr = _byte_option(options['font_family'])
        elif font_name_r:
            family_attr = kivy_fontfamily_cache.get(font_name_r, b'Sans')
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

    # At the moment, this is not needed since we don't use Pango for text layout
#    cdef PangoDirection base_dir = _get_options_base_direction(options)
#    if base_dir == PANGO_DIRECTION_NEUTRAL: <--- AUTO!
#        pango_layout_set_auto_dir(cc.layout, TRUE)
#        pango_context_set_base_dir(cc.context, PANGO_DIRECTION_WEAK_LTR)
#    else:
#        # If autodir is false, the context's base direction is used
#        pango_layout_set_auto_dir(cc.layout, FALSE)
#        pango_context_set_base_dir(cc.context, base_dir)

    # FIXME: Not clear if this is identical to sdl2 settings
    cdef bytes hinting = _byte_option(options['font_hinting'])
    if hinting == b'normal':
        cc.ft2subst_callback_data.antialias = 1
        cc.ft2subst_callback_data.hintstyle = FC_HINT_FULL
    elif hinting == b'light':
        cc.ft2subst_callback_data.antialias = 1
        cc.ft2subst_callback_data.hintstyle = FC_HINT_SLIGHT
    elif hinting == b'mono':
        cc.ft2subst_callback_data.antialias = 0
        cc.ft2subst_callback_data.hintstyle = FC_HINT_FULL
    else:
        cc.ft2subst_callback_data.antialias = 0
        cc.ft2subst_callback_data.hintstyle = FC_HINT_NONE
    pango_ft2_font_map_substitute_changed(PANGO_FT2_FONT_MAP(cc.fontmap))

    # Apply font description to context before getting metrics
    pango_context_set_font_description(cc.context, cc.fontdesc)

    cdef PangoFontMetrics *metrics
    cdef PangoLanguage *lang = _get_options_text_language(options)
    metrics = pango_context_get_metrics(cc.context, cc.fontdesc, lang)
    if metrics:
        cc.ascent = <double>(pango_font_metrics_get_ascent(metrics) / PANGO_SCALE)
        cc.descent = <double>(pango_font_metrics_get_descent(metrics) / PANGO_SCALE)
        pango_font_metrics_unref(metrics)
    else:
        Logger.warn("_text_pango: Could not get context metrics requesting "
                    "family_attr='{}', font_context='{}', font_name_r='{}'"
                    .format(family_attr, font_context, font_name_r))

    pango_attr_list_insert(attrs, pango_attr_language_new(lang))
    pango_layout_set_attributes(cc.layout, attrs)
    pango_attr_list_unref(attrs)  # Layout owns it now
    pango_layout_context_changed(cc.layout)


# Create or retrieve a ContextContainer from cache, for the given font_context
# and font_name_r. If no font context is specified, font_name_r is required and
# an isolated context is created (single font only). With a font_context,
# font_name_r can optionally be specified to load the font on top of existing
# fonts (for example provided by system:// or directory://)
cdef ContextContainer _get_or_create_cc(bytes font_context, bytes font_name_r):
    global kivy_font_context_cache
    global kivy_isolated_cache_order
    cdef ContextContainer cc
    cdef bint isolated = False

    if not font_context:
        if not font_name_r:
            raise Exception('_text_pango: Attempt to load empty font_name_r in an'
                            'isolated context. This is not possible.')
        isolated = True
        font_context = b'isolated://' + font_name_r

    # Check for cached context container
    cc = kivy_font_context_cache.get(font_context)
    if cc:
        if not font_name_r or font_name_r in cc.loaded_fonts:
            return cc
        if _cc_add_font_file(cc, font_name_r):
            if PANGO_VERSION_CHECK(1, 38, 0):
                # Older versions swap the FcConfig in _set_cc_options()
                pango_fc_font_map_config_changed(PANGO_FC_FONT_MAP(cc.fontmap))
        return cc

    cc = ContextContainer()
    if not _cc_fc_config_create(cc, font_context):
        return  # warnings issued in function call

    # Add the specified font file to context, if any.
    if font_name_r:
        _cc_add_font_file(cc, font_name_r)

    # Font description is updated from options every time the cc is used.
    # (it represents an "ideal font", ie what you *want* to draw with)
    cc.fontdesc = pango_font_description_new()

    # Create font map and set its FcConfig if Pango supports it (v1.38+).
    # Older versions swapping the current FcConfig in _set_cc_options()
    cc.fontmap = pango_ft2_font_map_new()
    if not cc.fontmap:
        Logger.warn("_text_pango: Could not create new font map")
        return
    if PANGO_VERSION_CHECK(1, 38, 0):
        pango_fc_font_map_set_config(PANGO_FC_FONT_MAP(cc.fontmap), cc.fc_config)
    # The default substitute function is used to apply some last-minute
    # options to FontConfig pattern.
    pango_ft2_font_map_set_default_substitute(PANGO_FT2_FONT_MAP(cc.fontmap),
                &_ft2subst_callback, <gpointer>&cc.ft2subst_callback_data, NULL)

    cc.context = _pango_font_map_create_context(cc.fontmap)
    if not cc.context:
        Logger.warn("_text_pango: Could not create pango context")
        return

    cc.layout = pango_layout_new(cc.context)
    if not cc.layout:
        Logger.warn("_text_pango: Could not create pango layout")
        return

    kivy_font_context_cache[font_context] = cc
    if isolated:
        _purge_ordered_cache(kivy_font_context_cache, kivy_isolated_cache_order, 128)
        kivy_isolated_cache_order.append(font_name_r)
    return cc


cdef inline ContextContainer _get_or_create_cc_from_options(dict options):
    cdef bytes font_name_r = _byte_option(options['font_name_r'])
    cdef bytes font_context = _byte_option(options['font_context'])
    return _get_or_create_cc(font_context, font_name_r)


# Renders the pango layout to a grayscale bitmap, and blits RGBA at x, y
cdef short RSHIFT, GSHIFT, BSHIFT, ASHIFT
if KIVY_BYTEORDER == KIVY_LIL_ENDIAN:
    RSHIFT = 0;  GSHIFT = 8;  BSHIFT = 16; ASHIFT = 24
else:
    RSHIFT = 24; GSHIFT = 16; BSHIFT = 8;  ASHIFT = 0
@cython.cdivision(True)
@cython.boundscheck(False)
@cython.wraparound(False)
cdef void _render_layout(PangoLayout *layout, unsigned char *dstbuf,
                     int dstbuf_w, int dstbuf_h, int x, int y,
                     unsigned char R, unsigned char G, unsigned char B,
                     unsigned char A) nogil:
    global RSHIFT, GSHIFT, BSHIFT, ASHIFT
    #              <----------- x -----------> <------- w -------->
    #         .--> .--------------- dstbuf ---.-------------------. <--.
    #         |    |                          |      bitmap       |    | h
    # dstbuf_h|    |                          '-------------------| <=<
    #         |    |                                              |    | y
    #         '--> '----------------------------------------------' <--'
    #              <---------------- dstbuf_w -------------------->
    if not dstbuf or dstbuf_w <= 0 or dstbuf_h <= 0 or x > dstbuf_w or y > dstbuf_h:
        with gil:
            Logger.warn("_text_pango: _cc_render() with invalid arguments, "
                        "this usually means text layout could not fit text within user-"
                        "specified constraints: dstbuf size={}x{}, x={}, y={}"
                        .format(dstbuf_w, dstbuf_h, x, y))
            return

    cdef int layout_w, layout_h
    pango_layout_get_pixel_size(layout, &layout_w, &layout_h)

    # If the bitmap is partially outside dstbuf, clip + blit a smaller area
    cdef int w = layout_w, h = layout_h
    cdef int clip_x_min = 0, clip_y_min = 0
    if x < 0:
        clip_x_min = -x
        w -= clip_x_min
        x = 0
    if y < 0:
        clip_y_min = -y
        h -= clip_y_min
        y = 0
    if x + w > dstbuf_w:
        w -= x + w - dstbuf_w
    if y + h > dstbuf_h:
        h -= y + h - dstbuf_h
    if w <= 0 or h <= 0 or x + w > dstbuf_w or y + h > dstbuf_h:
        with gil:
            Logger.warn("_text_pango: Invalid blit: dstbuf size={}x{}, "
                        "x={}, y={}, clip_x_min={}, w={}, clip_y_min={}, h={}"
                        .format(dstbuf_w, dstbuf_h, x, y, clip_x_min, w, clip_y_min, h))
            return

    cdef FT_Bitmap bitmap
    cdef int xi, yi
    cdef unsigned char graysrc
    cdef unsigned long grayidx
    cdef unsigned long yi_w
    cdef unsigned long offset
    cdef unsigned long offset_fixed = x + (y * dstbuf_w)
    cdef unsigned long offset_yi = dstbuf_w - w
    cdef unsigned long maxpos = dstbuf_w * dstbuf_h

    # Sanity check that we don't go out of bounds here, should not happen
    if offset_fixed + ((h-1)*offset_yi) + ((h-1)*w) + w - 1 > maxpos:
        with gil:
            Logger.warn("_text_pango: Ignoring out of bounds blit: dstbuf size={}x{}, "
                        "x={}, y={}, clip_x_min={}, w={}, clip_y_min={}, h={}, maxpos={}"
                        .format(dstbuf_w, dstbuf_h, x, y, clip_x_min, w, clip_y_min, h, maxpos))
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
            Logger.warn("_text_pango: Unsupported FreeType library version. "
                        "Abort rendering.")
            return

    bitmap.width = layout_w
    bitmap.rows = layout_h
    bitmap.pitch = layout_w # 1-byte grayscale
    bitmap.pixel_mode = FT_PIXEL_MODE_GRAY # no BGRA in pango (ft2 has it)
    bitmap.num_grays = 256
    bitmap.buffer = <unsigned char *>g_malloc0(layout_w * layout_h)
    if not bitmap.buffer:
        with gil:
            Logger.warn("_text_pango: Could not malloc FT_Bitmap.buffer")
            return

    # Render the layout as 1 byte per pixel grayscale bitmap
    # FIXME: does render_layout_subpixel() do us any good?
    pango_ft2_render_layout(&bitmap, layout, 0, 0)

    # Blit the bitmap as RGBA at x, y in dstbuf (w/h is the clipped ft2 bitmap)
    cdef uint32_t col = R << RSHIFT | G << GSHIFT | B << BSHIFT
    for yi in range(clip_y_min, h):
        offset = offset_fixed + (yi * offset_yi)
        yi_w = yi * w
        for xi in range(clip_x_min, w):
            grayidx = yi_w + xi
            graysrc = (bitmap.buffer)[grayidx]
            (<uint32_t *>dstbuf)[offset + grayidx] = col | ( ((A * graysrc) / 255) << ASHIFT )
    g_free(bitmap.buffer)
    # /nogil _render_layout()


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
            Logger.warn("_text_pango: render() called, but self.pixels is NULL")
            return
        cdef dict options = kivylabel.options
        cdef ContextContainer cc = _get_or_create_cc_from_options(options)
        if not cc:
            Logger.warn("_text_pango: Could not get context container, aborting")
            return

        _set_cc_options(cc, options)
        cdef bytes utf = _byte_option(text)
        pango_layout_set_text(cc.layout, utf, len(utf))

        # Kivy normalized text color -> 0-255 rgba for nogil
        cdef unsigned char R, G, B, A = 255
        color = options['color']
        R = min(255, int(color[0] * 255))
        G = min(255, int(color[1] * 255))
        B = min(255, int(color[2] * 255))
        if len(color) > 3:  # ran into a situation where a wasn't included
            A = min(255, int(color[3] * 255))

        # Finally render the layout and blit it to self.pixels
        cdef int xx = x
        cdef int yy = y
        with nogil:
            _render_layout(cc.layout, self.pixels, self.w, self.h, xx, yy, R, G, B, A)
        self.rdrcount += 1

    # Return ImageData instance with the rendered pixels
    def get_ImageData(self):
        if not self.pixels:
            Logger.warn("_text_pango: get_ImageData() self.pixels == NULL")
            return
        if not self.rdrcount:
            Logger.warn("_text_pango: get_ImageData() without render() call")
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
    if text is None:  # text='' needs to return size
        return 0, 0
    cdef dict options = kivylabel.options
    cdef ContextContainer cc = _get_or_create_cc_from_options(options)
    if not cc:
        Logger.warn("_text_pango: Could not get container for extents, "
                    "font_name='{}', font_context='{}', font_name_r='{}'"
                    .format(options['font_name'], options['font_context'], options['font_name_r']))
        return 0, 0

    cdef bytes utf = _byte_option(text)
    pango_layout_set_text(cc.layout, utf, len(utf))
    _set_cc_options(cc, options)
    cdef int w, h
    pango_layout_get_pixel_size(cc.layout, &w, &h)
    return w, h


def kpango_get_ascent(kivylabel):
    cdef dict options = kivylabel.options
    cdef ContextContainer cc = _get_or_create_cc_from_options(options)
    if not cc:
        Logger.warn("_text_pango: Could not get container for ascent, "
                    "font_name='{}', font_context='{}', font_name_r='{}'"
                    .format(options['font_name'], options['font_context'], options['font_name_r']))
        return 0
    _set_cc_options(cc, options)
    return cc.ascent


def kpango_get_descent(kivylabel):
    cdef dict options = kivylabel.options
    cdef ContextContainer cc = _get_or_create_cc_from_options(options)
    if not cc:
        Logger.warn("_text_pango: Could not get container for descent, "
                    "font_name='{}', font_context='{}', font_name_r='{}'"
                    .format(options['font_name'], options['font_context'], options['font_name_r']))
        return 0
    _set_cc_options(cc, options)
    return cc.descent


cdef dict _pango2kivy_base_direction = {
    PANGO_DIRECTION_LTR: 'ltr',
    PANGO_DIRECTION_RTL: 'rtl',
    PANGO_DIRECTION_WEAK_LTR: 'weak_ltr',
    PANGO_DIRECTION_WEAK_RTL: 'weak_rtl'}

def kpango_find_base_dir(text):
    global _pango2kivy_base_direction
    cdef bytes t = _byte_option(text)
    return _pango2kivy_base_direction.get(pango_find_base_dir(t, len(t)))


def kpango_font_context_exists(font_context):
    global kivy_font_context_cache
    cdef bytes fctx = _byte_option(font_context)
    return fctx and fctx in kivy_font_context_cache


def kpango_font_context_create(font_context, fontfile=None):
    global kivy_font_context_cache
    cdef bytes fctx = _byte_option(font_context)
    cdef bytes font_name_r = _byte_option(fontfile)
    if fctx in kivy_font_context_cache:
        return False
    cdef ContextContainer cc = _get_or_create_cc(fctx, font_name_r)
    if cc:
        return True


def kpango_font_context_add_font(font_context, fontfile):
    global kivy_font_context_cache
    global kiby_fontfamily_cache
    cdef bytes fctx = _byte_option(font_context)
    cdef bytes font_name_r = _byte_option(fontfile)
    if not fctx:
        Logger.warn("_text_pango: kpango_font_context_add_font() called "
                    "with empty context")
        return
    cdef ContextContainer cc = _get_or_create_cc(fctx, None)
    if not cc:
        Logger.warn("_text_pango: kpango_font_context_add_font() failed, could "
                    "not resolve or create context container for '{}'".format(fctx))
        return
    if font_name_r not in cc.loaded_fonts:
        return _cc_add_font_file(cc, font_name_r)
    return kivy_fontfamily_cache[font_name_r].decode('utf-8')


def kpango_font_context_destroy(font_context):
    global kivy_font_context_cache
    cdef bytes fctx = _byte_option(font_context)
    if fctx and fctx in kivy_font_context_cache:
        del kivy_font_context_cache[fctx]


def kpango_font_context_list():
    global kivy_font_context_cache
    return list(kivy_font_context_cache.keys())


def kpango_font_context_list_families(font_context):
    global kivy_font_context_cache
    cdef bytes fctx = _byte_option(font_context)
    if fctx and fctx in kivy_font_context_cache:
        return [x.decode('utf-8') for x in _cc_list_families(kivy_font_context_cache[fctx])]
    return []


def kpango_font_context_list_custom(font_context):
    global kivy_font_context_cache
    global kivy_fontfamily_cache
    cdef bytes fctx = _byte_option(font_context)
    cdef ContextContainer cc = kivy_font_context_cache.get(font_context)
    if cc:
        return {x: kivy_fontfamily_cache[x].decode('utf-8') for x in cc.loaded_fonts}
    return {}


# ----------------------------------------------------------------------------
# Direct Pango layout access. This can be used by application developers
# with advanced i18n requirements, and eventually Kivy's text core should
# evolve to support using Pango fully (probably a garden.pango package first)
# ----------------------------------------------------------------------------

cdef dict _pango2kivy_alignment = {
        PANGO_ALIGN_LEFT: 'left',
        PANGO_ALIGN_CENTER: 'center',
        PANGO_ALIGN_RIGHT: 'right'}
cdef dict _kivy2pango_alignment = {
        'left': PANGO_ALIGN_LEFT,
        'center': PANGO_ALIGN_CENTER,
        'right': PANGO_ALIGN_RIGHT}

cdef dict _pango2kivy_ellipsize_mode = {
        PANGO_ELLIPSIZE_NONE: 'none',
        PANGO_ELLIPSIZE_START: 'start',
        PANGO_ELLIPSIZE_MIDDLE: 'middle',
        PANGO_ELLIPSIZE_END: 'end'}
cdef dict _kivy2pango_ellipsize_mode = {
        'none': PANGO_ELLIPSIZE_NONE,
        'start': PANGO_ELLIPSIZE_START,
        'middle': PANGO_ELLIPSIZE_MIDDLE,
        'end': PANGO_ELLIPSIZE_END}

cdef dict _pango2kivy_wrap_mode = {
        PANGO_WRAP_WORD: 'word',
        PANGO_WRAP_CHAR: 'char',
        PANGO_WRAP_WORD_CHAR: 'word_char'}
cdef dict _kivy2pango_wrap_mode = {
        'word': PANGO_WRAP_WORD,
        'char': PANGO_WRAP_CHAR,
        'word_char': PANGO_WRAP_WORD_CHAR}

cdef class KivyPangoLayout:
    cdef PangoLayout *layout

    def __init__(self, font_context):
        global kivy_isolated_cache_order
        cdef bytes fctx = _byte_option(font_context)
        cdef ContextContainer cc = _get_or_create_cc(fctx, None)
        self.layout = pango_layout_new(cc.context)
        if fctx in kivy_isolated_cache_order:
            kivy_isolated_cache_order.remove(fctx)
            Logger.warn("_text_pango: Removed font context {} from ordered cache, "
                        "it was used in a KivyPangoLayout".format(font_context))

    def __dealloc__(self):
        if self.layout:
            g_object_unref(self.layout)

    def set_markup(self, markup, encoding='utf-8'):
        cdef bytes m = _byte_option(markup)
        pango_layout_set_markup(self.layout, m, len(m))

    def set_width(self, width):
        pango_layout_set_width(self.layout, int(width))

    def get_width(self):
        return pango_layout_get_width(self.layout)

    def set_height(self, height):
        pango_layout_set_height(self.layout, int(height))

    def get_height(self):
        return pango_layout_get_height(self.layout)

    def get_wrap(self):
        global _pango2kivy_wrap_mode
        return _pango2kivy_wrap_mode.get(pango_layout_get_wrap(self.layout))

    def set_wrap(self, wrap):
        global _kivy2pango_wrap_mode
        cdef PangoWrapMode wm = _kivy2pango_wrap_mode.get(wrap, PANGO_WRAP_WORD)
        pango_layout_set_wrap(self.layout, wm)

    def is_wrapped(self):
        return pango_layout_is_wrapped(self.layout)

    def set_ellipsize(self, ellipsize):
        global _kivy2pango_ellipsize_mode
        cdef PangoEllipsizeMode em = _kivy2pango_ellipsize_mode.get(ellipsize, PANGO_ELLIPSIZE_NONE)
        pango_layout_set_ellipsize(self.layout, em)

    def get_ellipsize(self):
        global _pango2kivy_ellipsize_mode
        return _pango2kivy_ellipsize_mode.get(pango_layout_get_ellipsize(self.layout), 'none')

    def is_ellipsized(self):
        return pango_layout_is_ellipsized(self.layout)

    def set_indent(self, indent):
        pango_layout_set_indent(self.layout, int(indent))

    def get_indent(self):
        return pango_layout_get_indent(self.layout)

    def set_spacing(self, spacing):
        pango_layout_set_spacing(self.layout, int(spacing))

    def get_spacing(self):
        return pango_layout_get_spacing(self.layout)

    def set_justify(self, justify):
        pango_layout_set_justify(self.layout, bool(justify))

    def get_justify(self):
        return pango_layout_get_justify(self.layout)

    def set_auto_dir(self, autodir):
        pango_layout_set_auto_dir(self.layout, bool(autodir))

    def get_auto_dir(self):
        return pango_layout_get_auto_dir(self.layout)

    def set_alignment(self, alignment):
        global _kivy2pango_alignment
        cdef PangoAlignment a = _kivy2pango_alignment.get(alignment, PANGO_ALIGN_LEFT)
        pango_layout_set_alignment(self.layout, a)

    def get_alignment(self):
        global _pango2kivy_alignment
        return _pango2kivy_alignment.get(pango_layout_get_alignment(self.layout), 'left')

    # set_tabs, get_tabs

    def set_single_paragraph_mode(self, mode):
        pango_layout_set_single_paragraph_mode(self.layout, bool(mode))

    def get_single_paragraph_mode(self):
        return pango_layout_get_single_paragraph_mode(self.layout)

    def get_unknown_glyphs_count(self):
        return pango_layout_get_unknown_glyphs_count(self.layout)

    # pango_layout_get_log_attrs, pango_layout_get_log_attrs_readonly
    # pango_layout_index_to_pos
    # pango_layout_index_to_line_x

    def xy_to_index(self, x, y):
        cdef int index, trailing
        cdef bint result = pango_layout_xy_to_index(self.layout, x, y, &index, &trailing)
        return (result, index, trailing)

    # pango_layout_get_cursor_pos
    # pango_layout_move_cursor_visually
    # pango_layout_get_extents
    # pango_layout_get_pixel_extents

    def get_size(self):
        cdef int w, h
        pango_layout_get_size(self.layout, &w, &h)
        return (w, h)

    def get_pixel_size(self):
        cdef int w, h
        pango_layout_get_pixel_size(self.layout, &w, &h)
        return (w, h)

    def get_baseline(self):
        return pango_layout_get_baseline(self.layout)

    def get_line_count(self):
        return pango_layout_get_line_count(self.layout)

    # pango_layout_get_line, pango_layout_get_line_readonly
    # pango_layout_get_lines
    # pango_layout_get_iter, pango_layout_iter_*
    # pango_layout_line_*

    def render_as_bytes(self, color=None):
        cdef int w, h
        pango_layout_get_pixel_size(self.layout, &w, &h)
        if w <= 0 or h <= 0:
            Logger.warn("_text_pango: KivyPangoLayout.render_as_bytes "
                        "failed - layout pixel size is {} x {}".format(w, h))
            return
        cdef unsigned char *pixels = <unsigned char *>PyMem_Malloc(w * h * 4)
        if not pixels:
            Logger.warn("_text_pango: KivyPangoLayout.render_as_bytes "
                        "failed - out of memory?")
            return
        cdef unsigned char R = 255, G = 255, B = 255, A = 255
        if color:
            R = min(255, int(color[0] * 255))
            G = min(255, int(color[1] * 255))
            B = min(255, int(color[2] * 255))
            if len(color) > 3:
                A = min(255, int(color[3] * 255))
        with nogil:
            memset(pixels, 0, w * h * 4)
            _render_layout(self.layout, pixels, w, h, 0, 0, R, G, B, A)
        cdef bytes out = <bytes>pixels[:w * h * 4]
        try:
            return (w, h, 'rgba', out)
        finally:
            PyMem_Free(pixels)

    def render_as_ImageData(self, **kwargs):
        result = self.render_as_bytes(**kwargs)
        if result:
            return ImageData(*result)

    def render_as_Texture(self, mipmap=False, **kwargs):
        result = self.render_as_bytes(**kwargs)
        if result:
            tex = Texture.create_from_data(ImageData(*result), mipmap=mipmap)
            tex.flip_vertical()
            return tex
