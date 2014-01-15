cdef class Memory:
    cdef void *data
    cdef int size
    cdef int is_proxy
    cdef int read_only
    cdef Memory proxy(self, int i, int size)

cdef class BaseArray:
    cdef int itemsize
    cdef Memory mem
    cdef int count
    cdef int _resolve_slice(self, int *ip, int *jp)
    cdef void allocate(self, int count)
    cdef void link_to_memory(self, Memory mem)
    cdef void sync_with_memory(self)

cdef class FloatArray(BaseArray):
    cdef float *fdata
    cdef void sync_with_memory(self)

cdef class ByteArray(BaseArray):
    cdef unsigned char *cdata
    cdef void sync_with_memory(self)

