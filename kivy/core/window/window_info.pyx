IF UNAME_SYSNAME == 'Linux':
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
        def hwnd(self):
            return <uintptr_t>self.hwnd

        @property
        def hdc(self):
            return <uintptr_t>self.hdc

        @property
        def hinstance(self):
            return <uintptr_t>self.hinstance
