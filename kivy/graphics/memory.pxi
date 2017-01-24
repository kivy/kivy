from cython cimport view as cyview


'''
These functions below, take a data element; if the data implements the
buffer interface, the data is returned unchanged, otherwise, a python
array is created from the data and returned.

in both cases, the second parameter is initialized with a pointer to the
starting address of the returned buffer

The return value is a tuple, of (original data, array), where in the first
case, array is None.

The method used below (a untyped python array + array.data.as_floats pointer)
results in the fastest list to array creation and usage. Even malloc isn't
faster. Note, using memoryview (which we avoided for this case) is relatively
slow in cython.

When the user passes in a memoryview type, we have no choice but to use the
memoryview passed in, though.
'''
cdef void track_free(void *ptr):
    print "track free", <unsigned long>ptr


cdef inline _ensure_float_view(data, float **f):
    cdef cyview.array arr
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
            pass

    # no way to get a memview about it, so we need to clone it
    arr = cyview.array(
        shape=(len(data), ), itemsize=sizeof(float), format="f", mode="c",
        allocate_buffer=True)
    arr.callback_free_data = track_free

    src = list(data)
    f[0] = (<float *>arr.data)
    for i in range(len(data)):
        f[0][i] = src[i]
    return src, arr

cdef inline _ensure_ushort_view(data, unsigned short **f):
    cdef cyview.array arr
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
            pass

    # no way to get a memview about it, so we need to clone it
    arr = cyview.array(
        shape=(len(data), ), itemsize=sizeof(unsigned short), format="H",
        mode="c", allocate_buffer=True)
    arr.callback_free_data = track_free

    src = list(data)
    f[0] = (<unsigned short *>arr.data)
    for i in range(len(data)):
        f[0][i] = src[i]
    return src, arr
