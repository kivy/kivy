include "../../include/config.pxi"

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

    @property
    def native_handle(self):
        return <uintptr_t>self.surface

    cdef void set_display(self, void* display):
        self.display = <struct_wl_display *>display

    cdef void set_surface(self, void* surface):
        self.surface = <struct_wl_surface *>surface

    cdef void set_shell_surface(self, void* shell_surface):
        self.shell_surface = <struct_wl_shell_surface *>shell_surface

cdef class WindowInfoX11:
    @property
    def display(self):
        return <uintptr_t>self.display

    @property
    def window(self):
        return <uintptr_t>self.window

    @property
    def native_handle(self):
        return <uintptr_t>self.window

    cdef void set_display(self, void* display):
        self.display = <Display *>display

    cdef void set_window(self, int window):
        self.window = <Window>window


cdef class WindowInfoWindows:
    @property
    def window(self):
        return <uintptr_t>self.window

    @property
    def hdc(self):
        return <uintptr_t>self.hdc

    @property
    def native_handle(self):
        return <uintptr_t>self.window

    cdef void set_hwnd(self, void* hwnd):
        self.window = hwnd

    cdef void set_hdc(self, void* hdc):
        self.hdc = hdc


cdef class WindowInfomacOS:
    @property
    def window(self):
        return <uintptr_t>self.window

    @property
    def native_handle(self):
        return <uintptr_t>self.window

    cdef void set_window(self, void* window):
        self.window = _BridgedNSWindow(window)

cdef class WindowInfoiOS:
    @property
    def window(self):
        return <uintptr_t>self.window

    @property
    def native_handle(self):
        return <uintptr_t>self.window

    cdef void set_window(self, void* window):
        self.window = _BridgedUIWindow(window)


cdef class WindowInfoAndroid:
    @property
    def window(self):
        return <uintptr_t>self.window

    @property
    def surface(self):
        return <uintptr_t>self.surface

    @property
    def native_handle(self):
        return <uintptr_t>self.window

    cdef void set_window(self, void* window):
        self.window = <ANativeWindow *>window

    cdef void set_surface(self, void* surface):
        self.surface = <EGLSurface>surface
