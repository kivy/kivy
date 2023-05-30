cdef class Buffer:
    cdef void *data
    cdef int *l_free
    cdef int i_free
    cdef long block_size
    cdef long block_count

    cdef void clear(self)
    cdef void grow(self, long block_count)
    cdef void add(self, void *blocks, unsigned short *indices, int count)
    cdef void remove(self, unsigned short *indices, int count)
    cdef int count(self)
    cdef long size(self)
    cdef void *pointer(self)
    cdef void *offset_pointer(self, int offset)
    cdef void update(self, int index, void* blocks, int count)

