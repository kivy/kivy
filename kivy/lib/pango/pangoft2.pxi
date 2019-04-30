cdef extern from "glib.h" nogil:
    ctypedef void *gpointer
    ctypedef char gchar
    ctypedef int gint
    ctypedef unsigned int guint
    ctypedef unsigned long gsize
    ctypedef gint gboolean
    gboolean TRUE
    gboolean FALSE

    void *g_malloc(gsize n_bytes)
    void *g_malloc0(gsize n_bytes)
    void g_free(gpointer mem)
    void g_object_unref(gpointer obj)
#    gpointer GUINT_TO_POINTER(guint u)
#    guint GPOINTER_TO_UINT(gpointer p)

# https://www.freetype.org/freetype2/docs/reference/ft2-index.html
cdef extern from "../../lib/pango/freetype2.h" nogil:
    int FREETYPE_MAJOR
    int FREETYPE_MINOR
    int FREETYPE_PATCH
    ctypedef void *FT_Library
    ctypedef void *FT_Face
    ctypedef int FT_Error
    ctypedef unsigned char *FT_Byte
    ctypedef unsigned int FT_UInt
    ctypedef unsigned short FT_UShort

    ctypedef enum FT_Pixel_Mode:
        FT_PIXEL_MODE_NONE = 0
        FT_PIXEL_MODE_MONO
        FT_PIXEL_MODE_GRAY
        FT_PIXEL_MODE_GRAY2
        FT_PIXEL_MODE_GRAY4
        FT_PIXEL_MODE_LCD
        FT_PIXEL_MODE_LCD_V
        FT_PIXEL_MODE_BGRA
        FT_PIXEL_MODE_MAX

    ctypedef struct FT_Bitmap:
        unsigned int rows
        unsigned int width
        int pitch
        unsigned char* buffer
        unsigned short num_grays
        unsigned char pixel_mode
        unsigned char palette_mode
        void* palette

    void FT_Bitmap_New(FT_Bitmap *bitmap) # <= v2.5
    void FT_Bitmap_Init(FT_Bitmap *bitmap) # >= v2.6
    void FT_Bitmap_Done(FT_Library library, FT_Bitmap *bitmap)

    # For font face detection
    FT_Error FT_Init_FreeType(FT_Library *library)
    FT_Error FT_New_Face(FT_Library library, const char *pathname, long face_index, FT_Face *aface)
    FT_Error FT_Done_Face(FT_Face face)
    const char *FT_Get_Postscript_Name(FT_Face face)
#    FT_Error FT_Get_Sfnt_Name(FT_Face face, FT_UInt idx, FT_SfntName *aname)
#    FT_Error FT_Get_Sfnt_Name_Count(FT_Face face)


# https://www.freedesktop.org/software/fontconfig/fontconfig-devel/t1.html
cdef extern from "fontconfig/fontconfig.h" nogil:
    ctypedef struct FcConfig:
        pass
    ctypedef struct FcPattern:
        pass
    ctypedef struct FcValue:
        pass
    ctypedef enum FcResult:
        FcResultMatch
        FcResultNoMatch
        FcResultTypeMismatch
        FcResultNoId

    ctypedef bint FcBool
    ctypedef unsigned char FcChar8
    bint FcTrue
    bint FcFalse
    const char *FC_FAMILY
    const char *FC_ANTIALIAS
    const char *FC_HINTING
    const char *FC_HINT_STYLE
    int FC_HINT_NONE
    int FC_HINT_SLIGHT
    int FC_HINT_MEDIUM
    int FC_HINT_FULL

    FcConfig *FcConfigCreate()
    FcConfig *FcInitLoadConfig()
    FcConfig *FcInitLoadConfigAndFonts()
    void FcConfigDestroy(FcConfig *config)
    FcConfig *FcConfigGetCurrent()
    FcBool FcConfigSetCurrent(FcConfig *config)
    FcBool FcConfigAppFontAddFile(FcConfig *config, const FcChar8 *file)
    FcBool FcConfigAppFontAddDir(FcConfig *config, const FcChar8 *dir)
    void FcConfigAppFontClear(FcConfig *config)
    FcBool FcConfigParseAndLoad(FcConfig *config, const FcChar8 *file, FcBool complain)
    FcBool FcConfigSetRescanInterval(FcConfig *config, int rescaninterval)
    int FcConfigGetRescanInterval(FcConfig *config)

    FcResult FcPatternGetString(FcPattern *p, const char *object, int id, FcChar8 **s)
    void FcPatternDestroy(FcPattern *p)
    FcBool FcPatternDel(FcPattern *p, const char *object)
    FcBool FcPatternAddInteger (FcPattern *p, const char *object, int i)
    FcBool FcPatternAddBool (FcPattern *p, const char *object, FcBool b)
#    FcPattern *FcPatternCreate()
#    FcBool FcPatternAddDouble (FcPattern *p, const char *object, double d)
#    FcBool FcPatternAddString (FcPattern *p, const char *object, const FcChar8 *s)
#    FcBool FcPatternAddMatrix (FcPattern *p, const char *object, const FcMatrix *m)
#    FcBool FcPatternAddCharSet (FcPattern *p, const char *object, const FcCharSet *c)
#    FcBool FcPatternAddFTFace (FcPattern *p, const char *object, const FT_Facef)
#    FcBool FcPatternAddLangSet (FcPattern *p, const char *object, const FcLangSet *l)
#    FcBool FcPatternAddRange (FcPattern *p, const char *object, const FcRange *r)


# https://www.freedesktop.org/software/fontconfig/fontconfig-devel/fcfreetypequeryface.html
cdef extern from "fontconfig/fcfreetype.h" nogil:
    FcPattern *FcFreeTypeQueryFace(const FT_Face face, const FcChar8 *file, unsigned int id, void *)


# https://developer.gnome.org/pango/stable/pango-Version-Checking.html
cdef extern from "pango/pango-utils.h":
    int PANGO_VERSION_CHECK(int major, int minor, int micro)


# https://developer.gnome.org/pango/stable/pango-Glyph-Storage.html
cdef extern from "pango/pango-types.h" nogil:
    unsigned int PANGO_SCALE


# https://developer.gnome.org/pango/stable/pango-Text-Attributes.html
cdef extern from "pango/pango-attributes.h" nogil:
    guint PANGO_ATTR_INDEX_FROM_TEXT_BEGINNING
    guint PANGO_ATTR_INDEX_TO_TEXT_END

    ctypedef struct PangoAttrList:
        pass
    ctypedef struct PangoAttrIterator:
        pass
    ctypedef struct PangoAttribute:
        pass
    ctypedef struct PangoAttrClass:
        pass
    ctypedef struct PangoAttrString:
        pass
    ctypedef struct PangoAttrLanguage:
        pass
    ctypedef struct PangoAttrInt:
        pass
    ctypedef struct PangoAttrSize:
        pass
    ctypedef struct PangoAttrFloat:
        pass
    ctypedef struct PangoAttrColor:
        pass
    ctypedef struct PangoAttrFontDesc:
        pass
    ctypedef struct PangoAttrShape:
        pass
    ctypedef struct PangoAttrFontFeatures:
        pass
    ctypedef enum PangoStyle:
        PANGO_STYLE_NORMAL
        PANGO_STYLE_OBLIQUE
        PANGO_STYLE_ITALIC
    # FIXME: investigate need to handle this for different pango versions
    ctypedef enum PangoWeight:
        PANGO_WEIGHT_THIN
        PANGO_WEIGHT_ULTRALIGHT
        PANGO_WEIGHT_LIGHT
        PANGO_WEIGHT_SEMILIGHT
        PANGO_WEIGHT_BOOK
        PANGO_WEIGHT_NORMAL
        PANGO_WEIGHT_MEDIUM
        PANGO_WEIGHT_SEMIBOLD
        PANGO_WEIGHT_BOLD
        PANGO_WEIGHT_ULTRABOLD
        PANGO_WEIGHT_HEAVY
        PANGO_WEIGHT_ULTRAHEAVY
    ctypedef enum PangoUnderline:
        PANGO_UNDERLINE_NONE
        PANGO_UNDERLINE_SINGLE
        PANGO_UNDERLINE_DOUBLE
        PANGO_UNDERLINE_LOW
        PANGO_UNDERLINE_ERROR

    PangoAttrList *pango_attr_list_new()
    PangoAttrList *pango_attr_list_ref(PangoAttrList *list)
    void pango_attr_list_unref(PangoAttrList *list)
    void pango_attr_list_insert(PangoAttrList  *list, PangoAttribute *attr)
    void pango_attr_list_insert_before(PangoAttrList  *list, PangoAttribute *attr)

    PangoAttribute *pango_attr_language_new(PangoLanguage *language)
    PangoAttribute *pango_attr_family_new(const char *family)
    PangoAttribute *pango_attr_size_new(int size)
    PangoAttribute *pango_attr_size_new_absolute(int size) # v1.8+
    PangoAttribute *pango_attr_style_new(PangoStyle style)
    PangoAttribute *pango_attr_weight_new(PangoWeight weight)
#    PangoAttribute *pango_attr_variant_new(PangoVariant variant)
#    PangoAttribute *pango_attr_stretch_new(PangoStretch stretch)
    PangoAttribute *pango_attr_font_desc_new(const PangoFontDescription *desc)
    PangoAttribute *pango_attr_underline_new(PangoUnderline underline)
    PangoAttribute *pango_attr_strikethrough_new(gboolean strikethrough)
    PangoAttribute *pango_attr_font_features_new(const gchar *features) # v1.38+


# https://developer.gnome.org/pango/stable/pango-Scripts-and-Languages.html
cdef extern from "pango/pango-language.h" nogil:
    ctypedef struct PangoLanguage:
        pass

    PangoLanguage *pango_language_get_default()
    PangoLanguage *pango_language_from_string(const char *language)
    const char *pango_language_to_string(PangoLanguage *language)


# https://developer.gnome.org/pango/stable/pango-FreeType-Fonts-and-Rendering.html
cdef extern from "pango/pangoft2.h" nogil:
    ctypedef struct PangoFT2FontMap:
        pass
    ctypedef void *PangoFT2SubstituteFunc
    ctypedef void *GDestroyNotify

    PangoFT2FontMap *PANGO_FT2_FONT_MAP(PangoFontMap *fontmap)
    void pango_ft2_render_layout(FT_Bitmap *bitmap, PangoLayout *layout, int x, int y)
    void pango_ft2_render_layout_subpixel(FT_Bitmap *bitmap, PangoLayout *layout, int x, int y)
    void pango_ft2_font_map_set_default_substitute(PangoFT2FontMap *fontmap, PangoFT2SubstituteFunc func, gpointer data, GDestroyNotify notify)
    void pango_ft2_font_map_substitute_changed(PangoFT2FontMap *fontmap)


# https://developer.gnome.org/pango/stable/pango-Text-Processing.html
cdef extern from "pango/pango-context.h" nogil:
    ctypedef struct PangoContext:
        pass

    void pango_context_set_base_dir(PangoContext *context, PangoDirection direction)
    void pango_context_set_font_description(PangoContext *context, const PangoFontDescription *desc)
    PangoDirection pango_context_get_base_dir(PangoContext *context)
    PangoFontMetrics *pango_context_get_metrics(PangoContext *context, const PangoFontDescription *desc, PangoLanguage *language)


# https://developer.gnome.org/pango/stable/pango-Bidirectional-Text.html
cdef extern from "pango/pango-bidi-type.h" nogil:
    ctypedef enum PangoDirection:
        PANGO_DIRECTION_LTR
        PANGO_DIRECTION_RTL
        PANGO_DIRECTION_TTB_LTR # deprecated
        PANGO_DIRECTION_TTB_RTL # deprecated
        PANGO_DIRECTION_WEAK_LTR
        PANGO_DIRECTION_WEAK_RTL
        PANGO_DIRECTION_NEUTRAL
    PangoDirection pango_find_base_dir(const gchar *text, gint length)


# https://developer.gnome.org/pango/stable/pango-Fonts.html
cdef extern from "pango/pango-font.h" nogil:
    ctypedef struct PangoFontMap:
        pass
    ctypedef struct PangoFontDescription:
        pass
    ctypedef struct PangoFontMetrics:
        pass
    ctypedef struct PangoFontFamily:
        pass

    PangoFontMap *pango_ft2_font_map_new()
    PangoFontDescription* pango_font_description_new()
    PangoFontDescription* pango_font_description_from_string(const char *string)
    void pango_font_description_free(PangoFontDescription *desc)
    int pango_font_metrics_get_ascent(PangoFontMetrics *metrics)
    int pango_font_metrics_get_descent(PangoFontMetrics *metrics)
    void pango_font_metrics_unref(PangoFontMetrics *metrics)
    const char *pango_font_family_get_name(PangoFontFamily *family)

    # Font descriptions:
    void pango_font_description_set_family(PangoFontDescription *desc, const char *family)
    const char *pango_font_description_get_family(PangoFontDescription *desc)

    void pango_font_description_set_size(PangoFontDescription *desc, gint size)
    void pango_font_description_set_absolute_size(PangoFontDescription *desc, gint size) # v1.8+
    gint pango_font_description_get_size(PangoFontDescription *desc)

    void pango_font_description_set_weight(PangoFontDescription *desc, PangoWeight weight)
    PangoWeight pango_font_description_get_weight(PangoFontDescription *desc)

    void pango_font_description_set_style(PangoFontDescription *desc, PangoStyle style)
    PangoStyle pango_font_description_get_style(PangoFontDescription *desc)


# https://developer.gnome.org/pango/stable/pango-Fonts.html
cdef extern from "pango/pango-fontmap.h" nogil:
    void pango_font_map_list_families(PangoFontMap *fontmap, PangoFontFamily ***families, int *n_families)


# https://developer.gnome.org/pango/stable/PangoFcFontMap.html
cdef extern from "pango/pangofc-fontmap.h" nogil:
    ctypedef struct PangoFcFontMap:
        pass

    PangoFcFontMap *PANGO_FC_FONT_MAP(PangoFontMap *fontmap)
    void pango_fc_font_map_set_config(PangoFcFontMap *fontmap, FcConfig *config)
    void pango_fc_font_map_config_changed(PangoFcFontMap *fontmap)


# https://developer.gnome.org/pango/stable/pango-Layout-Objects.html
cdef extern from "pango/pango-layout.h" nogil:
    ctypedef struct PangoLayout:
        pass

    ctypedef enum PangoAlignment:
        PANGO_ALIGN_LEFT
        PANGO_ALIGN_CENTER
        PANGO_ALIGN_RIGHT
    ctypedef enum PangoWrapMode:
        PANGO_WRAP_WORD
        PANGO_WRAP_CHAR
        PANGO_WRAP_WORD_CHAR
    ctypedef enum PangoEllipsizeMode:
        PANGO_ELLIPSIZE_NONE
        PANGO_ELLIPSIZE_START
        PANGO_ELLIPSIZE_MIDDLE
        PANGO_ELLIPSIZE_END

    PangoLayout *pango_layout_new(PangoContext *context)
    void pango_layout_context_changed(PangoLayout *layout)
    void pango_layout_set_attributes(PangoLayout *layout, PangoAttrList *attrs)
    void pango_layout_set_text(PangoLayout *layout, const char *text, int length)
    void pango_layout_set_markup(PangoLayout *layout, const char *markup, int length)
    void pango_layout_set_font_description(PangoLayout *layout, const PangoFontDescription *desc)
    void pango_layout_get_pixel_size(PangoLayout *layout, int *width, int *height)
    void pango_layout_get_size(PangoLayout *layout, int *width, int *height)
    int pango_layout_get_baseline(PangoLayout *layout)
    int pango_layout_get_line_count(PangoLayout *layout)
    int pango_layout_get_unknown_glyphs_count(PangoLayout *layout)
    gboolean pango_layout_xy_to_index(PangoLayout *layout, int x, int y, int *index, int *trailing)

    void pango_layout_set_ellipsize(PangoLayout *layout, PangoEllipsizeMode ellipsize)
    PangoEllipsizeMode pango_layout_get_ellipsize(PangoLayout *layout)
    gboolean pango_layout_is_ellipsized(PangoLayout *layout)

    void pango_layout_set_wrap(PangoLayout *layout, PangoWrapMode wrap)
    PangoWrapMode pango_layout_get_wrap(PangoLayout *layout)
    gboolean pango_layout_is_wrapped(PangoLayout *layout)

    void pango_layout_set_alignment(PangoLayout *layout, PangoAlignment alignment)
    PangoAlignment pango_layout_get_alignment(PangoLayout *layout)
    void pango_layout_set_auto_dir(PangoLayout *layout, gboolean auto_dir)
    gboolean pango_layout_get_auto_dir(PangoLayout *layout)
    void pango_layout_set_width(PangoLayout *layout, int width)
    int pango_layout_get_width(PangoLayout *layout)
    void pango_layout_set_height(PangoLayout *layout, int height)
    int pango_layout_get_height(PangoLayout *layout)
    void pango_layout_set_spacing(PangoLayout *layout, int spacing)
    int pango_layout_get_spacing(PangoLayout *laout)
    void pango_layout_set_indent(PangoLayout *layout, int indent)
    int pango_layout_get_indent(PangoLayout *layout)
    void pango_layout_set_justify(PangoLayout *layout, gboolean justify)
    gboolean pango_layout_get_justify(PangoLayout *layout)
    void pango_layout_set_single_paragraph_mode(PangoLayout *layout, gboolean setting)
    gboolean pango_layout_get_single_paragraph_mode(PangoLayout *layout)

cdef extern from "../../lib/pango/pangoft2.h" nogil:
    PangoContext *_pango_font_map_create_context(PangoFontMap *fontmap)
