



cdef class Rect:
    def __cinit__(self, int32_t x, int32_t y, int32_t width, int32_t height):
        self._vc_rect.x = x
        self._vc_rect.y = y
        self._vc_rect.width = width
        self._vc_rect.height = height
        
    property x:
        def __get__(self):
            return self._vc_rect.x
            
        def __set__(self, int32_t x):
            self._vc_rect.x = x
            
    property y:
        def __get__(self):
            return self._vc_rect.y
            
        def __set__(self, int32_t y):
            self._vc_rect.y = y
            
    property width:
        def __get__(self):
            return self._vc_rect.width
            
        def __set__(self, int32_t width):
            self._vc_rect.width = width
            
    property height:
        def __get__(self):
            return self._vc_rect.height
            
        def __set__(self, int32_t h):
            self._vc_rect.height = h
            
            
cdef class DisplayHandle:
    pass
    
cdef class UpdateHandle:
    pass
    
cdef class ResourceHandle:
    pass
    
cdef class ProtectionHandle:
    pass
    
cdef class ElementHandle:
    pass
    
    
class BCMDisplayException(Exception):
    pass
    
    
def host_init():
    bcm_host_init()
    
def host_deinit():
    bcm_host_deinit()
    
def graphics_get_display_size(uint16_t number):
    cdef:
        int32_t ret
        uint32_t width, height
        
    ret = c_get_display_size(number, &width, &height)
    if ret < 0:
        raise BCMDisplayException("Failed to get display size")
    return (width, height)

def display_open(uint32_t device):
    cdef:
        DISPMANX_DISPLAY_HANDLE_T disp
        DisplayHandle D
    disp = vc_dispmanx_display_open( 0 )
    print('Apenned display handle:', disp)
    if disp == 0:
        raise BCMDisplayException("Couldn't open handle to display")
    D = DisplayHandle()
    D._handle = disp
    return D
    
def update_start(int32_t priority):
    cdef DISPMANX_UPDATE_HANDLE_T hdl
    hdl = vc_dispmanx_update_start( priority )
    U = UpdateHandle()
    U._handle = hdl
    return U
    
def element_add(UpdateHandle update, 
                DisplayHandle display, 
                int32_t layer,
                Rect dest_rect,
                Rect src_rect):
    cdef:
        DISPMANX_ELEMENT_HANDLE_T elem
    elem = vc_dispmanx_element_add (update._handle, 
                                     display._handle,
                                     layer, 
                                     &(dest_rect._vc_rect), 
                                     0, #DISPMANX_RESOURCE_HANDLE_T src,
                                     &(src_rect._vc_rect), 
                                     0, #DISPMANX_PROTECTION_T protection, 
                                     <VC_DISPMANX_ALPHA_T *>0, #VC_DISPMANX_ALPHA_T *alpha,
                                     <DISPMANX_CLAMP_T *>0, #DISPMANX_CLAMP_T *clamp, 
                                     <DISPMANX_TRANSFORM_T>0) #DISPMANX_TRANSFORM_T transform
    E = ElementHandle()
    E._handle = elem
    return E
    
def update_submit_sync(UpdateHandle update):
    return vc_dispmanx_update_submit_sync( update._handle )
