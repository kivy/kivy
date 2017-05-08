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

    HB_EXTERN hb_blob_t *hb_blob_create (const char *data, unsigned int length, hb_memory_mode_t mode,void *user_data,hb_destroy_func_t  destroy);

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
