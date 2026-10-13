include "../../include/config.pxi"


cdef class EGLBaseANGLE:

    cdef void set_native_layer(self, void * native_layer) except *:
        pass

    cdef void create_context(self):
        pass

    cdef void swap_buffers(self):
        pass

    cdef void destroy_context(self):
        pass


cdef class EGLANGLE:
    """
    EGLANGLE serves as a comprehensive wrapper for EGL*ANGLE classes,
    unifying their functionality across diverse platforms.

    Its primary purpose is to facilitate the creation and administration of
    the EGL context specifically tailored for the ANGLE backend.

    The concrete implementation of EGLANGLE is delegated to platform-specific classes,
    exemplified by EGLMetalANGLE designed for iOS and macOS.

    To ensure consistency and extensibility, all platform-specific classes are
    expected to have the same public interface as EGLBaseANGLE.

    For platforms without ANGLE support, EGLBaseANGLE acts as a no-op, serving
    as a placeholder for dummy implementation.
    """

    def __cinit__(self):
        self._initialize_angle_implementation()

    cdef void _initialize_angle_implementation(self):
        if PLATFORM in ('ios', 'darwin'):
            from kivy.graphics.egl_backend.egl_angle_metal import EGLMetalANGLE
            self._egl = <EGLBaseANGLE>EGLMetalANGLE()
        else:
            self._egl = EGLBaseANGLE()

    cdef void set_native_layer(self, void * native_layer) except *:
        self._egl.set_native_layer(native_layer)

    cdef void create_context(self):
        self._egl.create_context()

    cdef void swap_buffers(self):
        self._egl.swap_buffers()

    cdef void destroy_context(self):
        self._egl.destroy_context()
