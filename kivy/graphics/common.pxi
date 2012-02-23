#
# Common definition
#

cdef extern from *:
    ctypedef char* const_char_ptr "const char*"

cdef double pi = 3.1415926535897931
cdef extern from "math.h":
    double cos(double) nogil
    double sin(double) nogil
    double sqrt(double) nogil

cdef extern from "stdlib.h":
    ctypedef unsigned long size_t
    void free(void *ptr) nogil
    void *realloc(void *ptr, size_t size) nogil
    void *malloc(size_t size) nogil
    void *calloc(size_t nmemb, size_t size) nogil

cdef extern from "string.h":
    void *memcpy(void *dest, void *src, size_t n)

cdef extern from "Python.h":
    object PyString_FromStringAndSize(char *s, Py_ssize_t len)
