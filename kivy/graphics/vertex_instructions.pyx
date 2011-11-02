#cython: embedsignature=True

'''
Vertex Instructions
===================

This module include all the classes for drawing simple vertex object.
'''

__all__ = ('Triangle', 'Quad', 'Rectangle', 'BorderImage', 'Ellipse', 'Line',
           'Point', 'GraphicException', 'Bezier')


include "config.pxi"
include "common.pxi"

from vbo cimport *
from vertex cimport *
from instructions cimport *
from c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *
from kivy.logger import Logger
from kivy.graphics.texture import Texture

cdef extern from "string.h":
    void *memset(void *s, int c, int n)

cdef extern from "Python.h":
    object PyString_FromStringAndSize(char *s, Py_ssize_t len)

cdef extern from "math.h":
    double sqrt(double x) nogil
    double pow(double x, double y) nogil

class GraphicException(Exception):
    '''Exception fired when a graphic error is fired.
    '''

cdef class Line(VertexInstruction):
    '''A 2d line.

    .. versionadded:: 1.0.8
        `dash_offset` and `dash_length` have been added

    :Parameters:
        `points`: list
            List of points in the format (x1, y1, x2, y2...)
        `dash_length`: int
            length of a segment (if dashed), default 1
        `dash_offset`: int
            offset between the end of a segments and the begining of the
            next one, default 0, changing this makes it dashed.
    '''
    cdef list _points
    cdef int _dash_offset, _dash_length

    def __init__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        self.points = kwargs.get('points', [])
        self.batch.set_mode('line_strip')
        self._dash_length = kwargs.get('dash_length', 1)
        self._dash_offset = kwargs.get('dash_offset', 0)

    cdef void build(self):
        cdef int i, count = len(self.points) / 2
        cdef list p = self.points
        cdef vertex_t *vertices = NULL
        cdef unsigned short *indices = NULL
        cdef float tex_x
        cdef char *buf = NULL
        cdef Texture texture = self.texture

        if count < 2:
            self.batch.clear_data()
            return

        if self._dash_offset != 0:
            if texture is None or texture._width != \
                (self._dash_length + self._dash_offset) or \
                texture._height != 1:

                self.texture = texture = Texture.create(
                        size=(self._dash_length + self._dash_offset, 1))
                texture.wrap = 'repeat'

            # create a buffer to fill our texture
            buf = <char *>malloc(3 * (self._dash_length + self._dash_offset))
            memset(buf, 255, self._dash_length * 3)
            memset(buf + self._dash_length * 3, 0, self._dash_offset * 3)
            p_str = PyString_FromStringAndSize(buf,  (self._dash_length + self._dash_offset) * 3)

            self.texture.blit_buffer(p_str, colorfmt='rgb', bufferfmt='ubyte')
            free(buf)

        elif texture is not None:
            self.texture = None

        vertices = <vertex_t *>malloc(count * sizeof(vertex_t))
        if vertices == NULL:
            raise MemoryError('vertices')

        indices = <unsigned short *>malloc(count * sizeof(unsigned short))
        if indices == NULL:
            free(vertices)
            raise MemoryError('indices')

        tex_x = 0
        for i in xrange(count):
            if self._dash_offset != 0 and i > 0:
                tex_x += sqrt(
                        pow(p[i * 2]     - p[(i - 1) * 2], 2)  +
                        pow(p[i * 2 + 1] - p[(i - 1) * 2 + 1], 2)) / (
                                self._dash_length + self._dash_offset)

                vertices[i].s0 = tex_x
                vertices[i].t0 = 0

            vertices[i].x = p[i * 2]
            vertices[i].y = p[i * 2 + 1]
            indices[i] = i

        self.batch.set_data(vertices, count, indices, count)

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
            self.flag_update()

    property dash_length:
        '''Property for getting/setting the length of the dashes in the curve

        .. versionadded:: 1.0.8
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

        .. versionadded:: 1.0.8
        '''
        def __get__(self):
            return self._dash_offset

        def __set__(self, value):
            if value < 0:
                raise GraphicException('Invalid dash_offset value, must be >= 0')
            self._dash_offset = value
            self.flag_update()


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
        self.points = kwargs.get('points', [0, 0, 0, 0, 0, 0, 0, 0])
        self._segments = kwargs.get('segments', 10)
        self._loop = kwargs.get('loop', False)
        if self._loop:
            self.points.extend(self.points[:2])
        self._dash_length = kwargs.get('dash_length', 1)
        self._dash_offset = kwargs.get('dash_offset', 0)
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
            buf = <char *>malloc(3 * (self._dash_length + self._dash_offset))
            memset(buf, 255, self._dash_length * 3)
            memset(buf + self._dash_length * 3, 0, self._dash_offset * 3)

            p_str = PyString_FromStringAndSize(buf,  (self._dash_length + self._dash_offset) * 3)

            texture.blit_buffer(p_str, colorfmt='rgb', bufferfmt='ubyte')
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

        tex_x = 0
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
        self.points = kwargs.get('points', [])
        self.pointsize = kwargs.get('pointsize', 1.)

    cdef void build(self):
        cdef float t0, t1, t2, t3, t4, t5, t6, t7
        cdef float x, y, ps = self._pointsize
        cdef int i, iv, ii, count = <int>(len(self._points) * 0.5)
        cdef list p = self.points
        cdef list tc = self._tex_coords
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

        t0, t1, t2, t3, t4, t5, t6, t7 = tc

        for i in xrange(count):
            x = p[i * 2]
            y = p[i * 2 + 1]
            iv = i * 4
            vertices[iv].x = x - ps
            vertices[iv].y = y - ps
            vertices[iv].s0 = t0
            vertices[iv].t0 = t1
            vertices[iv + 1].x = x + ps
            vertices[iv + 1].y = y - ps
            vertices[iv + 1].s0 = t2
            vertices[iv + 1].t0 = t3
            vertices[iv + 2].x = x + ps
            vertices[iv + 2].y = y + ps
            vertices[iv + 2].s0 = t4
            vertices[iv + 2].t0 = t5
            vertices[iv + 3].x = x - ps
            vertices[iv + 3].y = y + ps
            vertices[iv + 3].s0 = t6
            vertices[iv + 3].t0 = t7

            ii = i * 6
            indices[ii] = iv
            indices[ii + 1] = iv + 1
            indices[ii + 2] = iv + 2
            indices[ii + 3] = iv + 2
            indices[ii + 4] = iv + 3
            indices[ii + 5] = iv

        self.batch.set_data(vertices, count * 4, indices, count * 6)

        free(vertices)
        free(indices)

    def add_point(self, float x, float y):
        '''Add a point into the current :data:`points` list.

        If you intend to add multiple point, prefer to use this method, instead
        of reassign a new :data:`points` list. Assigning a new :data:`points`
        list will recalculate and reupload the whole buffer into GPU.
        If you use add_point, it will only upload the changes.
        '''
        cdef float t0, t1, t2, t3, t4, t5, t6, t7
        cdef float ps = self._pointsize
        cdef int iv, count = <int>(len(self._points) * 0.5)
        cdef list tc = self._tex_coords
        cdef vertex_t vertices[4]
        cdef unsigned short indices[6]

        if len(self._points) > 2**15 - 2:
            raise GraphicException('Cannot add elements (limit is 2^15-2)')

        self._points.append(x)
        self._points.append(y)

        t0, t1, t2, t3, t4, t5, t6, t7 = tc
        vertices[0].x = x - ps
        vertices[0].y = y - ps
        vertices[0].s0 = t0
        vertices[0].t0 = t1
        vertices[1].x = x + ps
        vertices[1].y = y - ps
        vertices[1].s0 = t2
        vertices[1].t0 = t3
        vertices[2].x = x + ps
        vertices[2].y = y + ps
        vertices[2].s0 = t4
        vertices[2].t0 = t5
        vertices[3].x = x - ps
        vertices[3].y = y + ps
        vertices[3].s0 = t6
        vertices[3].t0 = t7

        iv = count * 4
        indices[0] = iv
        indices[1] = iv + 1
        indices[2] = iv + 2
        indices[3] = iv + 2
        indices[4] = iv + 3
        indices[5] = iv

        # append the vertices / indices to current vertex batch
        self.batch.append_data(vertices, 4, indices, 6)

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
        self.points = kwargs.get('points', (0.0,0.0, 100.0,0.0, 50.0,100.0))

    cdef void build(self):
        cdef list vc, tc
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
        VertexInstruction.__init__(self)
        self.points = kwargs.get('points',
               (  0.0,  50.0,   50.0,   0.0,
                100.0,  50.0,   50.0, 100.0 ))

    cdef void build(self):
        cdef list vc, tc
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
        self.pos  = kwargs.get('pos',  (0,0))
        self.size = kwargs.get('size', (100,100))

    cdef void build(self):
        cdef float x, y, w, h
        cdef list tc = self._tex_coords
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
        self.border = kwargs.get('border', (10,10,10,10))

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
        cdef list tc = self._tex_coords
        tsize  = self.texture.size
        tw  = tsize[0]
        th  = tsize[1]
        tcw = tc[2] - tc[0]  #right - left
        tch = tc[7] - tc[1]  #top - bottom

        # calculate border offset in texture coord space
        # border width(px)/texture width(px) *  tcoord width
        cdef list b = self._border
        cdef float tb[4] # border offset in texture coordinate space
        tb[0] = b[0] / th * tch
        tb[1] = b[1] / tw * tcw
        tb[2] = b[2] / th * tch
        tb[3] = b[3] / tw * tcw


        # horizontal and vertical sections
        cdef float hs[4]
        cdef float vs[4]
        hs[0] = x;            vs[0] = y
        hs[1] = x + b[3];     vs[1] = y + b[0]
        hs[2] = x + w - b[1]; vs[2] = y + h - b[2]
        hs[3] = x + w;        vs[3] = y + h

        cdef float ths[4]
        cdef float tvs[4]
        ths[0] = tc[0];              tvs[0] = tc[1]
        ths[1] = tc[0] + tb[3];      tvs[1] = tc[1] + tb[0]
        ths[2] = tc[0] + tcw-tb[1];  tvs[2] = tc[1] + tch - tb[2]
        ths[3] = tc[0] + tcw;        tvs[3] = tc[1] + tch

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
        self._segments = kwargs.get('segments', 180)
        self._angle_start = kwargs.get('angle_start', 0)
        self._angle_end = kwargs.get('angle_end', 360)

    cdef void build(self):
        cdef list tc = self.tex_coords
        cdef int i, angle_dir
        cdef float angle_start, angle_end, angle_range
        cdef float x, y, angle, rx, ry, ttx, tty, tx, ty, tw, th
        cdef vertex_t *vertices = NULL
        cdef unsigned short *indices = NULL
        cdef int count = self._segments

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
        if self.angle_end > self.angle_start:
            angle_dir = 1
        else:
            angle_dir = -1
        # rad = deg * (pi / 180), where pi/180 = 0.0174...
        angle_start = self._angle_start * 0.017453292519943295
        angle_end = self._angle_end * 0.017453292519943295
        angle_range = abs(angle_end - angle_start) / self._segments

        # add start vertice in the middle
        x = self.x + rx
        y = self.y + ry
        ttx = ((x - self.x) / self.w) * tw + tx
        tty = ((y - self.y) / self.h) * th + ty
        vertices[0].x = self.x + rx
        vertices[0].y = self.y + ry
        vertices[0].s0 = ttx
        vertices[0].t0 = tty
        indices[0] = 0

        for i in xrange(1, count + 2):
            angle = angle_start + (angle_dir * (i - 1) * angle_range)
            x = (self.x+rx)+ (rx*sin(angle))
            y = (self.y+ry)+ (ry*cos(angle))
            ttx = ((x-self.x)/self.w)*tw + tx
            tty = ((y-self.y)/self.h)*th + ty
            vertices[i].x = x
            vertices[i].y = y
            vertices[i].s0 = ttx
            vertices[i].t0 = tty
            indices[i] = i

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

