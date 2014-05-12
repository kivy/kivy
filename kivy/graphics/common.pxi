#
# Common definition
#

DEF PI2 = 1.5707963267948966
DEF PI = 3.1415926535897931

cdef extern from *:
    ctypedef char* const_char_ptr "const char*"

cdef double pi = PI
cdef extern from "math.h":
    double cos(double) nogil
    double sin(double) nogil
    double sqrt(double) nogil
    double pow(double x, double y) nogil
    double atan2(double y, double x) nogil
    double tan(double) nogil

cdef extern from "stdlib.h":
    ctypedef unsigned long size_t
    void free(void *ptr) nogil
    void *realloc(void *ptr, size_t size) nogil
    void *malloc(size_t size) nogil
    void *calloc(size_t nmemb, size_t size) nogil

cdef extern from "string.h":
    void *memcpy(void *dest, void *src, size_t n)
    void *memset(void *dest, int c, size_t len)

from cpython.array cimport array, clone


# these functions below, take a data element; if the data implements the
# buffer interface, the data is returned unchanged, otherwise, a python
# array is created from the data and returned.
# in both cases, the second parameter is initialized with a pointer to the
# starting address of the returned buffer
# The return value is a tuple, of (original data, array), where in the first
# case, array is None.
cdef inline _ensure_float_view(data, float **f):
    cdef array arr
    cdef list src
    cdef int i
    cdef float [::1] memview
    # do if/else instead of straight try/except because its faster for list
    if not isinstance(data, (tuple, list)):
        try:
            memview = data
            f[0] = &memview[0]
            return data, None
        except:
            src = list(data)
            arr = clone(array('f'), len(src), False)
            f[0] = arr.data.as_floats
            for i in range(len(src)):
                f[0][i] = src[i]
    else:
        src = list(data)
        arr = clone(array('f'), len(src), False)
        f[0] = arr.data.as_floats
        for i in range(len(src)):
            f[0][i] = src[i]
    return src, arr


cdef inline _ensure_ushort_view(data, unsigned short **f):
    cdef array arr
    cdef list src
    cdef int i
    cdef unsigned short [::1] memview
    # do if/else instead of straight try/except because its faster for list
    if not isinstance(data, (tuple, list)):
        try:
            memview = data
            f[0] = &memview[0]
            return data, None
        except:
            src = list(data)
            arr = clone(array('H'), len(src), False)
            f[0] = arr.data.as_ushorts
            for i in range(len(src)):
                f[0][i] = src[i]
    else:
        src = list(data)
        arr = clone(array('H'), len(src), False)
        f[0] = arr.data.as_ushorts
        for i in range(len(src)):
            f[0][i] = src[i]
    return src, arr
