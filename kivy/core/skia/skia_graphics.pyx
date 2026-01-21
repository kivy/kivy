import os
from libc.stdint cimport uint8_t
from libcpp.memory cimport unique_ptr
from libcpp.string cimport string
from libc.stdint cimport uintptr_t


# cdef extern from "<utility>" namespace "std":
#     cdef cppclass pair[T1, T2]:
#         T1 first
#         T2 second

cdef extern from "include/core/SkRefCnt.h":
    cdef cppclass sk_sp[T]:
        sk_sp() 
        sk_sp(T*) 
        
cdef extern from "include/core/SkSurface.h":
    cdef cppclass SkSurface

cdef extern from "include/core/SkCanvas.h":
    cdef cppclass SkCanvas

cdef extern from "include/gpu/ganesh/GrDirectContext.h":
    cdef cppclass GrDirectContext




cdef extern from "skia_gl_initialization.cpp":
    void initialize_gl_interface(bint use_angle)


cdef extern from "skia_surface_implem.cpp":
    ctypedef struct SkiaSurfaceData:
        sk_sp[SkSurface] surface
        SkCanvas* canvas
        sk_sp[GrDirectContext] context
    
    SkiaSurfaceData createSkiaSurfaceData(int width, int height) nogil
    void flush(sk_sp[GrDirectContext] context) nogil
    void flushAndSubmit(sk_sp[GrDirectContext] context) nogil
    void clearCanvas(SkCanvas *canvas, sk_sp[GrDirectContext] context, uint8_t r, uint8_t g, uint8_t b, uint8_t a) nogil


cdef extern from "skia_graphics_implem.cpp":
    void drawLottie(SkCanvas *canvas, sk_sp[GrDirectContext] context, const char*)
    void drawLottieNextFrame(SkCanvas *canvas, sk_sp[GrDirectContext] context, float t)
    void updateLottiePosAndSize(float x, float y, float width, float height)
    


cdef extern from "skia_graphics_implem.cpp" namespace "":
    cdef cppclass SkiaEllipse:
        SkiaEllipse() nogil

        void setGeometryAttrs(float x, float y, float w, float h, float angle_start, float angle_end, int segments) nogil
        void renderOnCanvas(SkCanvas *canvas) nogil

        void setTexture(const string& path) nogil
        void clearTexture() nogil




def initialize_skia_gl(use_angle):
    """initialize the interface for the gl backend. The interface has similar usage to kivy's "cgl.<gl function>".
    but it is accessed through interface->fFunctions.f<gl function> GL Interface initialization functions
    """
    initialize_gl_interface(use_angle)



cdef class Ellipse:
    cdef SkiaEllipse* thisptr

    def __cinit__(self):
        # cdef string tex = texture_path.encode("utf-8") if texture_path else string()
        self.thisptr = new SkiaEllipse()#x, y, w, h, segments, angle_start, angle_end, tex)

    def __dealloc__(self):
        del self.thisptr

    def set_geometry(self, float x, float y, float w, float h, float angle_start, float angle_end, int segments):
        """Update all ellipse properties"""
        with nogil:
            self.thisptr.setGeometryAttrs(x, y, w, h, angle_start, angle_end, segments)

    cpdef render(self, uintptr_t canvas_ptr):
        """Draw on surface canvas"""
        with nogil:
            self.thisptr.renderOnCanvas(<SkCanvas *>canvas_ptr)


# ==========================
    cpdef render2(self, Surface skia_surface):
        """Draw on surface canvas"""
        with nogil:
            self.thisptr.renderOnCanvas(<SkCanvas *>skia_surface.canvas)

    def set_texture(self, path: str):
        cdef string s = path.encode("utf-8")
        with nogil:
            self.thisptr.setTexture(s)

    # def clearTexture(self):
    #     with nogil:
    #         self.thisptr.clearTexture()


    # def drawDirect(self, uintptr_t canvas_ptr, float x, float y, float w, float h, 
    #                int segments, float angle_start, float angle_end):
    #     """Draw directly without updating object state - FASTEST drawing"""
    #     with nogil:
    #         self.thisptr.drawDirect(<SkCanvas *>canvas_ptr, x, y, w, h, 
    #                                segments, angle_start, angle_end)




cdef class Surface:
    
    cdef sk_sp[SkSurface] surface
    cdef SkCanvas *canvas
    cdef sk_sp[GrDirectContext] context

    def __init__(self, int width, int height):
        cdef SkiaSurfaceData surface_data = createSkiaSurfaceData(width, height)
        self.surface = surface_data.surface
        self.canvas = surface_data.canvas
        self.context = surface_data.context

    cpdef uintptr_t get_canvas_ptr(self):
        """Returns the SkCanvas pointer."""
        return <uintptr_t>self.canvas

    cpdef void flush(self):
        with nogil:
            flush(self.context)

    cpdef void flush_and_submit(self):
        with nogil:
            flushAndSubmit(self.context)

    cpdef void clear_canvas(self, uint8_t r, uint8_t g, uint8_t b, uint8_t a):
        with nogil:
            clearCanvas(self.canvas, self.context, r, g, b, a)


# ==========================
    cpdef void draw_lottie(self, str animation_path):
        cdef bytes encoded_path = animation_path.encode("utf-8")
        cdef const char* c_path = encoded_path
        drawLottie(self.canvas, self.context, c_path)

    cpdef lottie_seek(self, float t):
        drawLottieNextFrame(self.canvas, self.context, t)

    cpdef update_lottie_pos_and_size(self, float x, float y, float width, float height):
        updateLottiePosAndSize(x, y, width, height)

    
