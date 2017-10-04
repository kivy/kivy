IF UNAME_SYSNAME == 'Windows':
    cdef extern from "WinNT.h":
        ctypedef void *HANDLE

    cdef extern from "WinDef.h":
        ctypedef HANDLE HWND
        ctypedef HANDLE HDC
        ctypedef HANDLE HINSTANCE

IF UNAME_SYSNAME == 'Linux':
    cdef extern from "X11/Xlib.h":
        cdef struct _XDisplay:
            pass

        ctypedef _XDisplay Display

        ctypedef int XID
        ctypedef XID Window

    cdef extern from "wayland-client-protocol.h":
        cdef struct wl_display:
            pass

        cdef struct wl_surface:
            pass

        cdef struct wl_shell_surface:
            pass


