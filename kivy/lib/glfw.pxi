include "../include/config.pxi"

#define GLFW_DLL

cdef extern from "GLFW/glfw3.h":
    ctypedef struct GLFWwindow
    ctypedef struct GLFWmonitor
    ctypedef struct GLFWvidmode:
        int width
        int height
        int redBits
        int greenBits
        int blueBits
        int refreshRate
    ctypedef struct GLFWimage:
        int width
        int height
        unsigned char* pixels

    ctypedef void (*GLFWcursorposfun)(GLFWwindow* window, double xpos, double ypos)
    ctypedef void (*GLFWcursorenterfun)(GLFWwindow* window, int entered)
    ctypedef void (*GLFWmousebuttonfun)(GLFWwindow* window, int button, int action, int mods)
    ctypedef void (*GLFWscrollfun)(GLFWwindow* window, double xoffset, double yoffset)
    ctypedef void (*GLFWkeyfun)(GLFWwindow* window, int key, int scancode, int action, int mods)
    ctypedef void (*GLFWwindowsizefun)(GLFWwindow* window, int width, int height)
    ctypedef void (*GLFWwindowposfun) (GLFWwindow *window, int xpos, int ypos)
    ctypedef void (*GLFWwindowiconifyfun)(GLFWwindow* window, int iconified)
    ctypedef void (*GLFWwindowmaximizefun)(GLFWwindow* window, int maximized)
    ctypedef void (*GLFWwindowfocusfun)(GLFWwindow* window, int focused)
    ctypedef void (*GLFWwindowrefreshfun)(GLFWwindow* window)
    ctypedef void (*GLFWframebuffersizefun)(GLFWwindow* window, int width, int height)
    ctypedef void (*GLFWerrorfun)(int error, const char* description)
    ctypedef void (*GLFWcharfun)(GLFWwindow* window, unsigned int codepoint)
    ctypedef void (*GLFWwindowclosefun)(GLFWwindow* window)

    cdef int GLFW_TRUE
    cdef int GLFW_FALSE

    cdef int GLFW_DONT_CARE
    cdef int GLFW_FLOATING
    cdef int GLFW_DECORATED
    cdef int GLFW_RESIZABLE
    cdef int GLFW_MAXIMIZED
    cdef int GLFW_DOUBLEBUFFER
    cdef int GLFW_DEPTH_BITS
    cdef int GLFW_STENCIL_BITS
    cdef int GLFW_RED_BITS
    cdef int GLFW_GREEN_BITS
    cdef int GLFW_BLUE_BITS
    cdef int GLFW_ALPHA_BITS
    cdef int GLFW_SAMPLES

    cdef int GLFW_PRESS
    cdef int GLFW_REPEAT
    cdef int GLFW_MOD_SHIFT
    cdef int GLFW_MOD_CONTROL
    cdef int GLFW_MOD_ALT
    cdef int GLFW_MOD_SUPER
    cdef int GLFW_MOD_CAPS_LOCK
    cdef int GLFW_MOD_NUM_LOCK

    cdef int GLFW_MOUSE_BUTTON_1
    cdef int GLFW_MOUSE_BUTTON_2
    cdef int GLFW_MOUSE_BUTTON_3
    cdef int GLFW_MOUSE_BUTTON_4
    cdef int GLFW_MOUSE_BUTTON_5
    cdef int GLFW_MOUSE_BUTTON_6
    cdef int GLFW_MOUSE_BUTTON_7
    cdef int GLFW_MOUSE_BUTTON_8
    cdef int GLFW_MOUSE_BUTTON_LAST = GLFW_MOUSE_BUTTON_8
    cdef int GLFW_MOUSE_BUTTON_LEFT = GLFW_MOUSE_BUTTON_1
    cdef int GLFW_MOUSE_BUTTON_RIGHT = GLFW_MOUSE_BUTTON_2
    cdef int GLFW_MOUSE_BUTTON_MIDDLE = GLFW_MOUSE_BUTTON_3

    cdef GLFWwindow* glfwCreateWindow(int width, int height, const char* title, GLFWmonitor* monitor, GLFWwindow* share)
    cdef GLFWmonitor* glfwGetPrimaryMonitor()
    cdef GLFWvidmode* glfwGetVideoMode(GLFWmonitor* monitor)
    cdef void glfwWaitEventsTimeout(double timeout)
    cdef void* glfwGetWindowUserPointer(GLFWwindow* window)
    cdef void glfwSetWindowUserPointer(GLFWwindow* window, void* pointer)
    cdef void glfwGetCursorPos(GLFWwindow* window, double* xpos, double* ypos)
    cdef void glfwGetWindowPos(GLFWwindow* window, int* xpos, int* ypos)
    cdef void glfwMakeContextCurrent(GLFWwindow* window)
    cdef void glfwSetWindowPos(GLFWwindow* window, int xpos, int ypos)
    cdef void glfwSetWindowTitle(GLFWwindow* window, const char* title)
    cdef void glfwSetCursorPosCallback(GLFWwindow* window, GLFWcursorposfun cbfun)
    cdef void glfwSetCursorEnterCallback(GLFWwindow* window, GLFWcursorenterfun cbfun)
    cdef void glfwSetMouseButtonCallback(GLFWwindow* window, GLFWmousebuttonfun cbfun)
    cdef void glfwSetKeyCallback(GLFWwindow* window, GLFWkeyfun cbfun)
    cdef void glfwSetScrollCallback(GLFWwindow* window, GLFWscrollfun cbfun)
    cdef void glfwSetWindowRefreshCallback(GLFWwindow* window, GLFWwindowrefreshfun cbfun)
    cdef void glfwSetWindowPosCallback(GLFWwindow* window, GLFWwindowposfun cbfun)
    cdef void glfwSetWindowSizeCallback(GLFWwindow* window, GLFWwindowsizefun cbfun)
    cdef void glfwSetWindowIconifyCallback(GLFWwindow* window, GLFWwindowiconifyfun cbfun)
    cdef void glfwSetWindowMaximizeCallback(GLFWwindow* window, GLFWwindowmaximizefun cbfun)
    cdef void glfwSetWindowFocusCallback(GLFWwindow* window, GLFWwindowfocusfun cbfun)
    cdef void glfwSetFramebufferSizeCallback(GLFWwindow* window, GLFWframebuffersizefun cbfun)  
    cdef void glfwSetErrorCallback(GLFWerrorfun cbfun)
    cdef void glfwSetCharCallback(GLFWwindow* window, GLFWcharfun cbfun)
    cdef void glfwSetWindowCloseCallback(GLFWwindow* window, GLFWwindowclosefun cbfun)
    cdef void glfwSetWindowIcon(GLFWwindow* window, int count, const GLFWimage* images)
    cdef void glfwSetWindowMonitor(GLFWwindow* window, GLFWmonitor* monitor, int xpos, int ypos, int width, int height, int refreshRate)
    cdef void glfwSetWindowSizeLimits(GLFWwindow* window, int minwidth, int minheight, int maxwidth, int maxheight)
    cdef void glfwGetFramebufferSize(GLFWwindow* window, int* width, int* height)
    cdef void glfwGetWindowSize(GLFWwindow* window, int* width, int* height)
    cdef void glfwSetWindowSize(GLFWwindow* window, int width, int height)
    cdef void glfwSetWindowShouldClose(GLFWwindow* window, int value)
    cdef void glfwMaximizeWindow(GLFWwindow* window)
    cdef void glfwIconifyWindow(GLFWwindow* window)
    cdef void glfwRestoreWindow(GLFWwindow* window)
    cdef void glfwFocusWindow(GLFWwindow* window)
    cdef void glfwHideWindow(GLFWwindow* window)
    cdef void glfwShowWindow(GLFWwindow* window)
    cdef void glfwSwapBuffers(GLFWwindow* window) nogil
    cdef void glfwDestroyWindow(GLFWwindow* window)
    cdef void glfwWindowHint(int hint, int value)
    cdef void glfwTerminate()
    cdef void glfwPollEvents()
    cdef void glfwWaitEvents()
    cdef int glfwWindowShouldClose(GLFWwindow* window)
    cdef int glfwInit()
    cdef int glfwSwapInterval(int interval)
    cdef int glfwSetWindowAttrib(GLFWwindow* window, int attrib, int value)
    cdef const char* glfwGetKeyName(int key, int scancode)
