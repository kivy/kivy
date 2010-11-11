
cdef class VertexDataInstruction

from buffer cimport Buffer
from graphics_vbo cimport VBO
from graphics_instruction cimport GraphicInstruction
from graphics_vertex cimport vertex

cdef class VertexDataInstruction(GraphicInstruction):
    # canvas, vbo and texture to use with this element
    cdef VBO        vbo
    cdef object     _texture

    # local vertex buffers and vbo index storage
    cdef int        v_count   #vertex count
    cdef Buffer     v_buffer  #local buffer of vertex data
    cdef vertex*    v_data

    # local buffer of vertex indices on vbp
    cdef Buffer     i_buffer
    cdef int*       i_data

    # indices to draw.  e.g. [1,2,3], will draw triangle:
    #  self.v_data[0], self.v_data[1], self.v_data[2]
    cdef int*       element_data
    cdef Buffer     element_buffer
    cdef int        num_elements
    cdef bytes      _source

    cdef allocate_vertex_buffers(self, int num_verts)
    cdef update_vbo_data(self)
    cdef trigger_texture_update(self)


cdef class Triangle(VertexDataInstruction):
    cdef float _points[6]
    cdef float _tex_coords[6]

    cdef build(self)


cdef class Rectangle(VertexDataInstruction):
    cdef float x, y      #position
    cdef float w, h      #size
    cdef int _user_texcoords
    cdef float _tex_coords[8]
    cdef int _is_init

    cdef build(self)
    cdef trigger_texture_update(self)
    cdef set_tex_coords(self, coords)


cdef class BorderImage(VertexDataInstruction):
    cdef float x, y
    cdef float w, h
    cdef float _border[4]
    cdef float _tex_coords[8]

    cdef build(self)
    cdef trigger_texture_update(self)


cdef class Ellipse(VertexDataInstruction):
    cdef float x,y,w,h
    cdef int segments
    cdef tuple _tex_coords

    cdef build(self)

