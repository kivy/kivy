include "window_attrs.pxi"

from libc.stdint cimport uintptr_t

IF USE_WAYLAND:
    cdef class WindowInfoWayland:
        cdef wl_display *display
        cdef wl_surface *surface
        cdef wl_shell_surface *shell_surface

IF USE_X11:
    cdef class WindowInfoX11:
        cdef Display *display
        cdef Window window

IF UNAME_SYSNAME == 'Windows':
    cdef class WindowInfoWindows:
        cdef HWND window
        cdef HDC hdc
