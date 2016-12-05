
from libc.stdlib cimport malloc, free
from bcm cimport DISPMANX_ELEMENT_HANDLE_T, ElementHandle
cimport bcm

cdef extern from "/opt/vc/include/EGL/egl.h":
    ctypedef int EGLint ###maybe wrong
    ctypedef unsigned int EGLBoolean
    ctypedef unsigned int EGLenum
    ctypedef void *EGLNativeDisplayType
    ctypedef void *EGLNativePixmapType
    ctypedef void *EGLNativeWindowType
    ctypedef void *EGLConfig
    ctypedef void *EGLContext
    ctypedef void *EGLDisplay
    ctypedef void *EGLSurface
    ctypedef void *EGLClientBuffer

    ctypedef struct EGL_DISPMANX_WINDOW_T:
        DISPMANX_ELEMENT_HANDLE_T element
        int width   #/* This is necessary because dispmanx elements are not queriable. */
        int height

    EGLint eglGetError()
    EGLDisplay eglGetDisplay(EGLNativeDisplayType display_id)
    EGLBoolean eglInitialize(EGLDisplay dpy, EGLint *major, EGLint *minor)
    EGLBoolean eglTerminate(EGLDisplay dpy)
    char * eglQueryString(EGLDisplay dpy, EGLint name)
    EGLBoolean eglGetConfigs(EGLDisplay dpy, EGLConfig *configs,
             EGLint config_size, EGLint *num_config)
    EGLBoolean eglChooseConfig(EGLDisplay dpy, EGLint *attrib_list,
               EGLConfig *configs, EGLint config_size,
               EGLint *num_config)
    EGLBoolean eglGetConfigAttrib(EGLDisplay dpy, EGLConfig config,
                  EGLint attribute, EGLint *value)
    EGLSurface eglCreateWindowSurface(EGLDisplay dpy, EGLConfig config,
                  EGLNativeWindowType win,
                  EGLint *attrib_list)
    EGLSurface eglCreatePbufferSurface(EGLDisplay dpy, EGLConfig config,
                   EGLint *attrib_list)
    EGLSurface eglCreatePixmapSurface(EGLDisplay dpy, EGLConfig config,
                  EGLNativePixmapType pixmap,
                  EGLint *attrib_list)
    EGLBoolean eglDestroySurface(EGLDisplay dpy, EGLSurface surface)
    EGLBoolean eglQuerySurface(EGLDisplay dpy, EGLSurface surface,
               EGLint attribute, EGLint *value)
    EGLBoolean eglBindAPI(EGLenum api)
    EGLenum eglQueryAPI()
    EGLBoolean eglWaitClient()
    EGLBoolean eglReleaseThread()
    EGLSurface eglCreatePbufferFromClientBuffer(
          EGLDisplay dpy, EGLenum buftype, EGLClientBuffer buffer,
          EGLConfig config, EGLint *attrib_list)
    EGLBoolean eglSurfaceAttrib(EGLDisplay dpy, EGLSurface surface,
                EGLint attribute, EGLint value)
    EGLBoolean eglBindTexImage(EGLDisplay dpy, EGLSurface surface, EGLint buffer)
    EGLBoolean eglReleaseTexImage(EGLDisplay dpy, EGLSurface surface, EGLint buffer)
    EGLBoolean eglSwapInterval(EGLDisplay dpy, EGLint interval)
    EGLContext eglCreateContext(EGLDisplay dpy, EGLConfig config,
                EGLContext share_context,
                EGLint *attrib_list)
    EGLBoolean eglDestroyContext(EGLDisplay dpy, EGLContext ctx)
    EGLBoolean eglMakeCurrent(EGLDisplay dpy, EGLSurface draw,
              EGLSurface read, EGLContext ctx)
    EGLContext eglGetCurrentContext()
    EGLSurface eglGetCurrentSurface(EGLint readdraw)
    EGLDisplay eglGetCurrentDisplay()
    EGLBoolean eglQueryContext(EGLDisplay dpy, EGLContext ctx,
               EGLint attribute, EGLint *value)
    EGLBoolean eglWaitGL()
    EGLBoolean eglWaitNative(EGLint engine)
    EGLBoolean eglSwapBuffers(EGLDisplay dpy, EGLSurface surface)
    EGLBoolean eglCopyBuffers(EGLDisplay dpy, EGLSurface surface,
              EGLNativePixmapType target)

class _constants:
    EGL_VERSION_1_0 = 1 #
    EGL_VERSION_1_1 = 1 #
    EGL_VERSION_1_2 = 1 #
    EGL_VERSION_1_3 = 1 #
    EGL_VERSION_1_4 = 1 #

    ''' EGL Enumerants. Bitmasks and other exceptional cases aside, most
     * enums are assigned unique values starting at 0x3000.
     '''

    ''' EGL aliases '''
    EGL_FALSE = 0 #
    EGL_TRUE = 1 #

    ''' Out-of-band handle values '''
    EGL_DEFAULT_DISPLAY = 0 #
    EGL_NO_CONTEXT = 0 #
    EGL_NO_DISPLAY = 0 #
    EGL_NO_SURFACE = 0 #

    ''' Out-of-band attribute value '''
    EGL_DONT_CARE = -1 #

    ''' Errors / GetError return values '''
    EGL_SUCCESS = 0x3000 #
    EGL_NOT_INITIALIZED = 0x3001 #
    EGL_BAD_ACCESS = 0x3002 #
    EGL_BAD_ALLOC = 0x3003 #
    EGL_BAD_ATTRIBUTE = 0x3004 #
    EGL_BAD_CONFIG = 0x3005 #
    EGL_BAD_CONTEXT = 0x3006 #
    EGL_BAD_CURRENT_SURFACE = 0x3007 #
    EGL_BAD_DISPLAY = 0x3008 #
    EGL_BAD_MATCH = 0x3009 #
    EGL_BAD_NATIVE_PIXMAP = 0x300A #
    EGL_BAD_NATIVE_WINDOW = 0x300B #
    EGL_BAD_PARAMETER = 0x300C #
    EGL_BAD_SURFACE = 0x300D #
    EGL_CONTEXT_LOST = 0x300E # ''' EGL 1.1 - IMG_power_management '''

    ''' Reserved 0x300F-0x301F for additional errors '''

    ''' Reserved 0x3041-0x304F for additional config attributes '''

    ''' Config attribute values '''
    EGL_SLOW_CONFIG = 0x3050 # ''' EGL_CONFIG_CAVEAT value '''
    EGL_NON_CONFORMANT_CONFIG = 0x3051 # ''' EGL_CONFIG_CAVEAT value '''
    EGL_TRANSPARENT_RGB = 0x3052 # ''' EGL_TRANSPARENT_TYPE value '''
    EGL_RGB_BUFFER = 0x308E # ''' EGL_COLOR_BUFFER_TYPE value '''
    EGL_LUMINANCE_BUFFER = 0x308F # ''' EGL_COLOR_BUFFER_TYPE value '''

    ''' More config attribute values, for EGL_TEXTURE_FORMAT '''
    EGL_NO_TEXTURE = 0x305C #
    EGL_TEXTURE_RGB = 0x305D #
    EGL_TEXTURE_RGBA = 0x305E #
    EGL_TEXTURE_2D = 0x305F #

    ''' Config attribute mask bits '''
    EGL_PBUFFER_BIT = 0x0001 # ''' EGL_SURFACE_TYPE mask bits '''
    EGL_PIXMAP_BIT = 0x0002 # ''' EGL_SURFACE_TYPE mask bits '''
    EGL_WINDOW_BIT = 0x0004 # ''' EGL_SURFACE_TYPE mask bits '''
    EGL_VG_COLORSPACE_LINEAR_BIT = 0x0020 # ''' EGL_SURFACE_TYPE mask bits '''
    EGL_VG_ALPHA_FORMAT_PRE_BIT = 0x0040 # ''' EGL_SURFACE_TYPE mask bits '''
    EGL_MULTISAMPLE_RESOLVE_BOX_BIT = 0x0200 # ''' EGL_SURFACE_TYPE mask bits '''
    EGL_SWAP_BEHAVIOR_PRESERVED_BIT = 0x0400 # ''' EGL_SURFACE_TYPE mask bits '''

    EGL_OPENGL_ES_BIT = 0x0001 # ''' EGL_RENDERABLE_TYPE mask bits '''
    EGL_OPENVG_BIT = 0x0002 # ''' EGL_RENDERABLE_TYPE mask bits '''
    EGL_OPENGL_ES2_BIT = 0x0004 # ''' EGL_RENDERABLE_TYPE mask bits '''
    EGL_OPENGL_BIT = 0x0008 # ''' EGL_RENDERABLE_TYPE mask bits '''

    ''' QueryString targets '''
    EGL_VENDOR = 0x3053 #
    EGL_VERSION = 0x3054 #
    EGL_EXTENSIONS = 0x3055 #
    EGL_CLIENT_APIS = 0x308D #

    ''' QuerySurface / SurfaceAttrib / CreatePbufferSurface targets '''
    EGL_HEIGHT = 0x3056 #
    EGL_WIDTH = 0x3057 #
    EGL_LARGEST_PBUFFER = 0x3058 #
    EGL_TEXTURE_FORMAT = 0x3080 #
    EGL_TEXTURE_TARGET = 0x3081 #
    EGL_MIPMAP_TEXTURE = 0x3082 #
    EGL_MIPMAP_LEVEL = 0x3083 #
    EGL_RENDER_BUFFER = 0x3086 #
    EGL_VG_COLORSPACE = 0x3087 #
    EGL_VG_ALPHA_FORMAT = 0x3088 #
    EGL_HORIZONTAL_RESOLUTION = 0x3090 #
    EGL_VERTICAL_RESOLUTION = 0x3091 #
    EGL_PIXEL_ASPECT_RATIO = 0x3092 #
    EGL_SWAP_BEHAVIOR = 0x3093 #
    EGL_MULTISAMPLE_RESOLVE = 0x3099 #

    ''' EGL_RENDER_BUFFER values / BindTexImage / ReleaseTexImage buffer targets '''
    EGL_BACK_BUFFER = 0x3084 #
    EGL_SINGLE_BUFFER = 0x3085 #

    ''' OpenVG color spaces '''
    EGL_VG_COLORSPACE_sRGB = 0x3089 # ''' EGL_VG_COLORSPACE value '''
    EGL_VG_COLORSPACE_LINEAR = 0x308A # ''' EGL_VG_COLORSPACE value '''

    ''' OpenVG alpha formats '''
    EGL_VG_ALPHA_FORMAT_NONPRE = 0x308B # ''' EGL_ALPHA_FORMAT value '''
    EGL_VG_ALPHA_FORMAT_PRE = 0x308C # ''' EGL_ALPHA_FORMAT value '''

    ''' Constant scale factor by which fractional display resolutions &
     * aspect ratio are scaled when queried as integer values.
     '''
    EGL_DISPLAY_SCALING = 10000 #

    ''' Unknown display resolution/aspect ratio '''
    EGL_UNKNOWN = -1 #

    ''' Back buffer swap behaviors '''
    EGL_BUFFER_PRESERVED = 0x3094 # ''' EGL_SWAP_BEHAVIOR value '''
    EGL_BUFFER_DESTROYED = 0x3095 # ''' EGL_SWAP_BEHAVIOR value '''

    ''' CreatePbufferFromClientBuffer buffer types '''
    EGL_OPENVG_IMAGE = 0x3096 #

    ''' QueryContext targets '''
    EGL_CONTEXT_CLIENT_TYPE = 0x3097 #

    ''' CreateContext attributes '''
    EGL_CONTEXT_CLIENT_VERSION = 0x3098 #

    ''' Multisample resolution behaviors '''
    EGL_MULTISAMPLE_RESOLVE_DEFAULT = 0x309A # ''' EGL_MULTISAMPLE_RESOLVE value '''
    EGL_MULTISAMPLE_RESOLVE_BOX = 0x309B # ''' EGL_MULTISAMPLE_RESOLVE value '''

    ''' GetCurrentSurface targets '''
    EGL_DRAW = 0x3059 #
    EGL_READ = 0x305A #

    ''' WaitNative engines '''
    EGL_CORE_NATIVE_ENGINE = 0x305B #

    ''' EGL 1.2 tokens renamed for consistency in EGL 1.3 '''
    EGL_COLORSPACE = EGL_VG_COLORSPACE #
    EGL_ALPHA_FORMAT = EGL_VG_ALPHA_FORMAT #
    EGL_COLORSPACE_sRGB = EGL_VG_COLORSPACE_sRGB #
    EGL_COLORSPACE_LINEAR = EGL_VG_COLORSPACE_LINEAR #
    EGL_ALPHA_FORMAT_NONPRE = EGL_VG_ALPHA_FORMAT_NONPRE #
    EGL_ALPHA_FORMAT_PRE = EGL_VG_ALPHA_FORMAT_PRE #


    EGL_OPENGL_ES_API = 0x30A0
    EGL_OPENVG_API	=	0x30A1
    EGL_OPENGL_API	=	0x30A2

    EGL_BUFFER_SIZE	=		0x3020
    EGL_ALPHA_SIZE	=		0x3021
    EGL_BLUE_SIZE	=		0x3022
    EGL_GREEN_SIZE	=		0x3023
    EGL_RED_SIZE	=		0x3024
    EGL_DEPTH_SIZE	=		0x3025
    EGL_STENCIL_SIZE=		0x3026
    EGL_CONFIG_CAVEAT	=	0x3027
    EGL_CONFIG_ID		=	0x3028
    EGL_LEVEL	=		0x3029
    EGL_MAX_PBUFFER_HEIGHT	=	0x302A
    EGL_MAX_PBUFFER_PIXELS	=	0x302B
    EGL_MAX_PBUFFER_WIDTH	=	0x302C
    EGL_NATIVE_RENDERABLE	=	0x302D
    EGL_NATIVE_VISUAL_ID	=	0x302E
    EGL_NATIVE_VISUAL_TYPE	=	0x302F
    EGL_SAMPLES		=	0x3031
    EGL_SAMPLE_BUFFERS	=	0x3032
    EGL_SURFACE_TYPE	=	0x3033
    EGL_TRANSPARENT_TYPE	=	0x3034
    EGL_TRANSPARENT_BLUE_VALUE=	0x3035
    EGL_TRANSPARENT_GREEN_VALUE=	0x3036
    EGL_TRANSPARENT_RED_VALUE=	0x3037
    EGL_NONE	=		0x3038	#/* Attrib list terminator */
    EGL_BIND_TO_TEXTURE_RGB	=	0x3039
    EGL_BIND_TO_TEXTURE_RGBA=	0x303A
    EGL_MIN_SWAP_INTERVAL	=	0x303B
    EGL_MAX_SWAP_INTERVAL	=	0x303C
    EGL_LUMINANCE_SIZE	=	0x303D
    EGL_ALPHA_MASK_SIZE	=	0x303E
    EGL_COLOR_BUFFER_TYPE	=	0x303F
    EGL_RENDERABLE_TYPE	=	0x3040
    EGL_MATCH_NATIVE_PIXMAP	=	0x3041	#/* Pseudo-attribute (not queryable) */
    EGL_CONFORMANT	=		0x3042

EGL_FALSE = _constants.EGL_FALSE

global _context_reg
_context_reg = {}

cdef class Context:
    cdef EGLContext _eglcontext

global _display_reg
_display_reg = {}

cdef class Display:
    cdef EGLDisplay _egldisplay

global _surface_reg
_surface_reg = {}

cdef class Surface:
    cdef EGLSurface _eglsurface

global _config_reg
_config_reg = {}

cdef class Config:
    cdef EGLConfig _eglconfig


class EGLError(Exception):
    codes = {
        0x3000 : 'EGL_SUCCESS'			,
        0x3001 : 'EGL_NOT_INITIALIZED',
        0x3002 : 'EGL_BAD_ACCESS'		,
        0x3003 : 'EGL_BAD_ALLOC'		,
        0x3004 : 'EGL_BAD_ATTRIBUTE'	,
        0x3005 : 'EGL_BAD_CONFIG'		,
        0x3006 : 'EGL_BAD_CONTEXT'		,
        0x3007 : 'EGL_BAD_CURRENT_SURFACE',
        0x3008 : 'EGL_BAD_DISPLAY'		,
        0x3009 : 'EGL_BAD_MATCH'			,
        0x300A : 'EGL_BAD_NATIVE_PIXMAP',
        0x300B : 'EGL_BAD_NATIVE_WINDOW',
        0x300C : 'EGL_BAD_PARAMETER'	,
        0x300D : 'EGL_BAD_SURFACE'		,
        0x300E : 'EGL_CONTEXT_LOST'		,
        }


cdef class NativeWindow:
    cdef EGL_DISPMANX_WINDOW_T _window

    def __cinit__(self, ElementHandle element, int width, int height):
        self._window.element = element._handle
        self._window.width = width
        self._window.height = height


def raise_egl_error():
    err_code = getError()
    raise EGLError("%s (code x%x)"%(EGLError.codes[err_code], err_code))

def getError():
    return int(eglGetError())

def BindAPI(EGLenum api):
    cdef:
        EGLBoolean ret
    ret = eglBindAPI(api)
    return bool(ret)

def GetDisplay(unsigned int display_id):
    cdef:
        EGLDisplay display
        Display py_display
    display = eglGetDisplay(<EGLNativeDisplayType>display_id)
    if display == <EGLDisplay>0:
        raise EGLError("No display available")
    py_display = Display()
    py_display._egldisplay = display
    _display_reg[<int>display] = py_display
    return py_display

def Initialise(Display dpy):
    cdef:
        EGLint major
        EGLint minor
        EGLBoolean ret
    ret = eglInitialize(dpy._egldisplay, &major, &minor)
    if ret == EGL_FALSE:
        raise_egl_error()
    return (int(major), int(minor))

def Terminate(Display dpy):
    if eglTerminate(dpy._egldisplay) == EGL_FALSE:
        raise_egl_error()

def QueryString(Display dpy, EGLint name):
    cdef char *data
    data = eglQueryString(dpy._egldisplay, name)
    return data

def GetConfigs(Display dpy):
    cdef:
        EGLint numConfigs = -1
    if eglGetConfigs(dpy._egldisplay, NULL, 0, &numConfigs)==EGL_FALSE:
        raise_egl_error()
    return int(numConfigs)

### Not implemented the other calling method for this ###
#    EGLBoolean eglGetConfigs(EGLDisplay dpy, EGLConfig *configs,
#			 EGLint config_size, EGLint *num_config)

def ChooseConfig(Display dpy, list attrib_list, EGLint config_size):
    cdef:
        EGLConfig *configs
        EGLint num_config
        EGLint *attribs
        int i, n_attrib=len(attrib_list)

    attribs = <EGLint*>malloc(sizeof(EGLint)*n_attrib)
    configs = <EGLConfig*>malloc(sizeof(EGLConfig)*config_size)
    try:
        for i in xrange(n_attrib):
            attribs[i] = attrib_list[i]

        if eglChooseConfig(dpy._egldisplay, attribs,
                   configs, config_size, &num_config) == EGL_FALSE:
            raise_egl_error()
        chosen = []
        for i in xrange(num_config):
            cfg = Config()
            cfg._eglconfig = configs[i]
            chosen.append(cfg)
        return chosen
    finally:
        free(attribs)
        free(configs)

def GetConfigAttrib(Display dpy, Config config, EGLint attribute):
    cdef EGLint value
    if eglGetConfigAttrib(dpy._egldisplay, config._eglconfig,
                  attribute, &value) == EGL_FALSE:
        raise_egl_error()
    return int(value)

def CreateWindowSurface(Display dpy, Config config, NativeWindow win,
                        list attrib_list=[]):
    cdef:
        EGLSurface surf
        EGLint *attribs=NULL
        int i, n_attrib=len(attrib_list)

    if n_attrib > 0:
        attribs = <EGLint*>malloc(sizeof(EGLint)*n_attrib)
        for i in xrange(n_attrib):
            attribs[i] = attrib_list[i]
    try:
        surf = eglCreateWindowSurface(dpy._egldisplay, config._eglconfig,
                      <EGLNativeWindowType>(&(win._window)), attribs) #FIXME
        if surf == <EGLSurface>0:
            raise_egl_error()
        py_surf = Surface()
        py_surf._eglsurface = surf
        _surface_reg[<int>surf] = py_surf
        return py_surf
    finally:
        free(attribs)


def CreatePbufferSurface(Display dpy, Config config, list attrib_list):
    cdef:
        EGLSurface surf
        EGLint *attribs
        int i, n_attrib=len(attrib_list)

    attribs = <EGLint*>malloc(sizeof(EGLint)*n_attrib)
    try:
        for i in xrange(n_attrib):
            attribs[i] = attrib_list[i]

        surf = eglCreatePbufferSurface(dpy._egldisplay, config._eglconfig,
                      attribs)
        if surf == <EGLSurface>0:
            raise_egl_error()
        py_surf = Surface()
        py_surf._eglsurface = surf
        _surface_reg[<int>surf] = py_surf
        return py_surf
    finally:
        free(attribs)

#def CreatePixmapSurface(Display dpy, Config config, pixmap, list attrib_list):
#    cdef:
#        EGLSurface surf
#        EGLint *attribs
#        int i, n_attrib=len(attrib_list)
#
#    attribs = <EGLint*>malloc(sizeof(EGLint)*n_attrib)
#    try:
#        for i in xrange(n_attrib):
#            attribs[i] = attrib_list[i]
#
#        surf = eglCreatePixmapSurface(dpy._egldisplay, config._eglconfig,
#                      pixmap, attribs)
#        if surf == <EGLSurface>0:
#            raise_egl_error()
#        py_surf = Surface()
#        py_surf._eglsurface = surf
#        _surface_rep[<int>surf] = py_surf
#        return py_surf
#    finally:
#        free(attribs)

def DestroySurface(Display dpy, Surface surf):
    if eglDestroySurface(dpy._egldisplay, surf._eglsurface) == EGL_FALSE:
        raise_egl_error()
    del _surface_reg[<int>(surf._eglsurface)]

def QuerySurface(Display dpy, Surface surf, EGLint attrib):
    cdef EGLint ret
    if eglQuerySurface(dpy._egldisplay, surf._eglsurface,
               attrib, &ret) == EGL_FALSE:
        raise_egl_error()
    return ret

def QueryAPI():
    return eglQueryAPI()

def WaitClient():
    if eglWaitClient() == EGL_FALSE:
        raise_egl_error()

def ReleaseThread():
    if eglReleaseThread() == EGL_FALSE:
        raise_egl_error()

####
#def CreatePbufferFromClientBuffer(Display dpy, EGLenum buftype, buf,
#                    Config config, list attrib_list):
#    FIXME
#    EGLSurface eglCreatePbufferFromClientBuffer(
#	      EGLDisplay dpy, EGLenum buftype, EGLClientBuffer buffer,
#	      EGLConfig config, EGLint *attrib_list)


def SurfaceAttrib(Display dpy, Surface surf, EGLint attrib, EGLint value):
    cdef EGLBoolean ret
    ret = eglSurfaceAttrib(dpy._egldisplay, surf._eglsurface,
                            attrib, value)
    if ret==EGL_FALSE: raise_egl_error()

def BindTexImage(Display dpy, Surface surf, EGLint buf):
    if eglBindTexImage(dpy._egldisplay, surf._eglsurface, buf) == EGL_FALSE:
        raise_egl_error()

def ReleaseTexImage(Display dpy, Surface surf, EGLint buf):
    if eglReleaseTexImage(dpy._egldisplay, surf._eglsurface, buf) == EGL_FALSE:
        raise_egl_error()

def SwapInterval(Display dpy, EGLint interval):
    if eglSwapInterval(dpy._egldisplay, interval) == EGL_FALSE:
        raise_egl_error()

def CreateContext(Display dpy, Config config, object share_ctx, list attrib_list=[]):
    cdef:
        EGLContext _ctx, _share_ctx
        EGLint *attribs=NULL
        int i, n_attrib=len(attrib_list)

    if share_ctx is None:
        _share_ctx = <EGLContext>0
    elif isinstance(share_ctx, Context):
        _share_ctx = (<Context>share_ctx)._eglcontext
    else:
        raise ValueError("3rd argument (share context) must be of type Context or None")

    if n_attrib > 0:
        attribs = <EGLint*>malloc(sizeof(EGLint)*n_attrib)
    try:
        for i in xrange(n_attrib):
            attribs[i] = attrib_list[i]

        _ctx = eglCreateContext(dpy._egldisplay, config._eglconfig,
                    _share_ctx, attribs)
        pyctx = Context()
        pyctx._eglcontext = _ctx
        _context_reg[<int>_ctx] = pyctx
        return pyctx
    finally:
        free(attribs)

def DestroyContext(Display dpy, Context ctx):
    if eglDestroyContext(dpy._egldisplay, ctx._eglcontext) == EGL_FALSE:
        raise_egl_error()
    del _context_reg[<int>(ctx._eglcontext)]

def MakeCurrent(Display dpy, Surface draw, Surface read, Context ctx):
    if eglMakeCurrent(dpy._egldisplay, draw._eglsurface,
              read._eglsurface, ctx._eglcontext) == EGL_FALSE:
        raise_egl_error()

def GetCurrentContext():
    cdef EGLContext ctx
    ctx = eglGetCurrentContext()
    return _context_reg[<int>ctx]

def GetCurrentSurface(EGLint readdraw):
    cdef EGLSurface surf
    surf = eglGetCurrentSurface(readdraw)
    return _surface_reg[<int>surf]

def GetCurrentDisplay():
    cdef EGLDisplay dpy
    dpy = eglGetCurrentDisplay()
    return _display_reg[<int>dpy]

def QueryContext(Display dpy, Context ctx, EGLint attrib):
    cdef EGLint value
    if eglQueryContext(dpy._egldisplay, ctx._eglcontext,
                        attrib, &value) == EGL_FALSE:
        raise_egl_error()
    return value

def WaitGL():
    if eglWaitGL() == EGL_FALSE:
        raise_egl_error()

def WaitNative(EGLint engine):
    if eglWaitNative(engine) == EGL_FALSE:
        raise_egl_error()

def SwapBuffers(Display dpy, Surface surf):
    if eglSwapBuffers(dpy._egldisplay, surf._eglsurface) == EGL_FALSE:
        raise_egl_error()


#### Don't know what a NativePixmapType is or how to make one ###
#def CopyBuffers(Display dpy, Surface surf, target):
#    EGLBoolean eglCopyBuffers(EGLDisplay dpy, EGLSurface surface,
#			  EGLNativePixmapType target)
def bcm_display_open(bcm.uint32_t device):
    cdef:
        bcm.DISPMANX_DISPLAY_HANDLE_T disp
        bcm.DisplayHandle D
    disp = bcm.vc_dispmanx_display_open( device )
    if disp == 0:
        raise bcm.BCMDisplayException("Couldn't open handle to display")
    D = bcm.DisplayHandle()
    D._handle = disp
    return D

def bcm_update_start(bcm.int32_t priority):
    cdef:
        bcm.DISPMANX_UPDATE_HANDLE_T hdl
        bcm.UpdateHandle U
    hdl = bcm.vc_dispmanx_update_start( priority )
    if hdl == 0:
        raise bcm.BCMDisplayException("Couldn't open handle to update-start")
    U = bcm.UpdateHandle()
    U._handle = hdl
    return U

def bcm_element_add(bcm.UpdateHandle update,
                bcm.DisplayHandle display,
                bcm.int32_t layer,
                bcm.Rect dest_rect,
                bcm.Rect src_rect):
    cdef:
        bcm.DISPMANX_ELEMENT_HANDLE_T elem
        bcm.ElementHandle E
    elem = bcm.vc_dispmanx_element_add (update._handle,
                                     display._handle,
                                     layer,
                                     &(dest_rect._vc_rect),
                                     0, #DISPMANX_RESOURCE_HANDLE_T src,
                                     &(src_rect._vc_rect),
                                     0, #DISPMANX_PROTECTION_T protection,
                                     <bcm.VC_DISPMANX_ALPHA_T *>0, #VC_DISPMANX_ALPHA_T *alpha,
                                     <bcm.DISPMANX_CLAMP_T *>0, #DISPMANX_CLAMP_T *clamp,
                                     <bcm.DISPMANX_TRANSFORM_T>0) #DISPMANX_TRANSFORM_T transform
    E = bcm.ElementHandle()
    E._handle = elem
    return E

def bcm_update_submit_sync(bcm.UpdateHandle update):
    return bcm.vc_dispmanx_update_submit_sync( update._handle )

def WinCreate2(NativeWindow nativewindow, bcm.DisplayHandle display,
                    bcm.UpdateHandle update,
                    bcm.Rect dst, bcm.Rect src, display_id=0):
    cdef:
        bcm.int32_t success = 0
        bcm.DISPMANX_ELEMENT_HANDLE_T dispman_element
        bcm.DISPMANX_DISPLAY_HANDLE_T dispman_display
        bcm.DISPMANX_UPDATE_HANDLE_T dispman_update
        #bcm.VC_RECT_T dst_rect
        #bcm.VC_RECT_T src_rect
        bcm.uint32_t display_width
        bcm.uint32_t display_height

    ## create an EGL window surface, passing context width/height
    success = bcm.c_get_display_size(display_id, ## /* LCD */
                                            &display_width,
                                            &display_height);
    if ( success < 0 ):
        raise RuntimeError("Couldn't get display size")

    dispman_display = display._handle
    dispman_update = update._handle
    #dispman_update = bcm.vc_dispmanx_update_start( 0 )

    dispman_element = bcm.vc_dispmanx_element_add ( dispman_update, dispman_display,
        0, ##/*layer*/,
        &(dst._vc_rect),
        <bcm.DISPMANX_RESOURCE_HANDLE_T>0, ##/*src*/,
        &(src._vc_rect),
        <bcm.DISPMANX_PROTECTION_T>0,
        <bcm.VC_DISPMANX_ALPHA_T *>0, ##/*alpha*/
        <bcm.DISPMANX_CLAMP_T *>0, ##/*clamp*/
        <bcm.DISPMANX_TRANSFORM_T>0) ##/*transform*/

    nativewindow._window.element = dispman_element
    nativewindow._window.width = dst._vc_rect.width
    nativewindow._window.height = dst._vc_rect.height
    bcm.vc_dispmanx_update_submit_sync( dispman_update )
    return True
