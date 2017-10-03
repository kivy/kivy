'''
texture_from_pixmap
'''

from kivy.graphics.cgl cimport XID, Window, GLXDrawable
from libc.stdint cimport uintptr_t
from libc.stdio cimport fprintf, stderr
from libc.string cimport strlen

DEF GLX_BIND_TO_TEXTURE_RGBA_EXT = 0x20D1
DEF GLX_DRAWABLE_TYPE = 0x8010
DEF GLX_PIXMAP_BIT = 0x00000002
DEF GLX_RGBA = 4
DEF GLX_DEPTH_SIZE = 12
DEF GLX_BIND_TO_TEXTURE_TARGETS_EXT = 0x20D3
DEF GLX_TEXTURE_2D_BIT_EXT = 0x00000002
DEF GLX_DOUBLEBUFFER = 5
DEF GLX_Y_INVERTED_EXT = 0x20D4
DEF GLX_DONT_CARE = 0xFFFFFFFF
DEF GLX_TEXTURE_TARGET_EXT = 0x20D6
DEF GLX_TEXTURE_2D_EXT = 0x20DC
DEF GLX_TEXTURE_FORMAT_EXT = 0x20D5
DEF GLX_TEXTURE_FORMAT_RGB_EXT = 0x20D9
DEF GLX_TEXTURE_FORMAT_RGBA_EXT = 0x20DA
DEF GLX_FRONT_EXT = 0x20DE

cdef extern from "X11/Xlib.h":
    ctypedef struct XErrorEvent:
        Display *display
        XID resourceid
        unsigned long serial
        unsigned char error_code
        unsigned char request_code
        unsigned char minor_code

    cdef void XFree(void *data)

    ctypedef int (*XErrorHandler)(Display *d, XErrorEvent *e)
    cdef XErrorHandler XSetErrorHandler(XErrorHandler)
    cdef void XGetErrorText(Display *, unsigned char, char *, int)

cdef extern from "GL/glx.h":
    GLXPixmap glXCreatePixmap(Display *, GLXFBConfig, Pixmap, const int *);
    GLXFBConfig *glXChooseFBConfig(Display *, int , const int *, int *);
    XVisualInfo *glXChooseVisual( Display *, int , int *);
    GLXContext glXCreateContext( Display *, XVisualInfo *, GLXContext, Bool);


cdef int error_handler(Display *d, XErrorEvent *e):
    print(f'ERROR: error_code: {e.error_code}, request_code: {e.request_code}, minor_code: {e.minor_code}')

    cdef char buf[255]
    XGetErrorText(d, e.error_code, buf, 255)
    print(f'ERROR Message: {buf}')

XSetErrorHandler(error_handler)

cdef GLXPixmap bindTexImage(Pixmap pixmap):
    from kivy.core.window import Window as KivyWindow

    _disp = <uintptr_t>KivyWindow.get_xdisplay()
    cdef Display *xdisplay = <Display *>_disp

    _win = <uintptr_t>KivyWindow.get_xwindow()
    cdef unsigned long xwindow = <Window>_win

    cdef int *pixmap_config = [
        GLX_BIND_TO_TEXTURE_RGBA_EXT, True,
        GLX_DRAWABLE_TYPE, GLX_PIXMAP_BIT,
        GLX_BIND_TO_TEXTURE_TARGETS_EXT, GLX_TEXTURE_2D_BIT_EXT,
        GLX_DOUBLEBUFFER, False,
        GLX_Y_INVERTED_EXT, GLX_DONT_CARE,
        0x8000
    ]

    cdef int c = 0
    cdef GLXFBConfig *configs = glXChooseFBConfig(xdisplay, 0, pixmap_config, &c);

    if not configs:
        print('No appropriate GLX FBConfig available!')

    cdef int *pixmap_attribs = [
        GLX_TEXTURE_TARGET_EXT, GLX_TEXTURE_2D_EXT,
        GLX_TEXTURE_FORMAT_EXT, GLX_TEXTURE_FORMAT_RGBA_EXT,
        0x8000
    ]

    glxpixmap = glXCreatePixmap(xdisplay, configs[0], pixmap, pixmap_attribs)

    XFree(configs)

    cgl.glx.glXBindTexImageEXT(xdisplay, glxpixmap, GLX_FRONT_EXT, NULL)
    return glxpixmap

cdef void releaseTexImage(GLXPixmap pixmap):
    from kivy.core.window import Window as KivyWindow
    from kivy.core.window.window_x11 import WindowX11

    _disp = <uintptr_t>KivyWindow.get_xdisplay()
    cdef Display *xdisplay = <Display *>_disp

    cgl.glx.glXReleaseTexImageEXT(xdisplay, pixmap, GLX_FRONT_EXT)
