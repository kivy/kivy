# Notes for optimizations
# - loop could be a array.array, but cython didn't release a version that
# support it yet (only in 0.17, in master.)
# it will be:
#   from cpython cimport array
#   cdef array.array[double] loop

include "common.pxi"

import re
pathdata_re = re.compile("([A-Za-z]|-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)")

class PathException(Exception):
    pass

cdef class Path:

    cdef int is_closed
    cdef float x, y, last_cx, last_cy
    cdef list loop
    cdef int bezier_points
    cdef list bezier_coefficients

    def __cinit__(self):
        self.is_closed = 0
        self.bezier_points = 10
        self.loop = list()

    def __init__(self):
        pass

    cpdef move_to(self, float x, float y):
        self.line_to(x, y)

    cpdef close(self):
        if self.is_closed:
            return
        if not self.loop:
            raise PathException('Empty loop, nothing to close.')
        add = self.loop.append
        add(self.loop[0])
        add(self.loop[1])
        self.is_closed = 1

    cpdef line_to(self, float x, float y):
        self.x = x
        self.y = y
        add = self.loop.append
        add(x)
        add(y)

    cpdef hline_to(self, float x):
        self.line_to(x, self.y)

    cpdef vline_to(self, float y):
        self.line_to(self.x, y)

    cpdef curve_to(self, float x1, float y1, float x2, float y2, float x, float y):
        cdef int i
        cdef float t, t0, t1, t2, t3, t4, yx, py
        cdef list a
        if not self.bezier_coefficients:
            self.bezier_coefficients = list()
            for i in xrange(self.bezier_points + 1):
                t = float(i)/self.bezier_points
                t0 = (1 - t) ** 3
                t1 = 3 * t * (1 - t) ** 2
                t2 = 3 * t ** 2 * (1 - t)
                t3 = t ** 3
                self.bezier_coefficients.append([t0, t1, t2, t3])
        self.last_cx = x2
        self.last_cy = y2
        add = self.loop.append
        for i, a in enumerate(self.bezier_coefficients):
            px = a[0] * self.x + a[1] * x1 + a[2] * x2 + a[3] * x
            py = a[0] * self.y + a[1] * y1 + a[2] * y2 + a[3] * y
            add(px)
            add(py)
        self.x = px
        self.y = py

    def arc_to(self, rx, ry, phi, large_arc, sweep, x, y):
        # This function is made out of magical fairy dust
        # http://www.w3.org/TR/2003/REC-SVG11-20030114/implnote.html#ArcImplementationNotes
        x1 = self.x
        y1 = self.y
        x2 = x
        y2 = y
        cp = cos(phi)
        sp = sin(phi)
        dx = .5 * (x1 - x2)
        dy = .5 * (y1 - y2)
        x_ = cp * dx + sp * dy
        y_ = -sp * dx + cp * dy
        r2 = (((rx * ry)**2 - (rx * y_)**2 - (ry * x_)**2)/
                ((rx * y_)**2 + (ry * x_)**2))
        if r2 < 0: r2 = 0
        r = sqrt(r2)
        if large_arc == sweep:
            r = -r
        cx_ = r * rx * y_ / ry
        cy_ = -r * ry * x_ / rx
        cx = cp * cx_ - sp * cy_ + .5 * (x1 + x2)
        cy = sp * cx_ + cp * cy_ + .5 * (y1 + y2)
        def angle(u, v):
            a = acos((u[0]*v[0] + u[1]*v[1]) / sqrt((u[0]**2 + u[1]**2) * (v[0]**2 + v[1]**2)))
            sgn = 1 if u[0]*v[1] > u[1]*v[0] else -1
            return sgn * a

        psi = angle((1,0), ((x_ - cx_)/rx, (y_ - cy_)/ry))
        delta = angle(((x_ - cx_)/rx, (y_ - cy_)/ry),
                      ((-x_ - cx_)/rx, (-y_ - cy_)/ry))
        if sweep and delta < 0: delta += pi * 2
        if not sweep and delta > 0: delta -= pi * 2
        n_points = max(int(abs(self.circle_points * delta / (2 * pi))), 1)

        for i in xrange(n_points + 1):
            theta = psi + i * delta / n_points
            ct = cos(theta)
            st = sin(theta)
            self.line_to(cp * rx * ct - sp * ry * st + cx,
                         sp * rx * ct + cp * ry * st + cy)


    cpdef rel_line_to(self, float x, float y):
        self.line_to(self.x + x, self.y + x)

    cpdef rel_hline_to(self, float x):
        self.line_to(self.x + x, self.y)

    cpdef rel_vline_to(self, float y):
        self.line_to(self.x, self.y + y)

    cpdef rel_curve_to(self, float x1, float y1, float x2, float y2, float x, float y):
        cdef float mx, my
        mx = self.x
        my = self.y
        self.curve_to(mx + x1, my + y1, mx + x2, my + y2, mx + x, my + y)

    cpdef from_svgpath(self, str svgpath):
        cdef list p = re.findall(pathdata_re, svgpath)
        cdef str opcode

        while p:
            opcode = p.pop(0)
            if opcode == 'M':
                self.move_to(*p[:2])
                p = p[2:]
            elif opcode == 'C':
                self.curve_to(*p[:6])
                p = p[6:]
            elif opcode == 'c':
                self.rel_curve_to(*p[:6])
                p = p[6:]
            elif opcode == 'S':
                self.curve_to(*p[:6])
                p = p[6:]
            elif opcode == 's':
                mx = self.x
                my = self.y
                x1 = 2 * self.x - self.last_cx
                y1 = 2 * self.y - self.last_cy
                self.curve_to(x1, y1, mx + p[0], my + p[1], mx + p[2], my + p[3])
            elif opcode == 'A':
                self.arc_to(*p[:7])
                p = p[7:]
            elif opcode in 'zZ':
                self.close_path()
            elif opcode == 'L':
                self.move_to(*p[:2])
                p = p[2:]
            elif opcode == 'l':
                self.rel_line_to(*p[:2])
                p = p[2:]
            elif opcode == 'H':
                self.hline_to(*p[:2])
                p = p[2:]
            elif opcode == 'h':
                self.rel_hline_to(*p[:2])
                p = p[2:]
            elif opcode == 'V':
                self.vline_to(*p[:2])
                p = p[2:]
            elif opcode == 'v':
                self.rel_vline_to(*p[:2])
                p = p[2:]
            else:
                print("Unrecognised opcode: " + opcode)

    property points:
        def __get__(self):
            return self.loop

