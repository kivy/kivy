from kivy.graphics.fbo cimport Fbo
from kivy.graphics.context_instructions cimport Translate, Scale
from kivy.graphics.vertex_instructions cimport VertexInstruction


cdef class BoxShadow(Fbo):

    cdef bint _inset
    cdef float _blur_radius
    cdef tuple _pos
    cdef tuple _size
    cdef tuple _offset
    cdef tuple _border_radius
    cdef tuple _spread_radius
    cdef VertexInstruction _fbo_rect
    cdef VertexInstruction _texture_container
    cdef Scale _fbo_scale
    cdef Translate _fbo_translate

    cdef void _init_texture(self)
    cdef void _update_canvas(self)
    cdef void _update_fbo(self)
    cdef void _update_shadow(self)
    cdef tuple _adjusted_pos(self)
    cdef tuple _adjusted_size(self)
    cdef object _bounded_value(self, object value, min_value=?, max_value=?)
    cdef bint _check_bool(self, object value)
    cdef float _check_float(self, str property_name, object value, str iter_text=?)
    cdef tuple _check_iter(self, str property_name, object value, int components=?)
    
