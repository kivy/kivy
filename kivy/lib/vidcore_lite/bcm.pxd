

cdef extern from "/opt/vc/include/bcm_host.h":
    ctypedef int int32_t
    ctypedef unsigned short int	uint16_t
    ctypedef unsigned int		uint32_t
    
    ctypedef uint32_t DISPMANX_DISPLAY_HANDLE_T
    ctypedef uint32_t DISPMANX_UPDATE_HANDLE_T
    ctypedef uint32_t DISPMANX_ELEMENT_HANDLE_T
    ctypedef uint32_t DISPMANX_RESOURCE_HANDLE_T
    ctypedef uint32_t DISPMANX_PROTECTION_T
    
    struct tag_VC_RECT_T:
        int32_t x
        int32_t y
        int32_t width
        int32_t height
        
    ctypedef tag_VC_RECT_T VC_RECT_T
        
    ctypedef enum DISPMANX_TRANSFORM_T:
        pass
        
    ctypedef struct DISPMANX_CLAMP_T:
        pass
        
    ctypedef struct VC_DISPMANX_ALPHA_T:
        pass
    
    void bcm_host_init()
    void bcm_host_deinit()
    
    int32_t c_get_display_size "graphics_get_display_size" (uint16_t display_number,
                                      uint32_t *width, uint32_t *height)
    DISPMANX_DISPLAY_HANDLE_T vc_dispmanx_display_open( uint32_t device )
    DISPMANX_UPDATE_HANDLE_T vc_dispmanx_update_start( int32_t priority )
    DISPMANX_ELEMENT_HANDLE_T vc_dispmanx_element_add ( DISPMANX_UPDATE_HANDLE_T update, 
                                                        DISPMANX_DISPLAY_HANDLE_T display,
                                                        int32_t layer, 
                                                        VC_RECT_T *dest_rect, 
                                                        DISPMANX_RESOURCE_HANDLE_T src,
                                                        VC_RECT_T *src_rect, 
                                                        DISPMANX_PROTECTION_T protection, 
                                                        VC_DISPMANX_ALPHA_T *alpha,
                                                        DISPMANX_CLAMP_T *clamp, 
                                                        DISPMANX_TRANSFORM_T transform )
    int vc_dispmanx_update_submit_sync( DISPMANX_UPDATE_HANDLE_T update )

cdef public uint32_t DISPMANX_PROTECTION_NONE = 0

cdef class Rect:
    cdef:
        VC_RECT_T _vc_rect


cdef class DisplayHandle:
    cdef DISPMANX_DISPLAY_HANDLE_T _handle
    
cdef class UpdateHandle:
    cdef DISPMANX_UPDATE_HANDLE_T _handle
    
cdef class ResourceHandle:
    cdef DISPMANX_RESOURCE_HANDLE_T _handle
    
cdef class ProtectionHandle:
    cdef DISPMANX_PROTECTION_T _handle
    
cdef class ElementHandle:
    cdef DISPMANX_ELEMENT_HANDLE_T _handle
