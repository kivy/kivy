

cdef class LayoutWord:
    cdef public object text
    cdef public int lw, lh
    cdef public dict options


cdef class LayoutLine:
    cdef public int x, y, w, h
    cdef public int line_wrap  # whether this line wraps from last line
    cdef public int is_last_line  # in a paragraph
    cdef public list words
