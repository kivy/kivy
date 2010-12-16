cdef extern from "../poly2tri/common/shapes.h":

    ctypedef struct c_Point "p2t::Point":
        double x, y
    c_Point* new_Point "new p2t::Point" (double x, double y)
    void del_Point "delete" (c_Point* p)
    
    ctypedef struct c_Triangle "p2t::Triangle":
        inline c_Point* GetPoint(int index)
    c_Triangle *new_Triangle "new p2t::Triangle" (c_Point a, c_Point b, c_Point c)
    void del_Triangle "delete" (c_Triangle* t)
    
    ctypedef struct triangle_vec "std::vector<p2t::Triangle*>":
        void (* push_back)(c_Triangle* elem)
        inline c_Triangle* get "operator[]" (int i)
        int size()
    triangle_vec trianglevec_factory "std::vector<p2t::Triangle*>"(int len)
    
    ctypedef struct point_vec "std::vector<p2t::Point*>":
        void (* push_back)(c_Point* elem)
        inline c_Point* get "operator[]" (int i)
        int size()
    point_vec pointvec_factory "std::vector<p2t::Point*>"(int len)