include "window_attrs.pxi"

from libc.stdint cimport uintptr_t


cdef class WindowInfoWayland:
    cdef struct_wl_display *display
    cdef struct_wl_surface *surface
    cdef struct_wl_shell_surface *shell_surface
    cdef void set_display(self, void* display)
    cdef void set_surface(self, void* surface)
    cdef void set_shell_surface(self, void* shell_surface)

cdef class WindowInfoX11:
    cdef Display *display
    cdef Window window
    cdef void set_display(self, void* display)
    cdef void set_window(self, int window)

cdef class WindowInfoWindows:
    cdef HWND window
    cdef HDC hdc
    cdef void set_hwnd(self, void* hwnd)
    cdef void set_hdc(self, void* hdc)

cdef class WindowInfomacOS:
    cdef NSWindow *window
    cdef void set_window(self, void* window)

cdef class WindowInfoiOS:
    cdef UIWindow *window
    cdef void set_window(self, void* window)

cdef class WindowInfoAndroid:
    cdef ANativeWindow *window
    cdef EGLSurface surface
    cdef void set_window(self, void* window)
    cdef void set_surface(self, void* surface)