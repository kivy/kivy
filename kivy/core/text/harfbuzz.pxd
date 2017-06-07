#for wrapping hb-ft
cdef extern from hb-ft.h:

	HB_EXTERN hb_face_t *hb_ft_face_create (FT_Face ft_face, hb_destroy_func_t destroy)

    HB_EXTERN hb_face_t *hb_ft_face_create_cached (FT_Face ft_face)

	HB_EXTERN hb_face_t *hb_ft_face_create_referenced (FT_Face ft_face)

	hb_ft_font_create (FT_Face ft_face,hb_destroy_func_t destroy)

	HB_EXTERN hb_font_t *hb_ft_font_create_referenced (FT_Face ft_face)

	HB_EXTERN FT_Face hb_ft_font_get_face (hb_font_t *font)

#for wrapping hb.h,wrapped below all header files

#wrapping hb-blob.h
cdef extern from  hb-blob.h:
	ctypedef enum hb_memory_mode_t:
        HB_MEMORY_MODE_DUPLICATE,
        HB_MEMORY_MODE_READONLY,
        HB_MEMORY_MODE_WRITABLE,
        HB_MEMORY_MODE_READONLY_MAY_MAKE_WRITABLE

    ctypedef struct hb_blob_t hb_blob_t
    
    #dbt how to deal with hb_memory_mode_t ? enum?

    HB_EXTERN hb_blob_t *hb_blob_create (const char *data, unsigned int length, hb_memory_mode_t mode,void *user_data,hb_destroy_func_t  destroy)

    HB_EXTERN hb_blob_t *hb_blob_create_sub_blob (hb_blob_t    *parent, unsigned int  offset, unsigned int  length)

    HB_EXTERN hb_blob_t *hb_blob_get_empty (void)

    HB_EXTERN hb_blob_t *hb_blob_reference (hb_blob_t *blob)

    HB_EXTERN void hb_blob_destroy (hb_blob_t *blob)

    HB_EXTERN hb_bool_t hb_blob_set_user_data (hb_blob_t *blob, hb_user_data_key_t *key, void *data, hb_destroy_func_t   destroy,hb_bool_t replace)

    HB_EXTERN void *hb_blob_get_user_data (hb_blob_t *blob, hb_user_data_key_t *key)

    HB_EXTERN void  hb_blob_make_immutable (hb_blob_t *blob)

    HB_EXTERN hb_bool_t hb_blob_is_immutable (hb_blob_t *blob)

    HB_EXTERN unsigned int hb_blob_get_length (hb_blob_t *blob)

    HB_EXTERN const char *hb_blob_get_data (hb_blob_t *blob, unsigned int *length)

    HB_EXTERN char *hb_blob_get_data_writable (hb_blob_t *blob, unsigned int *length)

#wrapping hb-buffer
cdef extern from hb-buffer.h:
	ctypedef struct hb_glyph_info_t:
        hb_codepoint_t codepoint
        hb_mask_t      mask
        uint32_t       cluster
        hb_var_int_t   var1
        hb_var_int_t   var2

    ctypedef struct hb_glyph_position_t:
        hb_position_t  x_advance
        hb_position_t  y_advance
        hb_position_t  x_offset
        hb_position_t  y_offset
        hb_var_int_t   var

    ctypedef struct hb_segment_properties_t:
    	hb_direction_t  direction;
        hb_script_t     script;
        hb_language_t   language;
        #/*< private >*/
        void           *reserved1;
        void           *reserved2;



    HB_EXTERN hb_bool_t hb_segment_properties_equal (const hb_segment_properties_t *a,const hb_segment_properties_t *b)

    HB_EXTERN unsigned int hb_segment_properties_hash (const hb_segment_properties_t *p)

    ctypedef struct hb_buffer_t hb_buffer_t

    HB_EXTERN hb_buffer_t *hb_buffer_create (void)

    HB_EXTERN hb_buffer_t *hb_buffer_get_empty (void)

    HB_EXTERN hb_buffer_t *hb_buffer_reference (hb_buffer_t *buffer);
    HB_EXTERN void hb_buffer_destroy (hb_buffer_t *buffer)

    HB_EXTERN hb_bool_t hb_buffer_set_user_data (hb_buffer_t *buffer, hb_user_data_key_t *key, void *data, hb_destroy_func_t   destroy, hb_bool_t replace)

    HB_EXTERN void *hb_buffer_get_user_data (hb_buffer_t *buffer,hb_user_data_key_t *key)

    ctypedef enum hb_buffer_content_type_t:
        HB_BUFFER_CONTENT_TYPE_INVALID = 0,
        HB_BUFFER_CONTENT_TYPE_UNICODE,
        HB_BUFFER_CONTENT_TYPE_GLYPHS


    HB_EXTERN void hb_buffer_set_content_type (hb_buffer_t *buffer,b_buffer_content_type_t  content_type)

    HB_EXTERN hb_buffer_content_type_t hb_buffer_get_content_type (hb_buffer_t *buffer)

    HB_EXTERN void hb_buffer_set_unicode_funcs (hb_buffer_t        *buffer, hb_unicode_funcs_t *unicode_funcs)

    HB_EXTERN hb_unicode_funcs_t *hb_buffer_get_unicode_funcs (hb_buffer_t        *buffer)

    HB_EXTERN void hb_buffer_set_direction (hb_buffer_t    *buffer,hb_direction_t  direction)

    HB_EXTERN hb_direction_t hb_buffer_get_direction (hb_buffer_t *buffer)

    HB_EXTERN void hb_buffer_set_script (hb_buffer_t *buffer, hb_script_t  script)
    
    HB_EXTERN hb_script_t hb_buffer_get_script (hb_buffer_t *buffer)

    HB_EXTERN void hb_buffer_set_language (hb_buffer_t   *buffer, hb_language_t  language)

    HB_EXTERN hb_language_t hb_buffer_get_language (hb_buffer_t *buffer)

    HB_EXTERN void hb_buffer_set_segment_properties (hb_buffer_t *buffer, const hb_segment_properties_t *props)

    HB_EXTERN void hb_buffer_get_segment_properties (hb_buffer_t *buffer, hb_segment_properties_t *props)

    HB_EXTERN void hb_buffer_guess_segment_properties (hb_buffer_t *buffer)

    ctypedef enum hb_buffer_flags_t: 
        HB_BUFFER_FLAG_DEFAULT			= 0x00000000u,
        HB_BUFFER_FLAG_BOT				= 0x00000001u, /* Beginning-of-text */
        HB_BUFFER_FLAG_EOT				= 0x00000002u, /* End-of-text */
        HB_BUFFER_FLAG_PRESERVE_DEFAULT_IGNORABLES	= 0x00000004u

    HB_EXTERN void hb_buffer_set_flags (hb_buffer_t       *buffer, hb_buffer_flags_t  flags)

    HB_EXTERN hb_buffer_flags_t hb_buffer_get_flags (hb_buffer_t *buffer)

    ctypedef enum hb_buffer_cluster_level_t:
    	HB_BUFFER_CLUSTER_LEVEL_MONOTONE_GRAPHEMES	= 0,
        HB_BUFFER_CLUSTER_LEVEL_MONOTONE_CHARACTERS	= 1,
        HB_BUFFER_CLUSTER_LEVEL_CHARACTERS		= 2,
        HB_BUFFER_CLUSTER_LEVEL_DEFAULT = HB_BUFFER_CLUSTER_LEVEL_MONOTONE_GRAPHEMES


    HB_EXTERN void hb_buffer_set_cluster_level (hb_buffer_t *buffer, hb_buffer_cluster_level_t  cluster_level)

    HB_EXTERN hb_buffer_cluster_level_t hb_buffer_get_cluster_level (hb_buffer_t *buffer)

#doubt 3 ?how to solve this?
#define HB_BUFFER_REPLACEMENT_CODEPOINT_DEFAULT 0xFFFDu

    HB_EXTERN void hb_buffer_set_replacement_codepoint (hb_buffer_t    *buffer, hb_codepoint_t  replacement)
 
    HB_EXTERN hb_codepoint_t hb_buffer_get_replacement_codepoint (hb_buffer_t    *buffer)


    HB_EXTERN void hb_buffer_reset (hb_buffer_t *buffer)

    HB_EXTERN void hb_buffer_clear_contents (hb_buffer_t *buffer)

    HB_EXTERN hb_bool_t hb_buffer_pre_allocate (hb_buffer_t  *buffer, unsigned int  size)

    HB_EXTERN hb_bool_t hb_buffer_allocation_successful (hb_buffer_t  *buffer)

    HB_EXTERN void hb_buffer_reverse (hb_buffer_t *buffer)

    HB_EXTERN void hb_buffer_reverse_range (hb_buffer_t *buffer,unsigned int start, unsigned int end)

    HB_EXTERN void hb_buffer_reverse_clusters (hb_buffer_t *buffer)

    HB_EXTERN void hb_buffer_add (hb_buffer_t *buffer, hb_codepoint_t  codepoint, unsigned int    cluster)

    HB_EXTERN void hb_buffer_add_utf8 (hb_buffer_t *buffer, const char   *text, int text_length,unsigned int  item_offset,int item_length)

    HB_EXTERN void hb_buffer_add_utf16 (hb_buffer_t  *buffer,const uint16_t *text,int text_length,unsigned int    item_offset,int item_length)

    HB_EXTERN void hb_buffer_add_utf32 (hb_buffer_t *buffer, const uint32_t *text, int text_length, unsigned int item_offset,int item_length)

    HB_EXTERN void hb_buffer_add_latin1 (hb_buffer_t *buffer, const uint8_t *text,int text_length,unsigned int   item_offset,int  item_length)

    HB_EXTERN void hb_buffer_add_codepoints (hb_buffer_t *buffer,const hb_codepoint_t *text, int  text_length, unsigned int   item_offset,int   item_length)

    HB_EXTERN hb_bool_t hb_buffer_set_length (hb_buffer_t  *buffer, unsigned int  length);
    HB_EXTERN unsigned int hb_buffer_get_length (hb_buffer_t *buffer)

    HB_EXTERN hb_glyph_info_t *hb_buffer_get_glyph_infos (hb_buffer_t  *buffer, unsigned int *length)

    HB_EXTERN hb_glyph_position_t *hb_buffer_get_glyph_positions (hb_buffer_t  *buffer,unsigned int *length)

    HB_EXTERN void hb_buffer_normalize_glyphs (hb_buffer_t *buffer)


    ctypedef enum hb_buffer_serialize_flags_t:
    	HB_BUFFER_SERIALIZE_FLAG_DEFAULT		= 0x00000000u,
        HB_BUFFER_SERIALIZE_FLAG_NO_CLUSTERS		= 0x00000001u,
        HB_BUFFER_SERIALIZE_FLAG_NO_POSITIONS		= 0x00000002u,
        HB_BUFFER_SERIALIZE_FLAG_NO_GLYPH_NAMES	= 0x00000004u,
        HB_BUFFER_SERIALIZE_FLAG_GLYPH_EXTENTS	= 0x00000008u
    
    ctypedef enum hb_buffer_serialize_format_t:
    	HB_BUFFER_SERIALIZE_FORMAT_TEXT	= HB_TAG('T','E','X','T'),
        HB_BUFFER_SERIALIZE_FORMAT_JSON	= HB_TAG('J','S','O','N'),
        HB_BUFFER_SERIALIZE_FORMAT_INVALID	= HB_TAG_NONE

    HB_EXTERN hb_buffer_serialize_format_t hb_buffer_serialize_format_from_string (const char *str, int len)

    HB_EXTERN const char *hb_buffer_serialize_format_to_string (hb_buffer_serialize_format_t format)

    HB_EXTERN const char **hb_buffer_serialize_list_formats (void);

    HB_EXTERN unsigned int hb_buffer_serialize_glyphs (hb_buffer_t *buffer,unsigned int start,
			    unsigned int end,
			    char *buf,
			    unsigned int buf_size,
			    unsigned int *buf_consumed,
			    hb_font_t *font,
			    hb_buffer_serialize_format_t format,
			    hb_buffer_serialize_flags_t flags)
    HB_EXTERN hb_bool_t hb_buffer_deserialize_glyphs (hb_buffer_t *buffer,
			      const char *buf,
			      int buf_len,
			      const char **end_ptr,
			      hb_font_t *font,
			      hb_buffer_serialize_format_t format)

    ctypedef hb_bool_t	(*hb_buffer_message_func_t)	(hb_buffer_t *buffer,
							 hb_font_t   *font,
							 const char  *message,
							 void        *user_data)

    HB_EXTERN void hb_buffer_set_message_func (hb_buffer_t *buffer,
			    hb_buffer_message_func_t func,
			    void *user_data, hb_destroy_func_t destroy)
