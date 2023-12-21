cdef extern from "egl_angle_metal_implem.mm":
    cppclass MetalANGLEGraphicsContext:
        MetalANGLEGraphicsContext(void* nativeMetalLayer)
        void swapBuffersEGL()

cdef class EGLMetalANGLE:
    cdef MetalANGLEGraphicsContext* ctx
    cdef void* native_layer
    cdef void set_native_layer(self, void * native_layer) except *
    cdef void create_context(self)
    cdef void swap_buffers(self)
    cdef void destroy_context(self)