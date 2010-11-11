from buffer cimport Buffer
from graphics_instruction cimport GraphicInstruction
from graphics_instr_vdi cimport VertexDataInstruction

cdef class Path(VertexDataInstruction):
    cdef float pen_x, pen_y
    cdef list points
    cdef Buffer point_buffer

    cdef int add_point(self, float x, float y)
    cdef build_stroke(self)
    cdef build_fill(self)


cdef class PathInstruction(GraphicInstruction):
    cdef Path path

cdef class PathStart(PathInstruction):
    cdef int index

cdef class PathLineTo(PathInstruction):
    cdef int index

cdef class PathClose(PathInstruction):
    pass

cdef class PathFill(PathInstruction):
    pass

cdef class PathStroke(PathInstruction):
    pass

cdef class PathEnd(PathStroke):
    pass

