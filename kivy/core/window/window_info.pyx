include "../../include/config.pxi"

IF USE_WAYLAND:
    cdef class WindowInfoWayland:
        @property
        def display(self):
            return <uintptr_t>self.display

        @property
        def surface(self):
            return <uintptr_t>self.surface

        @property
        def shell_surface(self):
            return <uintptr_t>self.shell_surface


IF USE_X11:
    cdef class WindowInfoX11:
        @property
        def display(self):
            return <uintptr_t>self.display

        @property
        def window(self):
            return <uintptr_t>self.window

IF UNAME_SYSNAME == 'Windows':
    cdef class WindowInfoWindows:
        @property
        def window(self):
            return <uintptr_t>self.window

        @property
        def hdc(self):
            return <uintptr_t>self.hdc
