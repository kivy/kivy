from kivy.graphics.opengl_utils cimport (gl_has_texture_native_format,
    gl_has_texture_conversion)
cimport cython
from cython cimport view as cyview
from cpython.array cimport array, clone


@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline convert_to_gl_format(data, fmt, width, height):
    ''' Takes data as a bytes object or an instance that implements the python
    buffer interface. If the data format is supported by opengl, the data
    is returned unchanged. Otherwise, the data is converted to a supported
    format, when possible, and returned as a python array object.

    Note that conversion is currently only supported for bytes data.
    '''
    cdef array ret_array
    cdef char *src_buffer
    cdef char *dst_buffer
    cdef char [::1] view
    cdef int datasize
    cdef str ret_format
    cdef int i, k
    cdef char c, c2
    cdef int pitch, rowlen
    cdef int pitchalign = 0

    # if native support of this format is available, use it
    if gl_has_texture_native_format(fmt):
        return data, fmt

    # no native support, can we at least convert it ?
    if not gl_has_texture_conversion(fmt):
        raise Exception('Unimplemented texture conversion for {}'.format(fmt))

    # do appropriate conversion, since we accepted it
    if isinstance(data, bytes):
        datasize = len(data)
        ret_array = clone(array('b'), datasize, False)
        src_buffer = <char *>data
    else:
        view = data
        datasize = view.nbytes
        ret_array = clone(array('b'), datasize, False)
        src_buffer = &view[0]
    dst_buffer = ret_array.data.as_chars

    # BGR -> RGB
    if fmt == 'bgr':
        ret_format = 'rgb'
        memcpy(dst_buffer, src_buffer, datasize)

        i = 0
        rowlen = width * 3
        pitch = (rowlen + 3) & ~3
        if rowlen * height < datasize:
            # FIXME: warn/fail if pitch * height != datasize:
            pitchalign = pitch - rowlen
            rowlen -= 1 # to match 0-based k below

        # note, this is the fastest copying method. copying element by element
        # from a memoryview is slower then copying the whole buffer and then
        # properly modifying the elements
        with nogil:
            while i < datasize:
                c = dst_buffer[i]
                k = i + 2
                dst_buffer[i] = dst_buffer[k]
                dst_buffer[k] = c
                if pitchalign and k % rowlen == 0:
                    i += pitchalign
                i += 3

    # BGRA -> RGBA
    elif fmt == 'bgra':
        ret_format = 'rgba'
        memcpy(dst_buffer, src_buffer, datasize)
        with nogil:
            for i in range(0, datasize, 4):
                c = dst_buffer[i]
                dst_buffer[i] = dst_buffer[i + 2]
                dst_buffer[i + 2] = c

    # ARGB -> RGBA
    elif fmt == 'argb':
        ret_format = 'rgba'
        memcpy(dst_buffer, &src_buffer[1], datasize-1)
        c2 = src_buffer[0]
        with nogil:
            for i in range(0, datasize, 4):
                c = dst_buffer[i+3]
                dst_buffer[i+3] = c2
                c2 = c

    # ABGR -> RGBA
    elif fmt == 'abgr':
        ret_format = 'rgba'
        memcpy(dst_buffer, &src_buffer[1], datasize-1)
        c2 = src_buffer[0]
        with nogil:
            for i in range(0, datasize, 4):
                c = dst_buffer[i+3]
                dst_buffer[i+3] = c2
                c2 = c

                c = dst_buffer[i]
                dst_buffer[i] = dst_buffer[i + 2]
                dst_buffer[i + 2] = c

    else:
        assert False, 'Non implemented texture conversion {}'.format(fmt)

    return ret_array, ret_format
