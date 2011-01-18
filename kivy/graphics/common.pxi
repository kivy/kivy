#
# Common definition
#

cdef double pi = 3.1415926535897931
cdef extern from "math.h":
    double cos(double) nogil
    double sin(double) nogil
    double sqrt(double) nogil

