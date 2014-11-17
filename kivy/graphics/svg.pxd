cdef class Matrix
cdef class Svg

from cython cimport view
from kivy.graphics.instructions cimport RenderContext
from kivy.graphics.texture cimport Texture
from kivy.graphics.vertex_instructions cimport StripMesh

from cpython cimport array
from array import array

ctypedef double matrix_t[6]

cdef class Matrix:
    cdef matrix_t mat
    cdef void transform(self, float ox, float oy, float *x, float *y)
    cpdef Matrix inverse(self)

cdef class Svg(RenderContext):
    cdef public double width
    cdef public double height
    cdef list paths
    cdef object transform
    cdef object fill
    cdef public object current_color
    cdef object stroke
    cdef float opacity
    cdef float x
    cdef float y
    cdef int close_index
    cdef list path
    cdef array.array loop
    cdef int bezier_points
    cdef int circle_points
    cdef public object gradients
    cdef view.array bezier_coefficients
    cdef float anchor_x
    cdef float anchor_y
    cdef double last_cx
    cdef double last_cy
    cdef Texture line_texture
    cdef StripMesh last_mesh

    cdef parse_tree(self, tree)
    cdef parse_element(seld, e)
    cdef list parse_transform(self, transform_def)
    cdef parse_path(self, pathdef)
    cdef void new_path(self)
    cdef void close_path(self)
    cdef void set_position(self, float x, float y, int absolute=*)
    cdef arc_to(self, float rx, float ry, float phi, float large_arc,
            float sweep, float x, float y)
    cdef void curve_to(self, float x1, float y1, float x2, float y2,
            float x, float y)
    cdef void end_path(self)
    cdef void push_mesh(self, float[:] path, fill, Matrix transform, mode)
    cdef void push_strip_mesh(self, float *vertices, int vindex, int count,
                              int mode=*)
    cdef void push_line_mesh(self, float[:] path, fill, Matrix transform)
    cdef void render(self)
