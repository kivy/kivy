cdef extern from "glib.h" nogil:
    ctypedef void *gpointer
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
cdef extern from "../../lib/pangoft2.h" nogil:
    ctypedef struct FT_Library:
        pass

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

    void FT_Bitmap_Init(FT_Bitmap *bitmap)
    void FT_Bitmap_Done(FT_Library library, FT_Bitmap *bitmap)


# https://www.freedesktop.org/software/fontconfig/fontconfig-devel/t1.html
cdef extern from "fontconfig/fontconfig.h" nogil:
    ctypedef struct FcConfig:
        pass
    ctypedef struct FcPattern:
        pass
#    ctypedef struct FcFontSet:
#        int nfont
#        int sfont
#        FcPattern **fonts

    ctypedef bint FcBool
    ctypedef unsigned char FcChar8
    bint FcTrue
    bint FcFalse

    FcConfig *FcConfigCreate()
    FcConfig *FcInitLoadConfig()
    FcConfig *FcInitLoadConfigAndFonts()
    void FcConfigDestroy(FcConfig *config)
    FcConfig *FcConfigGetCurrent()
    FcBool FcConfigSetCurrent(FcConfig *config)
    FcBool FcConfigAppFontAddFile(FcConfig *config, const FcChar8 *file)

#    FcPattern *FcPatternCreate()
#    void FcPatternDestroy(FcPattern *p)
#    FcBool FcPatternDel(FcPattern *p, const char *object)
#    FcBool FcPatternAddInteger (FcPattern *p, const char *object, int i)
#    FcBool FcPatternAddDouble (FcPattern *p, const char *object, double d)
#    FcBool FcPatternAddString (FcPattern *p, const char *object, const FcChar8 *s)
#    FcBool FcPatternAddMatrix (FcPattern *p, const char *object, const FcMatrix *m)
#    FcBool FcPatternAddCharSet (FcPattern *p, const char *object, const FcCharSet *c)
#    FcBool FcPatternAddBool (FcPattern *p, const char *object, FcBool b)
#    FcBool FcPatternAddFTFace (FcPattern *p, const char *object, const FT_Facef)
#    FcBool FcPatternAddLangSet (FcPattern *p, const char *object, const FcLangSet *l)
#    FcBool FcPatternAddRange (FcPattern *p, const char *object, const FcRange *r)


# https://developer.gnome.org/pango/stable/pango-Glyph-Storage.html
cdef extern from "pango/pango-types.h" nogil:
#    ctypedef struct PangoRectangle:
#        int x
#        int y
#        int width
#        int height
    unsigned int PANGO_SCALE


# https://developer.gnome.org/pango/stable/pango-Scripts-and-Languages.html
cdef extern from "pango/pango-language.h" nogil:
    ctypedef struct PangoLanguage:
        pass

    PangoLanguage *pango_language_get_default()
    PangoLanguage *pango_language_from_string(const char *language)


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


# https://developer.gnome.org/pango/stable/pango-Text-Processing.html
cdef extern from "pango/pango-context.h" nogil:
    ctypedef struct PangoContext:
        pass

    void pango_context_set_base_dir(PangoContext *context, PangoDirection direction)
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


# https://developer.gnome.org/pango/stable/pango-Fonts.html
cdef extern from "pango/pango-font.h" nogil:
    ctypedef struct PangoFontMap:
        pass
    ctypedef struct PangoFontDescription:
        pass
    ctypedef struct PangoFontMetrics:
        pass

    PangoFontDescription* pango_font_description_from_string(const char *string)
    void pango_font_description_free(PangoFontDescription *desc)
#    void pango_font_description_set_size(PangoFontDescription *desc, gint size)
    PangoContext *pango_font_map_create_context(PangoFontMap *fontmap)
    PangoFontMap *pango_ft2_font_map_new()
    int pango_font_metrics_get_ascent(PangoFontMetrics *metrics)
    int pango_font_metrics_get_descent(PangoFontMetrics *metrics)
    void pango_font_metrics_unref(PangoFontMetrics *metrics)


# https://developer.gnome.org/pango/stable/PangoFcFontMap.html
cdef extern from "pango/pangofc-fontmap.h" nogil:
    ctypedef struct PangoFcFontMap:
        pass

    PangoFcFontMap *PANGO_FC_FONT_MAP(PangoFontMap *fontmap)
    void pango_fc_font_map_set_config(PangoFcFontMap *fontmap, FcConfig *config)


# https://developer.gnome.org/pango/stable/pango-Layout-Objects.html
cdef extern from "pango/pango-layout.h" nogil:
    ctypedef struct PangoLayout:
        pass

    ctypedef enum PangoAlignment:
        PANGO_ALIGN_LEFT
        PANGO_ALIGN_CENTER
        PANGO_ALIGN_RIGHT

    PangoLayout *pango_layout_new(PangoContext *context)
    void pango_layout_get_pixel_size(PangoLayout *layout, int *width, int *height)
    void pango_layout_get_size(PangoLayout *layout, int *width, int *height)
    void pango_layout_set_alignment(PangoLayout *layout, PangoAlignment alignment)
    void pango_layout_set_auto_dir(PangoLayout *layout, gboolean auto_dir)
    void pango_layout_set_markup(PangoLayout *layout, const char *markup, int length)
    void pango_layout_set_font_description(PangoLayout *layout, const PangoFontDescription *desc)
    void pango_layout_set_text(PangoLayout *layout, const char *text, int length)
    void pango_layout_set_width(PangoLayout *layout, int width)
    void pango_layout_set_height(PangoLayout *layout, int height)
    void pango_layout_set_spacing(PangoLayout *layout, int spacing)

