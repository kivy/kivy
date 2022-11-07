from kivy.graphics.fbo cimport Fbo
from kivy.graphics.context_instructions cimport Translate, Scale
from kivy.graphics.vertex_instructions cimport VertexInstruction


cdef class BoxShadow(Fbo):

    cdef list _pos
    cdef list _size
    cdef list _offset
    cdef list _border_radius
    cdef float _blur_radius
    cdef float _spread_radius
    cdef VertexInstruction _rect
    cdef Scale _fbo_scale
    cdef Translate _fbo_translate

    cdef void _init_texture(self)
    cdef void _update_canvas(self)
    cdef void _update_fbo(self)
    cdef void _update_shadow(self)
    cdef list _adjusted_pos(self)
    cdef list _adjusted_size(self)
    cdef float _check_float(self, str property_name, object value, str iter_text=?)
    cdef list _check_iter(self, str property_name, object value, int components=?)
