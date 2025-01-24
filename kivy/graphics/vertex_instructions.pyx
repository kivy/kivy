'''
Vertex Instructions
===================

This module includes all the classes for drawing simple vertex objects.

Updating properties
-------------------

The list attributes of the graphics instruction classes (e.g.
:attr:`Triangle.points`, :attr:`Mesh.indices` etc.) are not Kivy
properties but Python properties. As a consequence, the graphics will only
be updated when the list object itself is changed and not when list values
are modified.

For example in python:

.. code-block:: python

    class MyWidget(Button):

        triangle = ObjectProperty(None)
        def __init__(self, **kwargs):
            super(MyWidget, self).__init__(**kwargs)
            with self.canvas:
                self.triangle = Triangle(points=[0,0, 100,100, 200,0])

and in kv:

.. code-block:: kv

    <MyWidget>:
        text: 'Update'
        on_press:
            self.triangle.points[3] = 400

Although pressing the button will change the triangle coordinates,
the graphics will not be updated because the list itself has not
changed. Similarly, no updates will occur using any syntax that changes
only elements of the list e.g. self.triangle.points[0:2] = [10,10] or
self.triangle.points.insert(10) etc.
To force an update after a change, the list variable itself must be
changed, which in this case can be achieved with:

.. code-block:: kv

    <MyWidget>:
        text: 'Update'
        on_press:
            self.triangle.points[3] = 400
            self.triangle.points = self.triangle.points
'''

__all__ = ('Triangle', 'Quad', 'Rectangle', 'RoundedRectangle', 'BorderImage', 'Ellipse',
           'Line', 'Point', 'Mesh', 'GraphicException', 'Bezier', 'SmoothLine')


include "../include/config.pxi"
include "common.pxi"
include "memory.pxi"

from os import environ
from kivy.graphics.vbo cimport *
from kivy.graphics.vertex cimport *
from kivy.graphics.instructions cimport *
from kivy.graphics.cgl cimport *
from kivy.logger import Logger
from kivy.graphics.texture cimport Texture
from kivy.utils import platform

cdef int gles_limts = int(environ.get(
    'KIVY_GLES_LIMITS', int(platform not in ('win', 'macosx', 'linux'))))


class GraphicException(Exception):
    '''Exception raised when a graphics error is fired.
    '''

include "vertex_instructions_line.pxi"


cdef class Bezier(VertexInstruction):
    '''A 2d Bezier curve.

    .. versionadded:: 1.0.8

    :Parameters:
        `points`: list
            List of points in the format (x1, y1, x2, y2...)
        `segments`: int, defaults to 180
            Define how many segments are needed for drawing the curve.
            The drawing will be smoother if you have many segments.
        `loop`: bool, defaults to False
            Set the bezier curve to join the last point to the first.
        `dash_length`: int
            Length of a segment (if dashed), defaults to 1.
        `dash_offset`: int
            Distance between the end of a segment and the start of the
            next one, defaults to 0. Changing this makes it dashed.
    '''

    # TODO: refactoring:
    #
    #    a) find interface common to all splines (given control points and
    #    perhaps tangents, what's the position on the spline for parameter t),
    #
    #    b) make that a superclass Spline,
    #    c) create BezierSpline subclass that does the computation

    def __init__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        v = kwargs.get('points')
        self.points = v if v is not None else [0, 0, 0, 0, 0, 0, 0, 0]
        self._segments = kwargs.get('segments') or 180
        self._loop = kwargs.get('loop') or False
        if self._loop:
            self.points.extend(self.points[:2])
        self._dash_length = kwargs.get('dash_length') or 1
        self._dash_offset = kwargs.get('dash_offset') or 0
        self.batch.set_mode('line_strip')

    cdef void build(self):
        cdef int x, i, j
        cdef float l
        cdef list T = self.points[:]
        cdef vertex_t *vertices = NULL
        cdef unsigned short *indices = NULL
        cdef float tex_x
        cdef char *buf = NULL
        cdef Texture texture = self.texture

        if self._dash_offset != 0:
            if texture is None or texture._width != \
                (self._dash_length + self._dash_offset) or \
                texture._height != 1:

                self.texture = texture = Texture.create(
                        size=(self._dash_length + self._dash_offset, 1))
                texture.wrap = 'repeat'

            # create a buffer to fill our texture
            buf = <char *>malloc(4 * (self._dash_length + self._dash_offset))
            memset(buf, 255, self._dash_length * 4)
            memset(buf + self._dash_length * 4, 0, self._dash_offset * 4)

            p_str = buf[:(self._dash_length + self._dash_offset) * 4]

            texture.blit_buffer(p_str, colorfmt='rgba', bufferfmt='ubyte')
            free(buf)

        elif texture is not None:
            self.texture = None

        vertices = <vertex_t *>malloc((self._segments + 1) * sizeof(vertex_t))
        if vertices == NULL:
            raise MemoryError('vertices')

        indices = <unsigned short *>malloc(
                (self._segments + 1) * sizeof(unsigned short))
        if indices == NULL:
            free(vertices)
            raise MemoryError('indices')

        tex_x = x = 0
        for x in range(self._segments):
            l = <float>(x / (1.0 * self._segments))
            # http://en.wikipedia.org/wiki/De_Casteljau%27s_algorithm
            # as the list is in the form of (x1, y1, x2, y2...) iteration is
            # done on each item and the current item (xn or yn) in the list is
            # replaced with a calculation of "xn + x(n+1) - xn" x(n+1) is
            # placed at n+2. each iteration makes the list one item shorter
            for i in range(1, len(T)):
                for j in range(len(T) - 2*i):
                    T[j] = T[j] + (T[j+2] - T[j]) * l

            # we got the coordinates of the point in T[0] and T[1]
            vertices[x].x = T[0]
            vertices[x].y = T[1]
            if self._dash_offset != 0 and x > 0:
                tex_x += <float>(sqrt(
                        pow(vertices[x].x - vertices[x-1].x, 2) +
                        pow(vertices[x].y - vertices[x-1].y, 2)) / (
                                self._dash_length + self._dash_offset))

                vertices[x].s0 = tex_x
                vertices[x].t0 = 0

            indices[x] = x

        # add one last point to join the curve to the end
        vertices[x+1].x = T[-2]
        vertices[x+1].y = T[-1]

        tex_x += <float>(sqrt(
                (vertices[x+1].x - vertices[x].x) ** 2 +
                (vertices[x+1].y - vertices[x].y) ** 2) / (
                        self._dash_length + self._dash_offset))

        vertices[x+1].s0 = tex_x
        vertices[x+1].t0 = 0
        indices[x+1] = x + 1

        self.batch.set_data(
                vertices,
                self._segments + 1,
                indices,
                self._segments + 1)

        free(vertices)
        free(indices)

    @property
    def points(self):
        '''Property for getting/settings the points of the triangle.

        .. warning::

            This will always reconstruct the whole graphic from the new points
            list. It can be very CPU intensive.
        '''
        return self._points

    @points.setter
    def points(self, points):
        self._points = list(points)
        if self._loop:
            self._points.extend(points[:2])
        self.flag_data_update()

    @property
    def segments(self):
        '''Property for getting/setting the number of segments of the curve.
        '''
        return self._segments

    @segments.setter
    def segments(self, value):
        if value <= 1:
            raise GraphicException('Invalid segments value, must be >= 2')
        self._segments = value
        self.flag_data_update()

    @property
    def dash_length(self):
        '''Property for getting/setting the length of the dashes in the curve.
        '''
        return self._dash_length


    @dash_length.setter
    def dash_length(self, value):
        if value < 0:
            raise GraphicException('Invalid dash_length value, must be >= 0')
        self._dash_length = value
        self.flag_data_update()

    @property
    def dash_offset(self):
        '''Property for getting/setting the offset between the dashes in the
        curve.
        '''
        return self._dash_offset


    @dash_offset.setter
    def dash_offset(self, value):
        if value < 0:
            raise GraphicException('Invalid dash_offset value, must be >= 0')
        self._dash_offset = value
        self.flag_data_update()


cdef class StripMesh(VertexInstruction):
    '''A specialized 2d mesh.

    (internal) Used for SVG, will be available with doc later.
    '''
    def __init__(self, VertexFormat fmt):
        cdef VBO vbo
        VertexInstruction.__init__(self)
        vbo = VBO(fmt)
        self.batch = VertexBatch(vbo=vbo)
        self.batch.set_mode("triangle_strip")
        self.icount = 0
        self.li = self.lic = 0

    cdef int add_triangle_strip(self, float *vertices, int vcount, int icount,
            int mode):
        cdef int i, li = self.li
        cdef int istart = 0
        cdef unsigned short *indices = NULL
        cdef vsize = self.batch.vbo.vertex_format.vsize

        if vcount == 0 or icount < 3:
            return 0
        if self.icount + icount > 65533:  # (optimization of) self.icount + icount - 2 > 65535
            return 0

        if self.icount > 0:
            # repeat the last indice and the first of the new batch
            istart = 2

        indices = <unsigned short *>malloc((icount + istart) * sizeof(unsigned short))
        if indices == NULL:
            free(vertices)
            raise MemoryError('indices')

        if istart == 2:
            indices[0] = self.lic
            indices[1] = li
        if mode == 0:
            # polygon
            for i in range(<int>int(icount / 2.)):
                indices[i * 2 + istart] = li + i
                indices[i * 2 + istart + 1] = li + (icount - i - 1)
            if icount % 2 == 1:
                indices[icount + istart - 1] = li + <unsigned short>int(icount / 2.)
        elif mode == 1:
            # line
            for i in range(icount):
                indices[istart + i] = li + i

        self.lic = indices[icount + istart - 1]

        self.batch.append_data(vertices, <int>(vcount / vsize), indices,
                <int>(icount + istart))

        free(indices)
        self.icount += icount + istart
        self.li += icount
        return 1


cdef class Mesh(VertexInstruction):
    '''A 2d mesh.

    In OpenGL ES 2.0 and in our graphics implementation, you cannot have more
    than 65535 indices.

    A list of vertices is described as::

        vertices = [x1, y1, u1, v1, x2, y2, u2, v2, ...]
                    |            |  |            |
                    +---- i1 ----+  +---- i2 ----+

    If you want to draw a triangle, add 3 vertices. You can then make an
    indices list as follows:

        indices = [0, 1, 2]

    .. versionadded:: 1.1.0

    :Parameters:
        `vertices`: iterable
            List of vertices in the format (x1, y1, u1, v1, x2, y2, u2, v2...).
        `indices`: iterable
            List of indices in the format (i1, i2, i3...).
        `mode`: str
            Mode of the vbo. Check :attr:`mode` for more information. Defaults to
            'points'.
        `fmt`: list
            The format for vertices, by default, each vertex is described by 2D
            coordinates (x, y) and 2D texture coordinate (u, v).
            Each element of the list should be a tuple or list, of the form

                (variable_name, size, type)

            which will allow mapping vertex data to the glsl instructions.

                [(b'v_pos', 2, 'float'), (b'v_tc', 2, 'float'),]

            will allow using

                attribute vec2 v_pos;
                attribute vec2 v_tc;

            in glsl's vertex shader.

    .. versionchanged:: 1.8.1
        Before, `vertices` and `indices` would always be converted to a list,
        now, they are only converted to a list if they do not implement the
        buffer interface. So e.g. numpy arrays, python arrays etc. are used
        in place, without creating any additional copies. However, the
        buffers cannot be readonly (even though they are not changed, due to
        a cython limitation) and must be contiguous in memory.

    .. note::
        When passing a memoryview or a instance that implements the buffer
        interface, `vertices` should be a buffer of floats (`'f'` code in
        python array) and `indices` should be a buffer of unsigned short (`'H'`
        code in python array). Arrays in other formats will still have to be
        converted internally, negating any potential gain.
    '''

    def __init__(self, **kwargs):
        cdef VBO vbo
        VertexInstruction.__init__(self, **kwargs)
        v = kwargs.get('vertices')
        self.vertices = v if v is not None else []
        v = kwargs.get('indices')
        self.indices = v if v is not None else []
        fmt = kwargs.get('fmt')
        if fmt is not None:
            if isinstance(fmt, VertexFormat):
                self.vertex_format = fmt
            else:
                self.vertex_format = VertexFormat(*fmt)
            vbo = VBO(self.vertex_format)
            self.batch = VertexBatch(vbo=vbo)
        self.mode = kwargs.get('mode') or 'points'
        self.is_built = 0

    cdef void build_triangle_fan(self, float *vertices, int vcount, int icount):
        cdef i
        cdef unsigned short *indices = NULL
        cdef vsize = self.batch.vbo.vertex_format.vsize

        if vcount == 0 or icount == 0:
            self.batch.clear_data()
            return

        indices = <unsigned short *>malloc(icount * sizeof(unsigned short))
        if indices == NULL:
            free(vertices)
            raise MemoryError('indices')

        for i in range(icount):
            indices[i] = i

        self.batch.set_data(vertices, <int>(vcount / vsize), indices,
                <int>icount)

        free(indices)
        self.is_built = 1

    cdef void build(self):
        if self.is_built:
            return
        cdef vsize = self.batch.vbo.vertex_format.vsize

        # if user updated the list, but didn't do self.indices = ... then
        # we'd not know about it, so ensure _indices/_indices is up to date
        if len(self._vertices) != self.vcount:
            self._vertices, self._fvertices = _ensure_float_view(self._vertices,
                &self._pvertices)
            self.vcount = <long>len(self._vertices)

        if len(self._indices) != self.icount:
            if len(self._indices) > 65535:
                raise GraphicException('Cannot upload more than 65535 indices'
                                       '(OpenGL ES 2 limitation)')
            self._indices, self._lindices = _ensure_ushort_view(self._indices,
                &self._pindices)
            self.icount = <long>len(self._indices)

        if self.vcount == 0 or self.icount == 0:
            self.batch.clear_data()
            return

        self.batch.set_data(&self._pvertices[0], <int>(self.vcount / vsize),
                            &self._pindices[0], <int>self.icount)

    @property
    def vertices(self):
        '''List of x, y, u, v coordinates used to construct the Mesh. Right now,
        the Mesh instruction doesn't allow you to change the format of the
        vertices, which means it's only x, y + one texture coordinate.
        '''
        return self._vertices

    @vertices.setter
    def vertices(self, value):
        self._vertices, self._fvertices = _ensure_float_view(value,
            &self._pvertices)
        self.vcount = <long>len(self._vertices)
        self.flag_data_update()

    @property
    def indices(self):
        '''Vertex indices used to specify the order when drawing the
        mesh.
        '''
        return self._indices

    @indices.setter
    def indices(self, value):
        if gles_limts and len(value) > 65535:
            raise GraphicException(
                'Cannot upload more than 65535 indices (OpenGL ES 2'
                ' limitation - consider setting KIVY_GLES_LIMITS)')
        self._indices, self._lindices = _ensure_ushort_view(value,
            &self._pindices)
        self.icount = <long>len(self._indices)
        self.flag_data_update()

    @property
    def mode(self):
        '''VBO Mode used for drawing vertices/indices. Can be one of 'points',
        'line_strip', 'line_loop', 'lines', 'triangles', 'triangle_strip' or
        'triangle_fan'.
        '''
        return self.batch.get_mode()

    @mode.setter
    def mode(self, mode):
        self.batch.set_mode(mode)



cdef class Point(VertexInstruction):
    '''A list of 2d points. Each point is represented as a square with a
    width/height of 2 times the :attr:`pointsize`.

    :Parameters:
        `points`: list
            List of points in the format (x1, y1, x2, y2...), where each pair
            of coordinates specifies the center of a new point.
        `pointsize`: float, defaults to 1.
            The size of the point, measured from the center to the edge. A
            value of 1.0 therefore means the real size will be 2.0 x 2.0.

    .. warning::

        Starting from version 1.0.7, vertex instruction have a limit of 65535
        vertices (indices of vertex to be accurate).
        2 entries in the list (x, y) will be converted to 4 vertices. So the
        limit inside Point() class is 2^15-2.

    '''
    cdef list _points
    cdef float _pointsize

    def __init__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        v = kwargs.get('points')
        self.points = v if v is not None else []
        self.pointsize = kwargs.get('pointsize') or 1.

    cdef void build(self):
        cdef float x, y, ps = self._pointsize
        cdef int i, iv, ii, count = <int>(len(self._points) * 0.5)
        cdef list p = self.points
        cdef float *tc = self._tex_coords
        cdef vertex_t *vertices = NULL
        cdef unsigned short *indices = NULL

        #if there is no points...nothing to do
        if count < 1:
            self.batch.clear_data()
            return

        vertices = <vertex_t *>malloc(count * 4 * sizeof(vertex_t))
        if vertices == NULL:
            raise MemoryError('vertices')

        indices = <unsigned short *>malloc(count * 6 * sizeof(unsigned short))
        if indices == NULL:
            free(vertices)
            raise MemoryError('indices')

        for i in xrange(count):
            x = p[i * 2]
            y = p[i * 2 + 1]
            iv = i * 4
            vertices[iv].x = x - ps
            vertices[iv].y = y - ps
            vertices[iv].s0 = tc[0]
            vertices[iv].t0 = tc[1]
            vertices[iv + 1].x = x + ps
            vertices[iv + 1].y = y - ps
            vertices[iv + 1].s0 = tc[2]
            vertices[iv + 1].t0 = tc[3]
            vertices[iv + 2].x = x + ps
            vertices[iv + 2].y = y + ps
            vertices[iv + 2].s0 = tc[4]
            vertices[iv + 2].t0 = tc[5]
            vertices[iv + 3].x = x - ps
            vertices[iv + 3].y = y + ps
            vertices[iv + 3].s0 = tc[6]
            vertices[iv + 3].t0 = tc[7]

            ii = i * 6
            indices[ii] = iv
            indices[ii + 1] = iv + 1
            indices[ii + 2] = iv + 2
            indices[ii + 3] = iv + 2
            indices[ii + 4] = iv + 3
            indices[ii + 5] = iv

        self.batch.set_data(vertices, <int>(count * 4),
                            indices, <int>(count * 6))

        free(vertices)
        free(indices)

    def add_point(self, float x, float y):
        '''Add a point to the current :attr:`points` list.

        If you intend to add multiple points, prefer to use this method instead
        of reassigning a new :attr:`points` list. Assigning a new :attr:`points`
        list will recalculate and reupload the whole buffer into the GPU.
        If you use add_point, it will only upload the changes.
        '''
        cdef float ps = self._pointsize
        cdef int iv, count = <int>(len(self._points) * 0.5)
        cdef float *tc = self._tex_coords
        cdef vertex_t vertices[4]
        cdef unsigned short indices[6]

        if len(self._points) > 2**15 - 2:
            raise GraphicException('Cannot add elements (limit is 2^15-2)')

        self._points.append(x)
        self._points.append(y)

        vertices[0].x = x - ps
        vertices[0].y = y - ps
        vertices[0].s0 = tc[0]
        vertices[0].t0 = tc[1]
        vertices[1].x = x + ps
        vertices[1].y = y - ps
        vertices[1].s0 = tc[2]
        vertices[1].t0 = tc[3]
        vertices[2].x = x + ps
        vertices[2].y = y + ps
        vertices[2].s0 = tc[4]
        vertices[2].t0 = tc[5]
        vertices[3].x = x - ps
        vertices[3].y = y + ps
        vertices[3].s0 = tc[6]
        vertices[3].t0 = tc[7]

        iv = count * 4
        indices[0] = iv
        indices[1] = iv + 1
        indices[2] = iv + 2
        indices[3] = iv + 2
        indices[4] = iv + 3
        indices[5] = iv

        # append the vertices / indices to current vertex batch
        self.batch.append_data(vertices, 4, indices, 6)

        if self.parent is not None:
            self.parent.flag_data_update()

    @property
    def points(self):
        '''Property for getting/settings the center points in the points list.
        Each pair of coordinates specifies the center of a new point.
        '''
        return self._points

    @points.setter
    def points(self, points):
        if self._points == points:
            return
        cdef list _points = list(points)
        if len(_points) > 2**15-2:
            raise GraphicException('Too many elements (limit is 2^15-2)')
        self._points = list(points)
        self.flag_data_update()

    @property
    def pointsize(self):
        '''Property for getting/setting point size.
        The size is measured from the center to the edge, so a value of 1.0
        means the real size will be 2.0 x 2.0.
        '''
        return self._pointsize

    @pointsize.setter
    def pointsize(self, float pointsize):
        if self._pointsize == pointsize:
            return
        self._pointsize = pointsize
        self.flag_data_update()


cdef class Triangle(VertexInstruction):
    '''A 2d triangle.

    :Parameters:
        `points`: list
            List of points in the format (x1, y1, x2, y2, x3, y3).
    '''

    cdef list _points

    def __init__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        v = kwargs.get('points')
        self.points = v if v is not None else (0.0,0.0, 100.0,0.0, 50.0,100.0)

    cdef void build(self):
        cdef list vc
        cdef float *tc
        cdef vertex_t vertices[3]
        cdef unsigned short *indices = [0, 1, 2]

        vc = self.points;
        tc = self._tex_coords

        vertices[0].x = vc[0]
        vertices[0].y = vc[1]
        vertices[0].s0 = tc[0]
        vertices[0].t0 = tc[1]
        vertices[1].x = vc[2]
        vertices[1].y = vc[3]
        vertices[1].s0 = tc[2]
        vertices[1].t0 = tc[3]
        vertices[2].x = vc[4]
        vertices[2].y = vc[5]
        vertices[2].s0 = tc[4]
        vertices[2].t0 = tc[5]

        self.batch.set_data(vertices, 3, indices, 3)

    @property
    def points(self):
        '''Property for getting/settings points of the triangle.
        '''
        return self._points

    @points.setter
    def points(self, points):
        self._points = list(points)
        self.flag_data_update()


cdef class Quad(VertexInstruction):
    '''A 2d quad.

    :Parameters:
        `points`: list
            List of point in the format (x1, y1, x2, y2, x3, y3, x4, y4).
    '''
    cdef list _points

    def __init__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        v = kwargs.get('points')
        self.points = v if v is not None else \
               (  0.0,  50.0,   50.0,   0.0,
                100.0,  50.0,   50.0, 100.0 )

    cdef void build(self):
        cdef list vc
        cdef float *tc
        cdef vertex_t vertices[4]
        cdef unsigned short *indices = [0, 1, 2, 2, 3, 0]

        vc = self.points
        tc = self._tex_coords

        vertices[0].x = vc[0]
        vertices[0].y = vc[1]
        vertices[0].s0 = tc[0]
        vertices[0].t0 = tc[1]
        vertices[1].x = vc[2]
        vertices[1].y = vc[3]
        vertices[1].s0 = tc[2]
        vertices[1].t0 = tc[3]
        vertices[2].x = vc[4]
        vertices[2].y = vc[5]
        vertices[2].s0 = tc[4]
        vertices[2].t0 = tc[5]
        vertices[3].x = vc[6]
        vertices[3].y = vc[7]
        vertices[3].s0 = tc[6]
        vertices[3].t0 = tc[7]

        self.batch.set_data(vertices, 4, indices, 6)

    @property
    def points(self):
        '''Property for getting/settings points of the quad.
        '''
        return self._points

    @points.setter
    def points(self, points):
        self._points = list(points)
        if len(self._points) != 8:
            raise GraphicException(
                'Quad: invalid number of points (%d instead of 8)' % len(
                self._points))
        self.flag_data_update()


cdef class Rectangle(VertexInstruction):
    '''A 2d rectangle optimized for faster point handling with direct memory access.

    :Parameters:
        `pos`: tuple
            Position of the rectangle, in the format (x, y).
        `size`: tuple
            Size of the rectangle, in the format (width, height).
    '''
    cdef float x, y, w, h
    cdef vertex_t* vertices
    cdef unsigned short* indices
    cdef float* _points

    def __cinit__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        v = kwargs.get('pos')
        self.pos = v if v is not None else (0, 0)
        v = kwargs.get('size')
        self.size = v if v is not None else (100, 100)
        # Allocate memory for 4 vertices and 6 indices
        self.vertices = <vertex_t*>malloc(4 * sizeof(vertex_t))
        self.indices = <unsigned short*>malloc(6 * sizeof(unsigned short))
        self._points = <float*>malloc(8 * sizeof(float))
        if not self.vertices or not self.indices or not self._points:
            raise MemoryError("Failed to allocate memory for rectangle data.")
        self.indices[0] = 0
        self.indices[1] = 1
        self.indices[2] = 2
        self.indices[3] = 2
        self.indices[4] = 3
        self.indices[5] = 0
        self.update_vertices()

    cdef void update_vertices(self):
        # Set the vertex positions directly using pointer arithmetic
        self.vertices[0].x = self.x
        self.vertices[0].y = self.y
        self.vertices[1].x = self.x + self.w
        self.vertices[1].y = self.y
        self.vertices[2].x = self.x + self.w
        self.vertices[2].y = self.y + self.h
        self.vertices[3].x = self.x
        self.vertices[3].y = self.y + self.h

        self._points[0] = self.x
        self._points[1] = self.y
        self._points[2] = self.x + self.w
        self._points[3] = self.y
        self._points[4] = self.x + self.w
        self._points[5] = self.y + self.h
        self._points[6] = self.x
        self._points[7] = self.y + self.h

    def __dealloc__(self):
        if self.vertices:
            free(self.vertices)
        if self.indices:
            free(self.indices)
        if self._points:
            free(self._points)

    @property
    def pos(self):
        return (self.x, self.y)

    @pos.setter
    def pos(self, pos):
        cdef float x, y
        x, y = pos
        if self.x == x and self.y == y:
            return
        self.x = x
        self.y = y
        self.update_vertices()
        self.flag_data_update()

    @property
    def size(self):
        return (self.w, self.h)

    @size.setter
    def size(self, size):
        cdef float w, h
        w, h = size
        if self.w == w and self.h == h:
            return
        self.w = w
        self.h = h
        self.update_vertices()
        self.flag_data_update()

    @property
    def points(self):
        return [self._points[i] for i in range(8)]

    cdef void build(self):
        self.batch.set_data(self.vertices, 4, self.indices, 6)

    def draw(self):
        # Implement drawing logic here, using self.vertices directly
        pass



cdef class BorderImage(Rectangle):
    '''A 2d border image optimized for faster point handling with direct memory access.

    :Parameters:
        `border`: list
            Border information in the format (bottom, right, top, left).
            Each value is in pixels.

        `auto_scale`: string
            Can be one of 'off', 'both', 'x_only', 'y_only', 'y_full_x_lower',
            'x_full_y_lower', 'both_lower'.

            Autoscale controls the behavior of the 9-slice.
    '''
    cdef float* _border
    cdef float* _display_border
    cdef str _auto_scale

    def __cinit__(self, **kwargs):
        Rectangle.__cinit__(self, **kwargs)
        v = kwargs.get('border')
        self.border = v if v is not None else (10, 10, 10, 10)
        self.auto_scale = kwargs.get('auto_scale', 'off')
        self.display_border = kwargs.get('display_border', [])

    cdef void update_vertices(self):
        # Custom update_vertices logic for BorderImage if needed
        Rectangle.update_vertices(self)

    cdef void build(self):
        if not self.texture:
            Logger.trace('GBorderImage: texture missing')
            return

        # pos and size of border rectangle
        cdef float x, y, w, h
        x = self.x
        y = self.y
        w = self.w
        h = self.h

        # width and height of texture in pixels, and tex coord space
        cdef float tw, th, tcw, tch
        cdef float *tc = self._tex_coords
        cdef float tc0, tc1, tc2, tc7
        tc0 = tc[0]
        tc1 = tc[1]
        tc2 = tc[2]
        tc7 = tc[7]
        tw, th  = self.texture.size
        tcw = tc2 - tc0  #right - left
        tch = tc7 - tc1  #top - bottom

        # calculate border offset in texture coord space
        cdef float tb[4] # border offset in texture coordinate space
        tb[0] = self._border[0] / th * tch
        tb[1] = self._border[1] / tw * tcw
        tb[2] = self._border[2] / th * tch
        tb[3] = self._border[3] / tw * tcw

        cdef float sb0, sb1, sb2, sb3

        if self._auto_scale == 'off':
            sb0, sb1, sb2, sb3 = self._border[0], self._border[1], self._border[2], self._border[3]
        elif self._auto_scale == 'both':
            sb0 = (self._border[0]/th) * h
            sb1 = (self._border[1]/tw) * w
            sb2 = (self._border[2]/th) * h
            sb3 = (self._border[3]/tw) * w
        elif self._auto_scale == 'x_only':
            sb0 = self._border[0]
            sb1 = (self._border[1]/tw) * w
            sb2 = self._border[2]
            sb3 = (self._border[3]/tw) * w
        elif self._auto_scale == 'y_only':
            sb0 = (self._border[0]/th) * h
            sb1 = self._border[1]
            sb2 = (self._border[2]/th) * h
            sb3 = self._border[3]
        elif self._auto_scale == 'y_full_x_lower':
            sb0 = (self._border[0]/th) * h
            sb1 = min((self._border[1]/tw) * w, self._border[1])
            sb2 = (self._border[2]/th) * h
            sb3 = min((self._border[3]/tw) * w, self._border[3])
        elif self._auto_scale == 'x_full_y_lower':
            sb0 = min((self._border[0]/th) * h, self._border[0])
            sb1 = (self._border[1]/tw) * w
            sb2 = min((self._border[2]/th) * h, self._border[2])
            sb3 = (self._border[3]/tw) * w
        elif self._auto_scale == 'both_lower':
            sb0 = min((self._border[0]/th) * h, self._border[0])
            sb1 = min((self._border[1]/tw) * w, self._border[1])
            sb2 = min((self._border[2]/th) * h, self._border[2])
            sb3 = min((self._border[3]/tw) * w, self._border[3])
        else:
            sb0, sb1, sb2, sb3 = self._border[0], self._border[1], self._border[2], self._border[3]

        # horizontal and vertical sections
        cdef float hs[4]
        cdef float vs[4]
        if self._display_border:
            sb0, sb1, sb2, sb3 = self._display_border[0], self._display_border[1], self._display_border[2], self._display_border[3]
        hs[0] = x;            vs[0] = y
        hs[1] = x + sb3;       vs[1] = y + sb0
        hs[2] = x + w - sb1;   vs[2] = y + h - sb2
        hs[3] = x + w;        vs[3] = y + h

        cdef float ths[4]
        cdef float tvs[4]
        ths[0] = tc0;              tvs[0] = tc1
        ths[1] = tc0 + tb[3];      tvs[1] = tc1 + tb[0]
        ths[2] = tc0 + tcw-tb[1];  tvs[2] = tc1 + tch - tb[2]
        ths[3] = tc0 + tcw;        tvs[3] = tc1 + tch

        # set the vertex data
        assert sizeof(vertex_t) == 4 * sizeof(float)
        cdef float *vertices = [
            hs[0], vs[0], ths[0], tvs[0], #v0
            hs[1], vs[0], ths[1], tvs[0], #v1
            hs[2], vs[0], ths[2], tvs[0], #v2
            hs[3], vs[0], ths[3], tvs[0], #v3
            hs[3], vs[1], ths[3], tvs[1], #v4
            hs[3], vs[2], ths[3], tvs[2], #v5
            hs[3], vs[3], ths[3], tvs[3], #v6
            hs[2], vs[3], ths[2], tvs[3], #v7
            hs[1], vs[3], ths[1], tvs[3], #v8
            hs[0], vs[3], ths[0], tvs[3], #v9
            hs[0], vs[2], ths[0], tvs[2], #v10
            hs[0], vs[1], ths[0], tvs[1], #v11
            hs[1], vs[1], ths[1], tvs[1], #v12
            hs[2], vs[1], ths[2], tvs[1], #v13
            hs[2], vs[2], ths[2], tvs[2], #v14
            hs[1], vs[2], ths[1], tvs[2]] #v15

        cdef unsigned short *indices = [
             0,  1, 12,    12, 11,  0,  # bottom left
             1,  2, 13,    13, 12,  1,  # bottom middle
             2,  3,  4,     4, 13,  2,  # bottom right
            13,  4,  5,     5, 14, 13,  # center right
            14,  5,  6,     6,  7, 14,  # top right
            15, 14,  7,     7,  8, 15,  # top middle
            10, 15,  8,     8,  9, 10,  # top left
            11, 12, 15,    15, 10, 11,  # center left
            12, 13, 14,    14, 15, 12]  # center middle

        self.batch.set_data(<vertex_t *>vertices, 16, indices, 54)

    @property
    def border(self):
        '''Property for getting/setting the border of the class.
        '''
        return [self._border[i] for i in range(4)]

    @border.setter
    def border(self, b):
        self._border = <float*>malloc(4 * sizeof(float))
        for i in range(4):
            self._border[i] = b[i]
        self.flag_data_update()

    @property
    def auto_scale(self):
        '''Property for setting if the corners are automatically scaled
        when the BorderImage is too small.
        '''
        return self._auto_scale

    @auto_scale.setter
    def auto_scale(self, value):
        self._auto_scale = value
        self.flag_data_update()

    @property
    def display_border(self):
        '''Property for getting/setting the border display size.
        '''
        return [self._display_border[i] for i in range(4)]

    @display_border.setter
    def display_border(self, b):
        self._display_border = <float*>malloc(4 * sizeof(float))
        for i in range(4):
            self._display_border[i] = b[i]
        self.flag_data_update()


cdef class Ellipse(Rectangle):
    '''A 2d ellipse optimized for faster point handling with direct memory access.

    :Parameters:
        `pos`: tuple
            Position of the ellipse center, in the format (x, y).
        `size`: tuple
            Size of the ellipse, in the format (width, height).
    '''
    cdef int segments
    cdef vertex_t* vertices
    cdef unsigned short* indices
    cdef float* _points

    def __cinit__(self, **kwargs):
        Rectangle.__cinit__(self, **kwargs)
        v = kwargs.get('segments')
        self.segments = v if v is not None else 32
        # Allocate memory for vertices and indices
        self.vertices = <vertex_t*>malloc(self.segments * sizeof(vertex_t))
        self.indices = <unsigned short*>malloc(self.segments * 3 * sizeof(unsigned short))
        self._points = <float*>malloc(2 * self.segments * sizeof(float))
        if not self.vertices or not self.indices or not self._points:
            raise MemoryError("Failed to allocate memory for ellipse data.")
        self.update_vertices()

    cdef void update_vertices(self):
        cdef int i
        cdef float theta, x, y, cx, cy, w, h
        cx, cy = self.x, self.y
        w, h = self.w / 2.0, self.h / 2.0
        for i in range(self.segments):
            theta = 2.0 * 3.1415926 * float(i) / float(self.segments)
            x = w * cos(theta)
            y = h * sin(theta)
            self.vertices[i].x = cx + x
            self.vertices[i].y = cy + y
            self._points[2 * i] = cx + x
            self._points[2 * i + 1] = cy + y
        for i in range(self.segments):
            self.indices[3 * i] = 0
            self.indices[3 * i + 1] = i
            self.indices[3 * i + 2] = (i + 1) % self.segments

    def __dealloc__(self):
        if self.vertices:
            free(self.vertices)
        if self.indices:
            free(self.indices)
        if self._points:
            free(self._points)

    @property
    def pos(self):
        return (self.x, self.y)

    @pos.setter
    def pos(self, pos):
        cdef float x, y
        x, y = pos
        if self.x == x and self.y == y:
            return
        self.x = x
        self.y = y
        self.update_vertices()
        self.flag_data_update()

    @property
    def size(self):
        return (self.w, self.h)

    @size.setter
    def size(self, size):
        cdef float w, h
        w, h = size
        if self.w == w and self.h == h:
            return
        self.w = w
        self.h = h
        self.update_vertices()
        self.flag_data_update()

    @property
    def points(self):
        return [self._points[i] for i in range(2 * self.segments)]

    cdef void build(self):
        self.batch.set_data(self.vertices, self.segments, self.indices, self.segments * 3)

    def draw(self):
        # Implement drawing logic here, using self.vertices directly
        pass



cdef class RoundedRectangle(Rectangle):
    '''A 2D rounded rectangle optimized for faster point handling with direct memory access.

    :Parameters:
        `segments`: int, defaults to 10
            Define how many segments are needed for drawing the rounded corner.
            The drawing will be smoother if you have many segments.
        `radius`: list, defaults to [(10.0, 10.0), (10.0, 10.0), (10.0, 10.0), (10.0, 10.0)]
            Specifies the radii used for the rounded corners clockwise:
            top-left, top-right, bottom-right, bottom-left.
            Elements of the list can be numbers or tuples of two numbers to specify different x,y dimensions.
            One value will define all corner radii to be of this value.
            Four values will define each corner radius separately.
            Higher numbers of values will be truncated to four.
            The first value will be used for all corners if there are fewer than four values.
    '''
    cdef int* _segments
    cdef float* _radius

    def __cinit__(self, **kwargs):
        Rectangle.__cinit__(self, **kwargs)
        self.batch.set_mode('triangle_fan')

        # number of segments for each corner
        segments = kwargs.get('segments', 10)
        self._segments = self._check_segments(segments)

        radius = kwargs.get('radius') or [10.0]
        self._radius = self._check_radius(radius)
        self._points = []

    cdef int* _check_segments(self, object segments):
        """
        Check segments argument, return list of four numeric values
        for each corner.
        """
        cdef int* result = <int*>malloc(4 * sizeof(int))

        if isinstance(segments, int):
            for i in range(4):
                result[i] = segments
            return result

        if isinstance(segments, list):
            if len(segments) < 4:
                value = segments[0]
                for i in range(4):
                    result[i] = value
            else:
                for i in range(4):
                    result[i] = segments[i]
            return result

        raise GraphicException("Invalid segments value, must be integer or list of integers")

    cdef float* _check_radius(self, object radius):
        """
        Check radius argument, return list of four tuples
        (xradius, yradius) for each corner.
        """
        cdef float* result = <float*>malloc(8 * sizeof(float))

        if isinstance(radius, (int, float)):
            for i in range(4):
                result[2*i] = radius
                result[2*i+1] = radius
            return result

        if isinstance(radius, list):
            for i in range(4):
                if isinstance(radius[i], tuple):
                    result[2*i] = radius[i][0]
                    result[2*i+1] = radius[i][1]
                else:
                    result[2*i] = radius[i]
                    result[2*i+1] = radius[i]
            return result

        raise GraphicException("Invalid radius value, must be list of tuples/numerics")

    cdef void build(self):
        cdef float *tc = self._tex_coords
        cdef vertex_t *vertices = NULL
        cdef unsigned short *indices = NULL

        cdef int count, corner, segments, dw, dh, index
        cdef float rx, ry, half_w, half_h, angle
        cdef float tx, ty, tw, th, px, py, x, y

        self._points = []

        if self.w == 0 or self.h == 0:
            return

        count = sum([1 + segments * bool(self._radius[2*i] * self._radius[2*i+1])
                     for i, segments in enumerate(self._segments)]) + 1

        vertices = <vertex_t*>malloc(count * sizeof(vertex_t))
        if vertices == NULL:
            raise MemoryError('vertices')

        indices = <unsigned short*>malloc((count + 1) * sizeof(unsigned short))
        if indices == NULL:
            free(vertices)
            raise MemoryError('indices')

        half_w = self.w / 2
        half_h = self.h / 2

        xradius = [min(self._radius[2*i], half_w) for i in range(4)]
        yradius = [min(self._radius[2*i+1], half_h) for i in range(4)]

        tx = tc[0]
        ty = tc[1]
        tw = tc[4] - tx
        th = tc[5] - ty

        vertices[0].x = self.x + half_w
        vertices[0].y = self.y + half_h
        vertices[0].s0 = tx + tw / 2
        vertices[0].t0 = ty + th / 2
        indices[0] = 0

        index = 1
        for corner in range(4):
            angle = 180 - 90 * corner

            dw, dh = [(0,1), (1,1), (1,0), (0,0)][corner]

            rx, ry = xradius[corner], yradius[corner]

            px, py = [
                (self.x + rx, self.y + self.h - ry),
                (self.x + self.w - rx, self.y + self.h - ry),
                (self.x + self.w - rx, self.y + ry),
                (self.x + rx, self.y + ry)
            ][corner]

            segments = self._segments[corner]

            if not(rx and ry and segments):
                vertices[index].x = self.x + self.w * dw
                vertices[index].y = self.y + self.h * dh
                vertices[index].s0 = tx + tw * dw
                vertices[index].t0 = ty + th * dh

                self._points.append((self.x + self.w * dw, self.y + self.h * dh))
            else:
                points = self.draw_arc(px, py, rx, ry, angle, angle - 90, segments)
                for i, point in enumerate(points, index):
                    x, y = point
                    vertices[i].x = x
                    vertices[i].y = y
                    vertices[i].s0 = (x - self.x) / self.w
                    vertices[i].t0 = 1 - (y - self.y) / self.h
                    indices[i] = i
                index += segments

                x = px * (dw != dh) + self.x * (dw == dh) + self.w * (dw * dh)
                y = py * (dw == dh) + self.y * (dw != dh) + self.h * (dh > dw)
                vertices[index].x = x
                vertices[index].y = y
                vertices[index].s0 = (x - self.x) / self.w
                vertices[index].t0 = 1 - (y - self.y) / self.h

                self._points.extend(points)
                self._points.append((x, y))

            indices[index] = index
            index += 1

        indices[count] = indices[1]
        self.batch.set_data(vertices, count, indices, count + 1)
        free(vertices)
        free(indices)

    cdef list draw_arc(self, float cx, float cy, float rx, float ry, float angle_start, float angle_end, int segments):
        cdef float fx, fy, x, y
        cdef float tangential_factor, radial_factor, theta
        cdef list points

        angle_start *= 0.017453292519943295
        angle_end *= 0.017453292519943295

        theta = (angle_end - angle_start) / segments
        tangential_factor = tan(theta)
        radial_factor = cos(theta)

        x = cos(angle_start)
        y = sin(angle_start)

        points = []

        for i in range(segments):
            real_x = cx + x * rx
            real_y = cy + y * ry
            points.append((real_x, real_y))

            fx = -y
            fy = x
            x += fx * tangential_factor
            y += fy * tangential_factor
            x *= radial_factor
            y *= radial_factor

        return points

    @property
    def segments(self):
        return [self._segments[i] for i in range(4)]

    @segments.setter
    def segments(self, value):
        self._segments = self._check_segments(value)
        self.flag_data_update()

    @property
    def radius(self):
        return [(self._radius[2*i], self._radius[2*i+1]) for i in range(4)]

    @radius.setter
    def radius(self, value):
        self._radius = self._check_radius(value)
        self.flag_data_update()



"""
Graphics section with antialiasing that uses a combination of AntiAliasingLine
and the target graphics Instruction, such as Rectangle, Ellipse,
RoundedRectangle, Triangle and Quad.

NOTE: Texture antialiasing is currently not supported. If a texture is defined
for any of the graphics with antialiasing, then antialiasing will be disabled.

The antialiasing is also disabled for graphics with "fixed" shapes, such as
Rectangle, RoundedRectangle and Ellipse through verification in
``too_small_for_antialiasing`` function. Reasons for it:

    - Drawing an antialiasing line on figures with very small dimensions does
    not bring great visual improvements. 

    - This reduces the code complexity in the `adjust_params` functions,
    which are used to adjust the size of these figures, and keep them
    proportional to the figures without antialiasing.

TODO: Use AntiAliasingLine as a sort of "alpha test" to enable texture
antialiasing. This will likely involve utilizing glBlendFunc in conjunction
with other functions. It would also involve creating custom instructions,
similar to the custom stencil instructions bellow, to ensure efficiency.
"""




"""
The functions below are extended versions of the radd, rinsert and rremove from
VertexInstruction, with the ability to add/remove more than one instruction set
(BindTexture + VertexInstruction) to/from a instruction group.
"""

cdef void radd_instructions(InstructionGroup ig, VertexInstruction target_graphic, AntiAliasingLine aa_line):
    cdef Instruction instr = target_graphic.texture_binding, aa_instr = target_graphic.texture_binding
    ig.children.append(target_graphic.texture_binding)
    ig.children.append(target_graphic)
    ig.children.append(aa_line.texture_binding)
    ig.children.append(aa_line)
    aa_instr.set_parent(ig)
    aa_line.set_parent(ig)
    instr.set_parent(ig)
    target_graphic.set_parent(ig)


cdef void rinsert_instructions(InstructionGroup ig, int index, VertexInstruction target_graphic, AntiAliasingLine aa_line):
    cdef Instruction instr = target_graphic.texture_binding, aa_instr = target_graphic.texture_binding
    cdef int index_adjust = 0 if index < 0 else 1
    ig.children.insert(index, target_graphic.texture_binding)
    ig.children.insert(index + 1 * index_adjust, target_graphic)
    ig.children.insert(index + 2 * index_adjust, aa_line.texture_binding)
    ig.children.insert(index + 3 * index_adjust, aa_line)
    aa_instr.set_parent(ig)
    aa_line.set_parent(ig)
    instr.set_parent(ig)
    target_graphic.set_parent(ig)


cdef void rremove_instructions(InstructionGroup ig, VertexInstruction target_graphic, AntiAliasingLine aa_line):
    cdef Instruction instr = target_graphic.texture_binding, aa_instr = target_graphic.texture_binding
    ig.children.remove(target_graphic.texture_binding)
    ig.children.remove(target_graphic)
    ig.children.remove(aa_line.texture_binding)
    ig.children.remove(aa_line)
    aa_instr.set_parent(None)
    aa_line.set_parent(None)
    instr.set_parent(None)
    target_graphic.set_parent(None)


cdef class AntiAliasingLine(VertexInstruction):
    """(internal) An instruction similar to SmoothLine, adjusted for antialiasing purposes.

    NOTE: AntiAliasingLine is not intended for public use, it was created and
    adjusted only for antialiasing purposes.

    Overview of behavior:

    - Its main purpose is to be drawn around other graphic instructions (such
    as RoundedRectangle, Ellipse, etc.) that do not have antialiasing.

    - When the alpha channel value of the active context is less than 1.0,
    stencil operations will be performed to prevent overlapping of alpha
    channel values (by default, drawing two overlapping graphics with an alpha
    channel of 0.5 would produce an alpha channel of 1.0 at their intersection).

    - The stencil instructions are based on the mask provided through the
    "stencil_mask" argument.

    - Points are filtered before being used to create vertices. If the number
    of valid points is less than 3, the list of points will be emptied and
    AntiAliasingLine will not be drawn. There is no reason to allow a value
    lower than 3 points here.

    - As it was designed to wrap around a graphic Instruction, it is closed by default.

    - The texture used, as well as the line width, have been defined through
    experimentation. Do not modify without extensive experimentation.

    """

    cdef list _points
    cdef float _width
    cdef int _close
    cdef int _use_stencil
    cdef Instruction _stencil_mask
    cdef Instruction _stencil_push
    cdef Instruction _stencil_use
    cdef Instruction _stencil_unuse
    cdef Instruction _stencil_pop

    def __init__(self, stencil_mask, **kwargs):
        super().__init__(**kwargs)
        self.batch.set_mode("triangles")
        self.close = int(bool(kwargs.get('close', 1)))  # closed by default
        self.points = kwargs.get('points', [])
        self.texture = self.premultiplied_texture()
        self._width = 2.5  # width defined through tests with the premultiplied texture
        self._stencil_push = None
        self._stencil_use = None
        self._stencil_unuse = None
        self._stencil_pop = None
        self._use_stencil = 0
        if isinstance(stencil_mask, Instruction):
            self._stencil_mask = stencil_mask  # the stencil mask
        else:
            raise TypeError(f"'stencil_mask' needs to be a graphics Instruction, got {type(stencil_mask)}")

    def premultiplied_texture(self):
        texture = Cache.get('kv.graphics.texture', 'antialiasing_line')
        if not texture:
            texture = Texture.create(size=(3, 1), colorfmt="rgba")
            texture.add_reload_observer(self._texture_reload_observer)
            self._texture_reload_observer(texture)
            Cache.append('kv.graphics.texture', 'antialiasing_line', texture)
        return texture

    cpdef _texture_reload_observer(self, texture):
        cdef bytes GRADIENT_DATA = (
            b"\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\x00")
        texture.blit_buffer(GRADIENT_DATA, colorfmt="rgba")

    cdef void radd(self, InstructionGroup ig):
        """Disabled because logic management is done on the radd of the target graphic (stencil_mask)"""
        pass

    cdef void rinsert(self, InstructionGroup ig, int index):
        """Disabled because logic management is done on the rinsert of the target graphic (stencil_mask)"""
        pass

    cdef void rremove(self, InstructionGroup ig):
        """Disabled because logic management is done on the rremove of the target graphic (stencil_mask)"""
        pass

    cdef void ensure_stencil(self):
        if self._stencil_push == None:
            self._stencil_push = StencilPush(clear_stencil=False)
            self._stencil_pop = StencilPop()
            self._stencil_use = StencilUse(op="greater")
            self._stencil_unuse = StencilUnUse()

    cdef int apply(self) except -1:
        cdef double alpha = getActiveContext()['color'][-1]
        self._use_stencil = alpha < 1
        if self._use_stencil:
            self.ensure_stencil()
            self._stencil_push.apply()
            self._stencil_mask.apply()
            self._stencil_use.apply()
            VertexInstruction.apply(self)
            self._stencil_unuse.apply()
            self._stencil_mask.apply()
            self._stencil_pop.apply()
        else:
            VertexInstruction.apply(self)
        return 0

    cdef void build(self):
        cdef:
            list p = self.points
            float width = self._width
            vertex_t *vertices = NULL
            unsigned short *indices = NULL
            double ax, ay, bx = 0., by = 0., cx = 0., cy = 0., last_angle = 0., angle, angle_diff
            double offset_x, offset_y, joint_offset_x, joint_offset_y
            int i, iv = 0, max_index, direction
            unsigned short vcount, icount, discarded_vcount = 3

        # AntiAliasingLine drawn will not be performed if the list of points
        # filtered by filtered_points is empty or has less than 3 points.
        if not p:
            self.batch.clear_data()
            return

        if self._close:
            discarded_vcount = 0

        icount = vcount = <unsigned short>int(9 * ((len(p) - 2) / 2) - discarded_vcount)

        vertices = <vertex_t *>malloc(vcount * sizeof(vertex_t))
        if vertices == NULL:
            raise MemoryError("vertices")

        indices = <unsigned short *>malloc(icount * sizeof(unsigned short))
        if indices == NULL:
            free(vertices)
            raise MemoryError("indices")

        if self._close:
            ax = p[-4]
            ay = p[-3]
            bx = p[0]
            by = p[1]
            cx = bx - ax
            cy = by - ay
            last_angle = atan2(cy, cx)

        max_index = len(p) - 2
        for i in range(0, max_index, 2):
            ax = p[i]
            ay = p[i + 1]
            bx = p[i + 2]
            by = p[i + 3]
            cx = bx - ax
            cy = by - ay
            angle = atan2(cy, cx)

            offset_x = width * sin(angle)
            offset_y = width * cos(angle)

            # fisrt triangle
            vertices[iv].x = <float>ax - offset_x
            vertices[iv].y = <float>ay + offset_y
            vertices[iv].s0 = 0
            vertices[iv].t0 = 0
            iv += 1
            vertices[iv].x = <float>bx + offset_x
            vertices[iv].y = <float>by - offset_y
            vertices[iv].s0 = 1
            vertices[iv].t0 = 0
            iv += 1
            vertices[iv].x = <float>ax + offset_x
            vertices[iv].y = <float>ay - offset_y
            vertices[iv].s0 = 1
            vertices[iv].t0 = 0
            iv += 1

            # second triangle
            vertices[iv].x = <float>ax - offset_x
            vertices[iv].y = <float>ay + offset_y
            vertices[iv].s0 = 0
            vertices[iv].t0 = 0
            iv += 1
            vertices[iv].x = <float>bx + offset_x
            vertices[iv].y = <float>by - offset_y
            vertices[iv].s0 = 1
            vertices[iv].t0 = 0
            iv += 1
            vertices[iv].x = <float>bx - offset_x
            vertices[iv].y = <float>by + offset_y
            vertices[iv].s0 = 0
            vertices[iv].t0 = 0
            iv += 1

            # miter joint code
            if i > 0 or self._close:
                joint_offset_x = width * sin(last_angle)
                joint_offset_y = width * cos(last_angle)

                angle_diff = (angle - last_angle)
                direction = -1 if - pi < angle_diff < 0 or angle_diff > pi else 1

                # miter joint triangle
                vertices[iv].x = <float>ax
                vertices[iv].y = <float>ay
                vertices[iv].s0 = 0.5
                vertices[iv].t0 = 0
                iv += 1
                vertices[iv].x = <float>ax + offset_x * direction
                vertices[iv].y = <float>ay - offset_y * direction
                vertices[iv].s0 = 1
                vertices[iv].t0 = 0
                iv += 1
                vertices[iv].x = <float>ax + joint_offset_x * direction
                vertices[iv].y = <float>ay - joint_offset_y * direction
                vertices[iv].s0 = 1
                vertices[iv].t0 = 0
                iv += 1

            last_angle = angle

        for i in range(icount):
            indices[i] = i

        self.batch.set_data(vertices, <int>vcount, indices, <int>icount)

        free(vertices)
        free(indices)

    cdef filtered_points(self, points):
        """Removes points where the x and y distances are less than 1px.

        If the points are too close, we must remove them for a few reasons:
        
        - Equal points generate an inconsistency in the generation of the
        miter joint. And dealing with them internally increases code
        complexity (unnecessarily).

        - Very close points (with distance less than 1px) have little
        relevance for antialiasing line drawing purposes. Furthermore,
        calculation inaccuracies can lead to the production of incorrect
        miter joints.

        - Fewer vertices to compute. By discarding the insignificant points
        we will also be saving computational resources and increasing the
        performance of building the antialiasing line.
        """
        cdef int index = 0
        cdef list p = points
        cdef double x1, x2, y1, y2

        # At least 3 points are required, otherwise we will return an empty
        # list, which means there are no valid points,
        # disabling AntiAliasingLine rendering.
        if len(p) < 6:
            return []

        while index < len(p) - 2:
            x1, y1 = p[index], p[index + 1]
            x2, y2 = p[index + 2], p[index + 3]
            if abs(x2 - x1) < 1.0 and abs(y2 - y1) < 1.0:
                del p[index + 2: index + 4]
            else:
                index += 2
        if abs(p[0] - p[-2]) < 1.0 and abs(p[1] - p[-1]) < 1.0:
            del p[:2]
        
        # If the amount of valid points is less than 3, then we will
        # return an empty list, to disable AntiAliasingLine rendering.
        return [] if len(p) < 6 else p

    @property
    def width(self):
        return self._width

    @property
    def points(self):
        return self._points
    
    @points.setter
    def points(self, points):
        if points and isinstance(points[0], (list, tuple)):
            points = list(itertools.chain(*points))
        else:
            points = list(points)
        points = self.filtered_points(points)
        if points and self.close:
            points += points[:2]
        self._points = points
        self.flag_data_update()
    
    @property
    def close(self):
        return self._close
    
    @close.setter
    def close(self, value):
        self._close = int(bool(value))
        self.flag_data_update()




cdef int has_texture_set(VertexInstruction instruction):
    if (instruction.texture and instruction.texture != instruction.default_texture) or instruction.source:
        return 1
    return 0


cdef int too_small_for_antialiasing(VertexInstruction instruction):
    if not isinstance(instruction, (SmoothRectangle, SmoothRoundedRectangle, SmoothEllipse)):
        raise NotImplementedError()

    return (-4 < instruction.size[0] < 4 or -4 < instruction.size[1] < 4)


cdef void adjust_params(VertexInstruction instruction, int delta):
        """Adjust the parameters that define the size of the drawing.
        This adjustment needs to be made before building the points, in order
        to compensate for the antialiasing line drawn around the contour of
        the figure.
        """
        if not isinstance(instruction, (SmoothRectangle, SmoothRoundedRectangle, SmoothEllipse)):
            raise NotImplementedError()

        cdef int sign_x, sign_y

        x, y = instruction.pos
        w, h = instruction.size

        sign_x = 1 if w < 0 else -1
        sign_y = 1 if h < 0 else -1

        x += delta * sign_x
        y += delta * sign_y
        w += delta * 2 * sign_x * -1
        h += delta * 2 * sign_y * -1

        instruction.pos = [x, y]
        instruction.size = [w, h]

        if isinstance(instruction, SmoothRoundedRectangle):
            instruction.radius = [(max(0, rx + delta), max(0, ry + delta)) for rx, ry in instruction.radius]




cdef class SmoothRoundedRectangle(RoundedRectangle):
    '''RoundedRectangle with antialiasing.

    :Parameters:
        Same as :class:`~kivy.graphics.vertex_instructions.RoundedRectangle`.
    '''
    cdef AntiAliasingLine _antialiasing_line
    cdef public Texture default_texture

    def __cinit__(self, **kwargs):
        self._antialiasing_line = AntiAliasingLine(stencil_mask=self, close=1)
        RoundedRectangle.__cinit__(self, **kwargs)
        self.default_texture = self.texture

    cdef void radd(self, InstructionGroup ig):
        radd_instructions(ig, self, self._antialiasing_line)

    cdef void rinsert(self, InstructionGroup ig, int index):
        rinsert_instructions(ig, index, self, self._antialiasing_line)

    cdef void rremove(self, InstructionGroup ig):
        rremove_instructions(ig, self, self._antialiasing_line)

    cdef void build(self):
        if has_texture_set(self) or too_small_for_antialiasing(self):
            self._antialiasing_line.points = []
            RoundedRectangle.build(self)
        else:
            adjust_params(self, -1)
            RoundedRectangle.build(self)
            self._antialiasing_line.points = self._points
            adjust_params(self, 1)

    @property
    def antialiasing_line_points(self):
        return self._antialiasing_line.points



cdef class SmoothRectangle(Rectangle):
    '''Rectangle with antialiasing.

    :Parameters:
        Same as :class:`~kivy.graphics.vertex_instructions.Rectangle`.
    '''
    cdef AntiAliasingLine _antialiasing_line
    cdef public Texture default_texture

    def __cinit__(self, **kwargs):
        self._antialiasing_line = AntiAliasingLine(stencil_mask=self, close=1)
        Rectangle.__cinit__(self, **kwargs)
        self.default_texture = self.texture

    cdef void radd(self, InstructionGroup ig):
        radd_instructions(ig, self, self._antialiasing_line)

    cdef void rinsert(self, InstructionGroup ig, int index):
        rinsert_instructions(ig, index, self, self._antialiasing_line)

    cdef void rremove(self, InstructionGroup ig):
        rremove_instructions(ig, self, self._antialiasing_line)

    cdef void build(self):
        if has_texture_set(self) or too_small_for_antialiasing(self):
            self._antialiasing_line.points = []
            Rectangle.build(self)
        else:
            adjust_params(self, -1)
            Rectangle.build(self)
            self._antialiasing_line.points = self._points
            adjust_params(self, 1)

    @property
    def antialiasing_line_points(self):
        return self._antialiasing_line.points



cdef class SmoothEllipse(Ellipse):
    '''Ellipse with antialiasing.

    :Parameters:
        Same as :class:`~kivy.graphics.vertex_instructions.Ellipse`.
    '''
    cdef AntiAliasingLine _antialiasing_line
    cdef public Texture default_texture

    def __cinit__(self, **kwargs):
        self._antialiasing_line = AntiAliasingLine(stencil_mask=self, close=1)
        Ellipse.__cinit__(self, **kwargs)
        self.default_texture = self.texture

    cdef void radd(self, InstructionGroup ig):
        radd_instructions(ig, self, self._antialiasing_line)

    cdef void rinsert(self, InstructionGroup ig, int index):
        rinsert_instructions(ig, index, self, self._antialiasing_line)

    cdef void rremove(self, InstructionGroup ig):
        rremove_instructions(ig, self, self._antialiasing_line)

    cdef void build(self):
        if has_texture_set(self) or too_small_for_antialiasing(self):
            self._antialiasing_line.points = []
            Ellipse.build(self)
        else:
            adjust_params(self, -1)
            Ellipse.build(self)
            ellipse_center = [self.x + self.w / 2, self.y + self.h / 2]
            self._antialiasing_line.points = self._points + ellipse_center
            adjust_params(self, 1)

    @property
    def antialiasing_line_points(self):
        return self._antialiasing_line.points



cdef class SmoothQuad(Quad):
    """Quad with antialiasing.

    Its usage is the same as :class:`~kivy.graphics.vertex_instructions.Quad`

    .. note::
        There is still no support for texture antialiasing. Therefore, if a
        texture is defined using either ``texture`` or ``source``,
        antialiasing will be disabled.

    .. versionadded:: 2.3.0

    """

    cdef AntiAliasingLine _antialiasing_line
    cdef public Texture default_texture

    def __init__(self, **kwargs):
        self._antialiasing_line = AntiAliasingLine(stencil_mask=self, close=1)
        Quad.__init__(self, **kwargs)
        self.default_texture = self.texture

    cdef void radd(self, InstructionGroup ig):
        radd_instructions(ig, self, self._antialiasing_line)

    cdef void rinsert(self, InstructionGroup ig, int index):
        rinsert_instructions(ig, index, self, self._antialiasing_line)
    
    cdef void rremove(self, InstructionGroup ig):
        rremove_instructions(ig, self, self._antialiasing_line)

    cdef void build(self):
        if has_texture_set(self):
            self._antialiasing_line.points = []
            Quad.build(self)
        else:
            # adjust_params(self, -1)
            Quad.build(self)
            self._antialiasing_line.points = self._points
            # adjust_params(self, 1)
    
    @property
    def antialiasing_line_points(self):
        return self._antialiasing_line.points


cdef class SmoothTriangle(Triangle):
    """Triangle with antialiasing.

    Its usage is the same as :class:`~kivy.graphics.vertex_instructions.Triangle`

    .. note::
        There is still no support for texture antialiasing. Therefore, if a
        texture is defined using either ``texture`` or ``source``,
        antialiasing will be disabled.

    .. versionadded:: 2.3.0

    """

    cdef AntiAliasingLine _antialiasing_line
    cdef public Texture default_texture

    def __init__(self, **kwargs):
        self._antialiasing_line = AntiAliasingLine(stencil_mask=self, close=1)
        Triangle.__init__(self, **kwargs)
        self.default_texture = self.texture

    cdef void radd(self, InstructionGroup ig):
        radd_instructions(ig, self, self._antialiasing_line)

    cdef void rinsert(self, InstructionGroup ig, int index):
        rinsert_instructions(ig, index, self, self._antialiasing_line)
    
    cdef void rremove(self, InstructionGroup ig):
        rremove_instructions(ig, self, self._antialiasing_line)

    cdef void build(self):
        if has_texture_set(self):
            self._antialiasing_line.points = []
            Triangle.build(self)
        else:
            # adjust_params(self, -1)
            Triangle.build(self)
            self._antialiasing_line.points = self._points[:6]
            # adjust_params(self, 1)
        
    @property
    def antialiasing_line_points(self):
        return self._antialiasing_line.points
