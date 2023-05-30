// needed to prevent warning during compilation

#if PANGO_VERSION_CHECK(1, 22, 0)
#define _pango_font_map_create_context(fontmap) \
    pango_font_map_create_context(fontmap)
#else
#define _pango_font_map_create_context(fontmap) \
    pango_ft2_font_map_create_context(PANGO_FT2_FONT_MAP(fontmap))
#endif
