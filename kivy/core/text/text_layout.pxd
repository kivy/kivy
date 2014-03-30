

cdef class LayoutWord:
    cdef public object text
    cdef public int lw, lh
    cdef public dict options


cdef class LayoutLine:
    cdef public int x, y, w, h
    cdef public int is_last_line
    cdef public list words
