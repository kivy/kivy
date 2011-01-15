#cython: embedsignature=True

'''
Vertex Instructions
===================

This module include all the classes for drawing simple vertex object.
'''

__all__ = ('Triangle', 'Quad', 'Rectangle', 'BorderImage', 'Ellipse', 'Line',
           'Point')


include "config.pxi"
include "common.pxi"

from vbo cimport *
from vertex cimport *
from instructions cimport *
from c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *
from kivy.logger import Logger

cdef class Line(VertexInstruction):
    '''A 2d line.

    :Parameters:
        `points`: list
            List of points in the format (x1, y1, x2, y2...)
    '''
    cdef list _points

    def __init__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        self.points = kwargs.get('points', [])
        self.batch.set_mode('points')

    cdef build(self):
        cdef int i, count = len(self.points) / 2
        cdef list p = self.points
        self.vertices = [Vertex(p[i*2], p[i*2+1]) for i in xrange(count)]
        self.indices = range(count)

    property points:
        '''Property for getting/settings points of the triangle
        '''
        def __get__(self):
            return self._points
        def __set__(self, points):
            self._points = list(points)
            self.flag_update()

cdef class Point(VertexInstruction):
    '''A 2d line.

    :Parameters:
        `points`: list
            List of points in the format (x1, y1, x2, y2...)
        `pointsize`: float, default to 1.
            Size of the point (1. mean the real size will be 2)
    '''
    cdef list _points
    cdef float _pointsize

    def __init__(self, **kwargs):
        VertexInstruction.__init__(self, **kwargs)
        self.points = kwargs.get('points', [])
        self.pointsize = kwargs.get('pointsize', 1.)

    cdef build(self):
        cdef float x, y, ps = self._pointsize
        cdef int i, ii, count = len(self.points) / 2
        cdef list p = self.points
        cdef list vv = []
        cdef list vi = []
        cdef list tc = self._tex_coords
        for i in xrange(count):
            x = p[i*2]
            y = p[i*2+1]
            vv.append(Vertex(x - ps, y - ps, tc[0], tc[1]))
            vv.append(Vertex(x + ps, y - ps, tc[2], tc[3]))
            vv.append(Vertex(x + ps, y + ps, tc[4], tc[5]))
            vv.append(Vertex(x - ps, y + ps, tc[6], tc[7]))
            ii = i * 4
            vi.extend([ii, ii+1, ii+2, ii+2, ii+3, ii])
        self.vertices = vv
        self.indices = vi

    property points:
        '''Property for getting/settings points of the triangle
        '''
        def __get__(self):
            return self._points
        def __set__(self, points):
            if self._points == points:
                return
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

    cdef build(self):
        cdef list vc, tc
        vc = self.points;  tc = self._tex_coords

        self.vertices = [
            Vertex(vc[0], vc[1], tc[0], tc[1]),
            Vertex(vc[2], vc[3], tc[2], tc[3]),
            Vertex(vc[4], vc[5], tc[4], tc[5])]

        self.indices = [0,1,2]

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

    cdef build(self):
        cdef list vc, tc
        vc = self.points;  tc = self._tex_coords

        self.vertices = [
            Vertex(vc[0], vc[1], tc[0], tc[1]),
            Vertex(vc[2], vc[3], tc[2], tc[3]),
            Vertex(vc[4], vc[5], tc[4], tc[5]),
            Vertex(vc[6], vc[7] ,tc[6], tc[7])]

        self.indices = [0,1,2, 2,3,0]

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

    cdef build(self):
        cdef float x, y, w, h
        x, y = self.x, self.y
        w, h = self.w, self.h
        cdef list tc = self._tex_coords

        self.vertices = [
            Vertex( x,   y,   tc[0], tc[1]),
            Vertex( x+w, y,   tc[2], tc[3]),
            Vertex( x+w, y+h, tc[4], tc[5]),
            Vertex( x,   y+h, tc[6], tc[7])]

        self.indices  = [0,1,2, 2,3,0]

    property pos:
        '''Property for getting/settings the position of the rectangle
        '''
        def __get__(self):
            return (self.x, self.y)
        def __set__(self, pos):
            self.x = pos[0]
            self.y = pos[1]
            self.flag_update()

    property size:
        '''Property for getting/settings the size of the rectangle
        '''
        def __get__(self):
            return (self.w, self.h)
        def __set__(self, size):
            self.w = size[0]
            self.h = size[1]
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

    cdef build(self):
        if not self.texture:
            Logger.trace('GBorderImage: texture missing')
            return

        #pos and size of border rectangle
        cdef float x,y,w,h
        x=self.x;  y=self.y; w=self.w;  h=self.h

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
        tb[0] = b[0] / th*tch
        tb[1] = b[1] / tw*tcw
        tb[2] = b[2] / th*tch
        tb[3] = b[3] / tw*tcw


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
        self.vertices = [
            Vertex(hs[0], vs[0], ths[0], tvs[0]), #v0
            Vertex(hs[1], vs[0], ths[1], tvs[0]), #v1
            Vertex(hs[2], vs[0], ths[2], tvs[0]), #v2
            Vertex(hs[3], vs[0], ths[3], tvs[0]), #v3
            Vertex(hs[3], vs[1], ths[3], tvs[1]), #v4
            Vertex(hs[3], vs[2], ths[3], tvs[2]), #v5
            Vertex(hs[3], vs[3], ths[3], tvs[3]), #v6
            Vertex(hs[2], vs[3], ths[2], tvs[3]), #v7
            Vertex(hs[1], vs[3], ths[1], tvs[3]), #v8
            Vertex(hs[0], vs[3], ths[0], tvs[3]), #v9
            Vertex(hs[0], vs[2], ths[0], tvs[2]), #v10
            Vertex(hs[0], vs[1], ths[0], tvs[1]), #v11
            Vertex(hs[1], vs[1], ths[1], tvs[1]), #v12
            Vertex(hs[2], vs[1], ths[2], tvs[1]), #v13
            Vertex(hs[2], vs[2], ths[2], tvs[2]), #v14 
            Vertex(hs[1], vs[2], ths[1], tvs[2])] #v15

        self.indices = [
             0,  1, 12,    12, 11,  0,  # bottom left
             1,  2, 13,    13, 12,  1,  # bottom middle
             2,  3,  4,     4, 13,  2,  # bottom right
            13,  4,  5,     5, 14, 13,  # center right
            14,  5,  6,     6,  7, 14,  # top right
            15, 14,  7,     7,  8, 15,  # top middle
            10, 15,  8,     8,  9, 10,  # top left
            11, 12, 15,    15, 10, 11,  # center left
            12, 13, 14,    14, 15, 12]  # center middel


    property border:
        '''Property for getting/setting the border of the class
        '''
        def __get__(self):
            return self._border
        def __set__(self, b):
            self._border = list(b)
            self.flag_update()


cdef class Ellipse(Rectangle):
    '''A 2d ellipse.

    :Parameters:
        `segments`: int, default to 180
            Define how much segment is needed for drawing the ellipse.
            The drawing will be smoother if you have lot of segment.
    '''
    cdef int segments

    def __init__(self, *args, **kwargs):
        Rectangle.__init__(self, **kwargs)
        self.segments = kwargs.get('segments', 180)

    cdef build(self):
        cdef list tc = self.tex_coords
        cdef float x, y, angle, rx, ry, ttx, tty, tx, ty, tw, th
        tx = tc[0]; ty=tc[1];  tw=tc[4]-tx;  th=tc[5]-ty
        angle = 0.0
        rx = 0.5*(self.w)
        ry = 0.5*(self.h)

        self.vertices = list()
        for i in xrange(self.segments):
            # rad = deg * (pi / 180), where pi/180 = 0.0174...
            angle = i * 360.0/self.segments *0.017453292519943295
            x = (self.x+rx)+ (rx*cos(angle))
            y = (self.y+ry)+ (ry*sin(angle))
            ttx = ((x-self.x)/self.w)*tw + tx
            tty = ((y-self.y)/self.h)*th + ty
            self.vertices.append( Vertex(x, y, ttx, tty) )
            self.indices.extend([i, self.segments, (i+1)%self.segments])
        #add last verte in the middle
        x, y = self.x+rx, self.y+ry
        ttx = ((x-self.x)/self.w)*tw + tx
        tty = ((y-self.y)/self.h)*th + ty
        self.vertices.append( Vertex(x,y,ttx, tty) )

