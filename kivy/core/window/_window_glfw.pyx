include "../../../kivy/lib/glfw.pxi"

from kivy.logger import Logger
from kivy.config import Config

cdef void error_callback(int error, const char* description) with gil:
    Logger.error(f'Window: GLFW error {error} - {description}')

cdef void _cursor_pos_callback(GLFWwindow* window, double xpos, double ypos) with gil:
    window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
    window_object._cursor_pos_callback(xpos, ypos)

cdef void _cursor_enter_callback(GLFWwindow* window, int entered) with gil:
    cdef str eventname
    if entered == GLFW_TRUE:
        eventname = 'on_cursor_enter'
    else:
        eventname = 'on_cursor_leave'
    window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
    window_object._cursor_enter_callback(eventname)

cdef void _mouse_button_callback(GLFWwindow* window, int button,
                                 int action, int mods) with gil:
    cdef str mouse_button = 'last'
    if button == GLFW_MOUSE_BUTTON_1:
        mouse_button = 'left'
    elif button == GLFW_MOUSE_BUTTON_2:
        mouse_button = 'right'
    elif button == GLFW_MOUSE_BUTTON_3:
        mouse_button = 'middle'
    elif button == GLFW_MOUSE_BUTTON_4:
        mouse_button = 'mouse4'
    elif button == GLFW_MOUSE_BUTTON_5:
        mouse_button = 'mouse5'
    elif button == GLFW_MOUSE_BUTTON_6:
        mouse_button = 'mouse6'
    elif button == GLFW_MOUSE_BUTTON_7:
        mouse_button = 'mouse7'
    cdef str eventname = 'on_mouse_down' if action == GLFW_PRESS else 'on_mouse_up'
    cdef double xpos, ypos
    glfwGetCursorPos(window, &xpos, &ypos)
    window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
    window_object._mouse_button_callback(xpos, ypos, mouse_button, eventname)

cdef void _scroll_callback(GLFWwindow* window, double xoffset, double yoffset) with gil:
    cdef str button
    if yoffset > 0:
        button = 'scrolldown'
    elif yoffset < 0:
        button = 'scrollup'
    elif xoffset > 0:
        button = 'scrollright'
    elif xoffset < 0:
        button = 'scrollleft'
    cdef double xpos, ypos
    glfwGetCursorPos(window, &xpos, &ypos)
    window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
    window_object._scroll_callback(xpos, ypos, button)

cdef void _window_pos_callback(GLFWwindow* window, int xpos, int ypos) with gil:
    if xpos > 0 and ypos > 0:
        window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
        window_object._window_pos_callback()

cdef void _window_size_callback(GLFWwindow* window, int width, int height) with gil:
    if width > 0 and height > 0:
        window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
        window_object._window_size_callback(width, height)

cdef void _window_iconify_callback(GLFWwindow* window, int iconified) with gil:
    cdef str eventname
    if iconified == GLFW_TRUE:
        eventname = 'on_minimize'
    else:
        eventname = 'on_restore'
    window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
    window_object._window_iconify_callback(eventname)

cdef void _window_maximize_callback(GLFWwindow* window, int maximize) with gil:
    cdef str eventname
    if maximize == GLFW_TRUE:
        eventname = 'on_maximize'
    else:
        eventname = 'on_restore'
    window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
    window_object._window_maximize_callback(eventname)

cdef void _window_focus_callback(GLFWwindow* window, int focused) with gil:
    window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
    window_object._window_focus_callback(focused)

cdef void _window_refresh_callback(GLFWwindow* window) with gil:
    window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
    window_object._window_refresh_callback()

cdef void _key_callback(GLFWwindow* window, int key, int scancode,
                        int action, int mods) with gil:
    cdef const char* key_str = glfwGetKeyName(key, scancode)
    cdef str text
    if key_str == NULL:
        text = ''
    else:
        text = key_str.decode('utf-8')
    cdef str eventname
    if action in (GLFW_PRESS, GLFW_REPEAT):
        eventname = 'on_key_down'
    else:
        eventname = 'on_key_up'
    cdef list modifiers = []
    if mods & GLFW_MOD_SHIFT:
        modifiers.append('shift')
    if mods & GLFW_MOD_CONTROL:
        modifiers.append('ctrl')
    if mods & GLFW_MOD_ALT:
        modifiers.append('alt')
    if mods & GLFW_MOD_SUPER:
        modifiers.append('meta')
    if mods & GLFW_MOD_CAPS_LOCK:
        modifiers.append('capslock')
    if mods & GLFW_MOD_NUM_LOCK:
        modifiers.append('numlock')
    window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
    window_object._key_callback(eventname, key, scancode, text, modifiers)

cdef void _char_callback(GLFWwindow* window, unsigned int codepoint) with gil:
    window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
    window_object._char_callback(chr(codepoint))

cdef void _window_close_callback(GLFWwindow* window) with gil:
    window_object = <WindowGLFWStorage>glfwGetWindowUserPointer(window)
    if window_object.dispatch('on_request_close'):
        glfwSetWindowShouldClose(window, GLFW_FALSE)
    else:
        window_object.quit()


cdef class WindowGLFWStorage:

    cdef GLFWwindow *win
    cdef str _fullscreen
    cdef tuple _window_pos
    cdef tuple _window_size
    cdef object _window_object

    def __cinit__(self):
        self.win = NULL
        self._fullscreen = 'False'
        self._window_pos = (0, 0)
        self._window_size = (0, 0)
        self._window_object = None

    def __init__(self):
        if not glfwInit():
            raise Exception("Cannot init GLFW")
        glfwSetErrorCallback(error_callback)

    def setup_window(self, x, y, width, height, borderless, fullscreen):
        if borderless:
            glfwWindowHint(GLFW_DECORATED, GLFW_FALSE)

        self._window_pos = (x, y)
        self._window_size = (width, height)

        cdef GLFWmonitor* monitor = NULL
        if fullscreen == 'auto':
            width, height = self._get_monitor_size()
        if fullscreen is True or fullscreen == 'auto':
            monitor = glfwGetPrimaryMonitor()
            self._fullscreen = str(fullscreen)

        if not Config.getboolean('graphics', 'resizable'):
            glfwWindowHint(GLFW_RESIZABLE, GLFW_FALSE)

        glfwWindowHint(GLFW_DOUBLEBUFFER, 1)
        glfwWindowHint(GLFW_DEPTH_BITS, 16)
        glfwWindowHint(GLFW_STENCIL_BITS, 8)
        glfwWindowHint(GLFW_RED_BITS, 8)
        glfwWindowHint(GLFW_GREEN_BITS, 8)
        glfwWindowHint(GLFW_BLUE_BITS, 8)
        glfwWindowHint(GLFW_ALPHA_BITS, 8)  # at rpi should be 0 as I understand

        cdef int multisamples = Config.getint('graphics', 'multisamples')
        glfwWindowHint(GLFW_SAMPLES, min(4, multisamples))  # 0 disables multisampling

        vsync = Config.get('graphics', 'vsync')
        if vsync and vsync != 'none':
            vsync = Config.getint('graphics', 'vsync')
            Logger.debug(f'GLFW: setting vsync interval == {vsync}')
            glfwSwapInterval(vsync)

        self.win = glfwCreateWindow(width, height, b'', monitor, NULL)

        if not self.win:
            glfwTerminate()
            raise Exception("Cannot create window GLFW")

        if x and y:
            glfwSetWindowPos(self.win, x, y)

        glfwMakeContextCurrent(self.win)

        # Set pointer and callbacks
        glfwSetWindowUserPointer(self.win, <void *>self._window_object)
        glfwSetCursorPosCallback(self.win, _cursor_pos_callback)
        glfwSetCursorEnterCallback(self.win, _cursor_enter_callback)
        glfwSetMouseButtonCallback(self.win, _mouse_button_callback)
        glfwSetScrollCallback(self.win, _scroll_callback)
        glfwSetWindowPosCallback(self.win, _window_pos_callback)
        glfwSetWindowSizeCallback(self.win, _window_size_callback)
        glfwSetWindowIconifyCallback(self.win, _window_iconify_callback)
        glfwSetWindowMaximizeCallback(self.win, _window_maximize_callback)
        glfwSetWindowFocusCallback(self.win, _window_focus_callback)
        glfwSetWindowRefreshCallback(self.win, _window_refresh_callback)
        glfwSetWindowCloseCallback(self.win, _window_close_callback)
        glfwSetFramebufferSizeCallback(self.win, _window_size_callback)
        glfwSetKeyCallback(self.win, _key_callback)
        glfwSetCharCallback(self.win, _char_callback)
        return self.get_window_size()

    def _get_monitor_size(self):
        cdef GLFWmonitor* monitor = glfwGetPrimaryMonitor()
        cdef const GLFWvidmode* videomode = glfwGetVideoMode(monitor)
        cdef int width, height
        width = videomode.width
        height = videomode.height
        return width, height

    def set_window_object(self, _object):
        self._window_object = _object

    def _get_gl_size(self):
        if not self.win:  # will be crash without a window
            return 0, 0
        cdef int width, height
        glfwGetFramebufferSize(self.win, &width, &height)
        return width, height

    def set_window_icon(self, width, height, pixels):
        cdef GLFWimage images[1]
        images[0].width = width
        images[0].height = height
        images[0].pixels = <unsigned char*>pixels
        glfwSetWindowIcon(self.win, 1, images)

    def set_window_title(self, title):
        glfwSetWindowTitle(self.win, <bytes>title.encode('utf-8'))

    def get_window_pos(self):
        cdef int xpos, ypos
        glfwGetWindowPos(self.win, &xpos, &ypos)
        return xpos, ypos

    def set_window_pos(self, x, y):
        glfwSetWindowPos(self.win, x, y)

    def get_window_size(self):
        cdef int width, height
        glfwGetWindowSize(self.win, &width, &height)
        return width, height

    def set_minimum_size(self, minwidth, minheight):
        glfwSetWindowSizeLimits(self.win, minwidth, minheight,
                                GLFW_DONT_CARE, GLFW_DONT_CARE)

    def set_window_size(self, width, height):
        if self.get_window_size() != (width, height):
            glfwSetWindowSize(self.win, width, height)

    def set_window_border(self, borderless):
        glfwSetWindowAttrib(self.win, GLFW_DECORATED,
                            GLFW_FALSE if borderless else GLFW_TRUE)

    def set_always_on_top(self, always_on_top):
        glfwSetWindowAttrib(self.win, GLFW_FLOATING,
                            GLFW_TRUE if always_on_top else GLFW_FALSE)

    def set_fullscreen_mode(self, mode):
        # A few remarks:
        #   When switching to fullscreen mode, GLFW does
        #   not remember the current coordinates of the
        #   window. Thus, when setting fullscreen=False,
        #   the window moves to a point with coordinates
        #   (0, 0). To get rid of this problem, before
        #   switching to fullscreen mode, the current
        #   coordinates are stored in the _window_pos variable.
        #
        #   A similar problem with the window size. When
        #   setting the "auto" mode, the window gets the
        #   size of the current monitor and when changing the
        #   mode to another, the window size remains the same
        #   (such as the monitor).  The "real" window size is
        #   stored in the _window_size variable.
        #
        #   The _fullscreen variable store current window mode.

        cdef GLFWmonitor* monitor
        cdef int width, height, x, y

        if str(mode) != self._fullscreen:  # check if mode has been changed
            if mode == 'auto':
                self._window_size = self.get_window_size()
                width, height = self._get_monitor_size()
            else:
                width, height = self._window_size
            if mode is True or mode == 'auto':
                monitor = glfwGetPrimaryMonitor()
                x, y = 0, 0
                if self._fullscreen == 'True':
                    self._window_pos = self.get_window_pos()
            else:
                monitor = NULL
                x, y = self._window_pos
            self._fullscreen = str(mode)
            glfwSetWindowMonitor(self.win, monitor, x, y, width, height, GLFW_DONT_CARE)

    def maximize_window(self):
        glfwMaximizeWindow(self.win)

    def minimize_window(self):
        glfwIconifyWindow(self.win)

    def restore_window(self):
        glfwRestoreWindow(self.win)

    def raise_window(self):
        glfwFocusWindow(self.win)

    def hide_window(self):
        glfwHideWindow(self.win)

    def show_window(self):
        glfwShowWindow(self.win)

    def flip(self):
        with nogil:
            glfwSwapBuffers(self.win)

    def poll(self):
        if glfwWindowShouldClose(self.win):
            return ('quit', )
        glfwPollEvents()  # must only be called from the main thread

    def wait_events(self):
        glfwWaitEventsTimeout(1 / 60)  # 60 should be replaced with maxfps

    def terminate(self):
        glfwDestroyWindow(self.win)
        glfwTerminate()

    def mainloop(self):
        while not glfwWindowShouldClose(self.win):
            glfwSwapBuffers(self.win)
            glfwPollEvents()
            glfwWaitEvents()
        glfwTerminate()
