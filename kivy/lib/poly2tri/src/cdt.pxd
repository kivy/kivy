cdef extern from "../poly2tri/sweep/cdt.h":
    ctypedef struct c_CDT "p2t::CDT":
        void AddHole(point_vec polyline)
        void AddPoint(c_Point* point)
        void Triangulate()
        triangle_vec GetTriangles()
    c_CDT *new_CDT "new p2t::CDT" (point_vec polyline)
    void del_CDT "delete" (c_CDT *cdt)
    