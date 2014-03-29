

cdef class LayoutWord:
    cdef readonly object text
    cdef readonly int lw, lh
    cdef readonly dict options


cdef class LayoutLine:
    cdef public int x, y, w, h
    cdef public int is_last_line
    cdef readonly list words
