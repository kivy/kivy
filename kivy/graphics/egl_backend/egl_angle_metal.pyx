# distutils: language = c++
from kivy.graphics.egl_backend.egl_angle_metal cimport MetalANGLEGraphicsContext, EGLMetalANGLE

cdef class EGLMetalANGLE:

    cdef void set_native_layer(self, void * native_layer) except *:
        self.native_layer = native_layer

    cdef void create_context(self):
        self.ctx = new MetalANGLEGraphicsContext(self.native_layer)

    cdef void swap_buffers(self):
        self.ctx.swapBuffersEGL()

    cdef void destroy_context(self):
        del self.ctx
