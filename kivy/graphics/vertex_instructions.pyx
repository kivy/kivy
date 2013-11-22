'''
Vertex Instructions
===================

This module include all the classes for drawing simple vertex object.
'''

__all__ = ('Triangle', 'Quad', 'Rectangle', 'BorderImage', 'Ellipse', 'Line',
           'Point', 'Mesh', 'GraphicException', 'Bezier')


include "config.pxi"
include "common.pxi"

from kivy.graphics.vbo cimport *
from kivy.graphics.vertex cimport *
from kivy.graphics.instructions cimport *
from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.logger import Logger
from kivy.graphics.texture cimport Texture


class GraphicException(Exception):
    '''Exception fired when a graphic error is fired.
    '''

include "vertex_instructions_line.pxi"


cdef class Bezier(VertexInstruction):
    '''A 2d Bezier curve.

    .. versionadded:: 1.0.8

    :Parameters:
        `points`: list
            List of points in the format (x1, y1, x2, y2...)
        `segments`: int, default to 180
            Define how much segment is needed for drawing the ellipse.
            The drawing will be smoother if you have lot of segment.
        `loop`: bool, default to False
            Set the bezier curve to join last point to first.
        `dash_length`: int
            length of a segment (if dashed), default 1
        `dash_offset`: int
            distance between the end of a segment and the start of the
            next one, default 0, changing this makes it dashed.
    '''

    # TODO: refactoring:
    #
    #    a) find interface common to all splines (given control points and
    #    perhaps tangents, what's the position on the spline for parameter t),
    #
    #    b) make that a superclass Spline,
    #    c) create BezierSpline subclass that does the computation

    cdef list _points
    cdef int _segments
    cdef bint _loop
    cdef int _dash_offset, _dash_length

    def __init__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        v = kwargs.get('points')
        self.points = v if v is not None else [0, 0, 0, 0, 0, 0, 0, 0]
        self._segments = kwargs.get('segments') or 10
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
        for x in xrange(self._segments):
            l = x / (1.0 * self._segments)
            # http://en.wikipedia.org/wiki/De_Casteljau%27s_algorithm
            # as the list is in the form of (x1, y1, x2, y2...) iteration is
            # done on each item and the current item (xn or yn) in the list is
            # replaced with a calculation of "xn + x(n+1) - xn" x(n+1) is
            # placed at n+2. each iteration makes the list one item shorter
            for i in range(1, len(T)):
                for j in xrange(len(T) - 2*i):
                    T[j] = T[j] + (T[j+2] - T[j]) * l

            # we got the coordinates of the point in T[0] and T[1]
            vertices[x].x = T[0]
            vertices[x].y = T[1]
            if self._dash_offset != 0 and x > 0:
                tex_x += sqrt(
                        pow(vertices[x].x - vertices[x-1].x, 2) +
                        pow(vertices[x].y - vertices[x-1].y, 2)) / (
                                self._dash_length + self._dash_offset)

                vertices[x].s0 = tex_x
                vertices[x].t0 = 0

            indices[x] = x

        # add one last point to join the curve to the end
        vertices[x+1].x = T[-2]
        vertices[x+1].y = T[-1]

        tex_x += sqrt(
                (vertices[x+1].x - vertices[x].x) ** 2 +
                (vertices[x+1].y - vertices[x].y) ** 2) / (
                        self._dash_length + self._dash_offset)

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

    property points:
        '''Property for getting/settings points of the triangle

        .. warning::

            This will always reconstruct the whole graphics from the new points
            list. It can be very CPU expensive.
        '''
        def __get__(self):
            return self._points
        def __set__(self, points):
            self._points = list(points)
            if self._loop:
                self._points.extend(points[:2])
            self.flag_update()

    property segments:
        '''Property for getting/setting the number of segments of the curve
        '''
        def __get__(self):
            return self._segments
        def __set__(self, value):
            if value <= 1:
                raise GraphicException('Invalid segments value, must be >= 2')
            self._segments = value
            self.flag_update()

    property dash_length:
        '''Property for getting/stting the length of the dashes in the curve
        '''
        def __get__(self):
            return self._dash_length

        def __set__(self, value):
            if value < 0:
                raise GraphicException('Invalid dash_length value, must be >= 0')
            self._dash_length = value
            self.flag_update()

    property dash_offset:
        '''Property for getting/setting the offset between the dashes in the curve
        '''
        def __get__(self):
            return self._dash_offset

        def __set__(self, value):
            if value < 0:
                raise GraphicException('Invalid dash_offset value, must be >= 0')
            self._dash_offset = value
            self.flag_update()


cdef class Mesh(VertexInstruction):
    '''A 2d mesh.

    The format of vertices are actually fixed, this might change in a future
    release. Right now, each vertex is described with 2D coordinates (x, y) and
    a 2D texture coordinate (u, v).

    In OpenGL ES 2.0 and in our graphics implementation, you cannot have more
    than 65535 indices.

    A list of vertices is described as::

        vertices = [x1, y1, u1, v1, x2, y2, u2, v2, ...]
                    |            |  |            |
                    +---- i1 ----+  +---- i2 ----+

    If you want to draw a triangles, put 3 vertices, then you can make an
    indices list as:

        indices = [0, 1, 2]

    .. versionadded:: 1.1.0

    :Parameters:
        `vertices`: list
            List of vertices in the format (x1, y1, u1, v1, x2, y2, u2, v2...)
        `indices`: list
            List of indices in the format (i1, i2, i3...)
        `mode`: str
            Mode of the vbo. Check :data:`mode` for more information. Default to
            'points'.

    '''
    cdef list _vertices
    cdef list _indices
    cdef VertexFormat vertex_format

    def __init__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        v = kwargs.get('vertices')
        self.vertices = v if v is not None else []
        v = kwargs.get('indices')
        self.indices = v if v is not None else []
        fmt = kwargs.get('fmt')
        if fmt is not None:
            self.vertex_format = VertexFormat(*fmt)
            self.batch = VertexBatch(vbo=VBO(self.vertex_format))
        self.mode = kwargs.get('mode') or 'points'

    cdef void build(self):
        cdef int i
        cdef long vcount = len(self._vertices)
        cdef long icount = len(self._indices)
        cdef float *vertices = NULL
        cdef unsigned short *indices = NULL
        cdef list lvertices = self._vertices
        cdef list lindices = self._indices
        cdef vsize = self.batch.vbo.vertex_format.vsize

        if vcount == 0 or icount == 0:
            self.batch.clear_data()
            return

        vertices = <float *>malloc(vcount * sizeof(float))
        if vertices == NULL:
            raise MemoryError('vertices')

        indices = <unsigned short *>malloc(icount * sizeof(unsigned short))
        if indices == NULL:
            free(vertices)
            raise MemoryError('indices')

        for i in xrange(vcount):
            vertices[i] = lvertices[i]
        for i in xrange(icount):
            indices[i] = lindices[i]

        self.batch.set_data(vertices, <int>(vcount / vsize), indices, <int>icount)

        free(vertices)
        free(indices)

    property vertices:
        '''List of x, y, u, v, ... used to construct the Mesh. Right now, the
        Mesh instruction doesn't allow you to change the format of the vertices,
        mean it's only x/y + one texture coordinate.
        '''
        def __get__(self):
            return self._vertices
        def __set__(self, value):
            self._vertices = list(value)
            self.flag_update()

    property indices:
        '''Vertex indices used to know which order you wanna do for drawing the
        mesh.
        '''
        def __get__(self):
            return self._indices
        def __set__(self, value):
            if len(value) > 65535:
                raise GraphicException(
                    'Cannot upload more than 65535 indices'
                    '(OpenGL ES 2 limitation)')
            self._indices = list(value)
            self.flag_update()

    property mode:
        '''VBO Mode used for drawing vertices/indices. Can be one of: 'points',
        'line_strip', 'line_loop', 'lines', 'triangle_strip', 'triangle_fan'
        '''
        def __get__(self):
            self.batch.get_mode()
        def __set__(self, mode):
            self.batch.set_mode(mode)



cdef class Point(VertexInstruction):
    '''A 2d line.

    :Parameters:
        `points`: list
            List of points in the format (x1, y1, x2, y2...)
        `pointsize`: float, default to 1.
            Size of the point (1. mean the real size will be 2)

    .. warning::

        Starting from version 1.0.7, vertex instruction have a limit of 65535
        vertices (indices of vertex to be accurate).
        2 entry in the list (x + y) will be converted to 4 vertices. So the
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
        '''Add a point into the current :data:`points` list.

        If you intend to add multiple point, prefer to use this method, instead
        of reassign a new :data:`points` list. Assigning a new :data:`points`
        list will recalculate and reupload the whole buffer into GPU.
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
            self.parent.flag_update()

    property points:
        '''Property for getting/settings points of the triangle
        '''
        def __get__(self):
            return self._points
        def __set__(self, points):
            if self._points == points:
                return
            cdef list _points = list(points)
            if len(_points) > 2**15-2:
                raise GraphicException('Too many elements (limit is 2^15-2)')
            self._points = list(points)
            self.flag_update()

    property pointsize:
        '''Property for getting/setting point size
        '''
        def __get__(self):
            return self._pointsize
        def __set__(self, float pointsize):
            if self._pointsize == pointsize:
                return
            self._pointsize = pointsize
            self.flag_update()


cdef class Triangle(VertexInstruction):
    '''A 2d triangle.

    :Parameters:
        `points`: list
            List of point in the format (x1, y1, x2, y2, x3, y3)
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

    property points:
        '''Property for getting/settings points of the triangle
        '''
        def __get__(self):
            return self._points
        def __set__(self, points):
            self._points = list(points)
            self.flag_update()


cdef class Quad(VertexInstruction):
    '''A 2d quad.

    :Parameters:
        `points`: list
            List of point in the format (x1, y1, x2, y2, x3, y3, x4, y4)
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

    property points:
        '''Property for getting/settings points of the quads
        '''
        def __get__(self):
            return self._points
        def __set__(self, points):
            self._points = list(points)
            if len(self._points) != 8:
                raise GraphicException(
                    'Quad: invalid number of points (%d instead of 8)' % len(
                    self._points))
            self.flag_update()


cdef class Rectangle(VertexInstruction):
    '''A 2d rectangle.

    :Parameters:
        `pos`: list
            Position of the rectangle, in the format (x, y)
        `size`: list
            Size of the rectangle, in the format (width, height)
    '''
    cdef float x,y,w,h

    def __init__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        v = kwargs.get('pos')
        self.pos = v if v is not None else (0, 0)
        v = kwargs.get('size')
        self.size = v if v is not None else (100, 100)

    cdef void build(self):
        cdef float x, y, w, h
        cdef float *tc = self._tex_coords
        cdef vertex_t vertices[4]
        cdef unsigned short *indices = [0, 1, 2, 2, 3, 0]

        x, y = self.x, self.y
        w, h = self.w, self.h

        vertices[0].x = x
        vertices[0].y = y
        vertices[0].s0 = tc[0]
        vertices[0].t0 = tc[1]
        vertices[1].x = x + w
        vertices[1].y = y
        vertices[1].s0 = tc[2]
        vertices[1].t0 = tc[3]
        vertices[2].x = x + w
        vertices[2].y = y + h
        vertices[2].s0 = tc[4]
        vertices[2].t0 = tc[5]
        vertices[3].x = x
        vertices[3].y = y + h
        vertices[3].s0 = tc[6]
        vertices[3].t0 = tc[7]

        self.batch.set_data(vertices, 4, indices, 6)

    property pos:
        '''Property for getting/settings the position of the rectangle
        '''
        def __get__(self):
            return (self.x, self.y)
        def __set__(self, pos):
            cdef float x, y
            x, y = pos
            if self.x == x and self.y == y:
                return
            self.x = x
            self.y = y
            self.flag_update()

    property size:
        '''Property for getting/settings the size of the rectangle
        '''
        def __get__(self):
            return (self.w, self.h)
        def __set__(self, size):
            cdef float w, h
            w, h = size
            if self.w == w and self.h == h:
                return
            self.w = w
            self.h = h
            self.flag_update()



cdef class BorderImage(Rectangle):
    '''A 2d border image. The behavior of the border image is similar to the
    concept of CSS3 border-image.

    :Parameters:
        `border`: list
            Border information in the format (top, right, bottom, left).
            Each value is in pixels.
    '''
    cdef list _border

    def __init__(self, **kwargs):
        Rectangle.__init__(self, **kwargs)
        v = kwargs.get('border')
        self.border = v if v is not None else (10, 10, 10, 10)

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

        # width and heigth of texture in pixels, and tex coord space
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
        # border width(px)/texture width(px) *  tcoord width
        cdef list b = self._border
        cdef float b0, b1, b2, b3
        cdef float tb[4] # border offset in texture coordinate space
        b0, b1, b2, b3 = b
        tb[0] = b0 / th * tch
        tb[1] = b1 / tw * tcw
        tb[2] = b2 / th * tch
        tb[3] = b3 / tw * tcw


        # horizontal and vertical sections
        cdef float hs[4]
        cdef float vs[4]
        hs[0] = x;            vs[0] = y
        hs[1] = x + b3;       vs[1] = y + b0
        hs[2] = x + w - b1;   vs[2] = y + h - b2
        hs[3] = x + w;        vs[3] = y + h

        cdef float ths[4]
        cdef float tvs[4]
        ths[0] = tc0;              tvs[0] = tc1
        ths[1] = tc0 + tb[3];      tvs[1] = tc1 + tb[0]
        ths[2] = tc0 + tcw-tb[1];  tvs[2] = tc1 + tch - tb[2]
        ths[3] = tc0 + tcw;        tvs[3] = tc1 + tch

        '''
            v9---v8------v7----v6
            |        b2        |
           v10  v15------v14   v5
            |    |        |    |
            |-b4-|        |-b1-|
            |    |        |    |
           v11  v12------v13   v4
            |        b0        |
            v0---v1------v2----v3
        '''

        # set the vertex data
        # WARNING we are allocating the vertices as a float
        # because we know exactly the format.
        assert(sizeof(vertex_t) == 4 * sizeof(float))
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
            12, 13, 14,    14, 15, 12]  # center middel

        self.batch.set_data(<vertex_t *>vertices, 16, indices, 54)


    property border:
        '''Property for getting/setting the border of the class
        '''
        def __get__(self):
            return self._border
        def __set__(self, b):
            self._border = list(b)
            self.flag_update()


cdef class Ellipse(Rectangle):
    '''A 2D ellipse.

    .. versionadded:: 1.0.7 added angle_start + angle_end

    :Parameters:
        `segments`: int, default to 180
            Define how much segment is needed for drawing the ellipse.
            The drawing will be smoother if you have lot of segment.
        `angle_start`: int default to 0
            Specifies the starting angle, in degrees, of the disk portion
        `angle_end`: int default to 360
            Specifies the ending angle, in degrees, of the disk portion
    '''
    cdef int _segments
    cdef float _angle_start
    cdef float _angle_end

    def __init__(self, *args, **kwargs):
        Rectangle.__init__(self, **kwargs)
        self.batch.set_mode('triangle_fan')
        self._segments = kwargs.get('segments') or 180
        self._angle_start = kwargs.get('angle_start') or 0
        self._angle_end = kwargs.get('angle_end') or 360

    cdef void build(self):
        cdef float *tc = self._tex_coords
        cdef int i, angle_dir
        cdef float angle_start, angle_end, angle_range
        cdef float x, y, angle, rx, ry, ttx, tty, tx, ty, tw, th
        cdef float cx, cy, tangetial_factor, radial_factor, fx, fy
        cdef vertex_t *vertices = NULL
        cdef unsigned short *indices = NULL
        cdef int count = self._segments

        if self.w == 0 or self.h == 0:
            return

        tx = tc[0]
        ty = tc[1]
        tw = tc[4] - tx
        th = tc[5] - ty
        angle = 0.0
        rx = 0.5 * self.w
        ry = 0.5 * self.h

        vertices = <vertex_t *>malloc((count + 2) * sizeof(vertex_t))
        if vertices == NULL:
            raise MemoryError('vertices')

        indices = <unsigned short *>malloc((count + 2) * sizeof(unsigned short))
        if indices == NULL:
            free(vertices)
            raise MemoryError('indices')

        # calculate the start/end angle in radians, and adapt the range
        if self._angle_end > self._angle_start:
            angle_dir = 1
        else:
            angle_dir = -1

        # rad = deg * (pi / 180), where pi / 180 = 0.0174...
        angle_start = self._angle_start * 0.017453292519943295
        angle_end = self._angle_end * 0.017453292519943295
        angle_range = -1 * (angle_end - angle_start) / self._segments

        # add start vertex in the middle
        x = self.x + rx
        y = self.y + ry
        ttx = ((x - self.x) / self.w) * tw + tx
        tty = ((y - self.y) / self.h) * th + ty
        vertices[0].x = self.x + rx
        vertices[0].y = self.y + ry
        vertices[0].s0 = ttx
        vertices[0].t0 = tty
        indices[0] = 0

        # super fast ellipse drawing
        # credit goes to: http://slabode.exofire.net/circle_draw.shtml
        tangetial_factor = tan(angle_range)
        radial_factor = cos(angle_range)

        # Calculate the coordinates for a circle with radius 0.5 about
        # the point (0.5, 0.5). Only stretch to an ellipse later.
        cx = 0.5
        cy = 0.5
        r = 0.5
        x = r * sin(angle_start)
        y = r * cos(angle_start)

        for i in xrange(1, count + 2):
            ttx = (cx + x) * tw + tx
            tty = (cy + y) * th + ty
            real_x = self.x + (cx + x) * self.w
            real_y = self.y + (cy + y) * self.h
            vertices[i].x = real_x
            vertices[i].y = real_y
            vertices[i].s0 = ttx
            vertices[i].t0 = tty
            indices[i] = i

            fx = -y
            fy = x
            x += fx * tangetial_factor
            y += fy * tangetial_factor
            x *= radial_factor
            y *= radial_factor

        self.batch.set_data(vertices, count + 2, indices, count + 2)

        free(vertices)
        free(indices)

    property segments:
        '''Property for getting/setting the number of segments of the ellipse
        '''
        def __get__(self):
            return self._segments
        def __set__(self, value):
            self._segments = value
            self.flag_update()

    property angle_start:
        '''Angle start of the ellipse in degrees, default to 0
        '''
        def __get__(self):
            return self._angle_start
        def __set__(self, value):
            self._angle_start = value
            self.flag_update()

    property angle_end:
        '''Angle end of the ellipse in degrees, default to 360
        '''
        def __get__(self):
            return self._angle_end
        def __set__(self, value):
            self._angle_end = value
            self.flag_update()

    

