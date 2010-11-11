cdef class Canvas

from c_opengl cimport *
from buffer cimport Buffer
from graphics_instr_base cimport BindTexture
from graphics_vbo cimport VBO
from graphics_context cimport GraphicContext
from graphics_instruction cimport GraphicInstruction
from graphics_instr_vdi cimport VertexDataInstruction

cdef class CanvasAfter:
    cdef Canvas canvas

cdef class Canvas:
    cdef GraphicContext _context
    cdef VBO vertex_buffer
    cdef list texture_map
    cdef list _batch
    cdef list _batch_after
    cdef list _children
    cdef CanvasAfter _canvas_after

    cdef int _need_compile
    cdef int num_slices
    cdef list batch_slices

    cpdef trigger(self)
    cpdef add_canvas(self, Canvas canvas)
    cpdef remove_canvas(self, Canvas canvas)
    cdef add(self, GraphicInstruction instruction)
    cdef remove(self, GraphicInstruction instruction)
    cdef update(self, instruction)
    cdef compile_init(self)
    cdef list compile_strip_compiler(self, list batch)
    cdef compile(self)
    cdef compile_batch(self, list batch)
    cdef compile_children(self)
    cdef compile_slice(self, str command, list batch, slice_start, slice_end)
    cpdef draw(self)
    cdef _draw(self)
