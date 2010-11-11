__all__ = ('Path', 'PathInstruction', 'PathStart', 'PathLineTo', 'PathClose',
           'PathFill', 'PathStroke', 'PathEnd')

include "graphics_common.pxi"

from graphics_instr_vdi cimport VertexDataInstruction
from graphics_vertex cimport vertex, vertex2f, vertex8f
from c_opengl cimport *
from kivy.logger import Logger

# tesselation of complex polygons
from kivy.c_ext.p2t import CDT, Point


cdef class Path
cdef Path _active_path = None

cdef class Path(VertexDataInstruction):
    def __init__(self):
        VertexDataInstruction.__init__(self)
        self.point_buffer = Buffer(sizeof(vertex))
        self.points  = list()

    cdef int add_point(self, float x, float y):
        cdef int idx
        cdef vertex v = vertex2f(x,y)
        for p in self. points:
            if abs(p.x-x) < 0.001 and abs(p.y-y) < 0.001:
                Logger("PATH: ignoring point(x,y)...already in list")
                return 0

        self.point_buffer.add(&v, &idx, 1)
        self.points.append(Point(x,y))
        return idx

    cdef build_stroke(self):
        cdef vertex* p    #pointer into point buffer
        cdef vertex v[4]  #to hold the vertices for each quad were creating
        cdef int  idx[4]  #to hold the vbo indecies for every quad we add
        cdef int num_points, i #number of points in path, loop counter
        cdef float x0,x1, y0,y1, dx,dy, ns, sw
        cdef int  end_point_idx[2]  # to connect end points from previous segment

        sw = 3.0 #self.pen.stroke_width
        p = <vertex*>self.point_buffer.pointer()
        num_points = self.point_buffer.count()

        #generate a quad for every line
        self.v_buffer = Buffer(sizeof(vertex))
        self.i_buffer = Buffer(sizeof(GLint))
        self.element_buffer = Buffer(sizeof(int))
        for i in range(num_points-1):
            #normals for this line: (-dy,dx), (dy,-dx)
            x0 = p[i].x;  x1 = p[i+1].x; dx = (x1-x0);
            y0 = p[i].y;  y1 = p[i+1].y; dy = (y1-y0);

            #normalize normal vector and scale for stroke offset
            ns = sqrt( (dx*dx) + (dy*dy) )
            if ns == 0.0:
                Logger.trace('GPath: skipping line, the two points are 0 '
                             'unit apart.')
                continue

            dx = sw/2.0 * dx/ns
            dy = sw/2.0 * dy/ns

            #create quad, with cornerss pull off the line by the normal
            v[0] = vertex8f(x0, y0, 0,0, -dy, dx, -1.0,-1.0);
            v[1] = vertex8f(x0, y0, 0,0,  dy,-dx,  1.0, 1.0);
            v[2] = vertex8f(x1, y1, 0,0,  dy,-dx,  1.0, 1.0);
            v[3] = vertex8f(x1, y1, 0,0, -dy, dx, -1.0,-1.0);

            #add vertices to vertex buffer, get vbo indices
            self.v_buffer.add(v, idx, 4)
            self.i_buffer.add(idx, NULL, 4)
            self.v_count = self.v_count + 4

            #and extend eleemnt buffer with indices to include this quad in draw
            #print "segment:", idx[0], idx[1], idx[2],  ":",  idx[2], idx[3], idx[0]
            self.element_buffer.add(&idx[0], NULL, 3)
            self.element_buffer.add(&idx[2], NULL, 2)
            self.element_buffer.add(&idx[0], NULL, 1)

            #also connect to the previous line segment with nice joint
            if i > 0: #not the first time...nothing to connect to
                #print "connection:", end_point_idx[0], end_point_idx[1], idx[0],  ":",  idx[0], idx[3], end_point_idx[0]
                self.element_buffer.add(end_point_idx, NULL, 2)
                self.element_buffer.add(&idx[0], NULL, 1)
                self.element_buffer.add(&idx[1], NULL, 1)
                self.element_buffer.add(&idx[1], NULL, 1)
                self.element_buffer.add(end_point_idx, NULL, 1)

            end_point_idx[0] = idx[3]
            end_point_idx[1] = idx[2]

        #update vertex and vbo index pointers
        self.v_data = <vertex*>  self.v_buffer.pointer()
        self.i_data = <int*>     self.i_buffer.pointer()
        self.element_data = <int*> self.element_buffer.pointer()
        self.num_elements = self.element_buffer.count()

        #actually add vertices to VBO
        self.vbo.add_vertices(self.v_data, self.i_data, self.v_count)
        self.canvas.add(self)
        self.canvas.update(self)


    cdef build_fill(self):

        cdef vertex v[4]  #to hold the vertices for each quad were creating
        cdef int  idx[4]  #to hold the vbo indecies for every quad we add
        cdef list triangles
        cdef list indices = []
        Logger.trace('GPath: build fill %s' % str(self.points))
        poly = CDT(self.points)
        triangles = poly.triangulate()


        cdef int i = 0
        self.v_buffer = Buffer(sizeof(vertex))
        self.i_buffer = Buffer(sizeof(GLint))
        for t in triangles:

            v[0] = vertex2f(t.a.x, t.a.y)
            v[1] = vertex2f(t.b.x, t.b.y)
            v[2] = vertex2f(t.c.x, t.c.y)
            self.v_count += 3

            self.v_buffer.add(v, idx, 3)
            self.i_buffer.add(idx, NULL, 3)
            indices.extend([i, i+1, i+2])
            i +=3


        #update vertex and vbo index pointers
        self.v_data = <vertex*>  self.v_buffer.pointer()
        self.i_data = <int*>     self.i_buffer.pointer()
        self.indices = indices

        #actually add vertices to VBO
        self.vbo.add_vertices(self.v_data, self.i_data, self.v_count)
        self.canvas.add(self)
        self.canvas.update(self)

cdef class PathInstruction(GraphicInstruction):
    def __init__(self):
        global _active_path
        GraphicInstruction.__init__(self, GI_IGNORE)
        self.path = _active_path



cdef class PathStart(PathInstruction):
    '''Starts a new path at position x,y.  Will raise an Excpetion, if called
    while another path is already started.

    :Parameters:
        `x`: float
            x position
        `y`: float
            y position
    '''
    def __init__(self):
        global _active_path
        PathInstruction.__init__(self)
        if _active_path != None:
            raise Exception("Can't start a new path while another one is being constructed")
        _active_path = self.path = Path()
        #self.index = self.path.add_point(x, y)


cdef class PathLineTo(PathInstruction):
    '''Adds a line from the current location to the x, y coordinates passed as
    parameters.
    '''
    def __init__(self, x, y):
        PathInstruction.__init__(self)
        self.index = self.path.add_point(x, y)


cdef class PathClose(PathInstruction):
    '''Closes the path, by adding a line from the current location to the first
    vertex taht started the path.
    '''
    def __init__(self):
        PathInstruction.__init__(self)
        cdef vertex* v = <vertex*> self.path.point_buffer.pointer()
        self.path.add_point(v[0].x, v[0].y)

cdef class PathFill(PathInstruction):
    '''Ends path construction on the current path, the path will be build
    and added to the canvas
    '''
    def __init__(self):
        global _active_path
        PathInstruction.__init__(self)
        self.path.build_fill()
        _active_path = None


cdef class PathStroke(PathInstruction):
    '''Ends path construction on the current path, the path will be build
    and added to the canvas
    '''
    def __init__(self):
        global _active_path
        PathInstruction.__init__(self)
        self.path.build_stroke()
        _active_path = None


cdef class PathEnd(PathStroke):
    pass

