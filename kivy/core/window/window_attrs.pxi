include "../../include/config.pxi"

IF USE_WAYLAND:
    cdef extern from "wayland-client-protocol.h":
        cdef struct wl_display:
            pass

        cdef struct wl_surface:
            pass

        cdef struct wl_shell_surface:
            pass

IF USE_X11:
    cdef extern from "X11/Xlib.h":
        cdef struct _XDisplay:
            pass

        ctypedef _XDisplay Display

        ctypedef int XID
        ctypedef XID Window

IF UNAME_SYSNAME == 'Windows':
    cdef extern from "windows.h":
        ctypedef void *HANDLE

        ctypedef HANDLE HWND
        ctypedef HANDLE HDC
        ctypedef HANDLE HINSTANCE
