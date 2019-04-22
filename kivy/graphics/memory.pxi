from cpython.array cimport array, clone


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
        except Exception as e:
            import traceback; traceback.print_exc() 
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

