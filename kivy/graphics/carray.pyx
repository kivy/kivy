'''
Module that implements array type classes.
'''

from libc.stdlib cimport malloc, free
from libc.string cimport memcpy

import ctypes


cdef class Memory:
    '''
    An abstracted class that stores memory buffers.

    *size* (int): If non-zero, a buffer of size size (in bytes) will be
    created. If zero, no buffer is created. Defaults to zero.

    *ctypes_array* (ctypes.Array): If not None, a ctypes array object which is
    used as the buffer. Defaults to None.

    *read_only* (bool): Whether the buffer should be read only. Defaults to
    False.

    ::

        import ctypes
        char_array = ctypes.c_char * (3 * texsize * texsize)
        data = char_array()
        memory = Memory(ctypes_array=data)

    '''

    def __cinit__(self, int size=0, ctypes_array=None, read_only=False):
        self.data = NULL
        self.size = 0
        self.read_only = read_only
        self.proxy_src = None

        if size != 0:
            self.data = malloc(size)
            self.size = size
            if self.data == NULL:
                raise MemoryError()
        elif ctypes_array is not None:
            if not isinstance(ctypes_array, ctypes.Array):
                raise TypeError()
            self.data = <void *><size_t>ctypes.addressof(ctypes_array)
            self.size = ctypes.sizeof(ctypes_array)
            self.proxy_src = ctypes_array  # keep ref to keep array alive


    def __init__(self, int size=0, ctypes_array=None, read_only=False):
        pass

    def __dealloc__(self):
        if self.data != NULL and self.proxy_src is None:
            free(self.data)

    cdef Memory proxy(self, int i, int size):
        cdef Memory mem = Memory()
        mem.data = self.data + i
        mem.size = size
        mem.proxy_src = self
        return mem


cdef class BaseArray:
    def __cinit__(self, count):
        self.mem = None
        self.count = count
        self.itemsize = 0

    def __init__(self, count):
        if count > 0:
            self.allocate(count)

    cdef void allocate(self, int count):
        self.mem = Memory(count * sizeof(float))
        self.count = count
        self.sync_with_memory()

    cdef void link_to_memory(self, Memory mem):
        self.mem = mem
        self.count = self.mem.size / self.itemsize
        self.sync_with_memory()

    cdef void sync_with_memory(self):
        pass

    def __dealloc__(self):
        self.mem = None

    def __len__(self):
        return self.count

    def __getslice__(self, int i, int j):
        cdef int count = self._resolve_slice(&i, &j)
        if count <= 0:
            return self.__class__(0)
        cdef BaseArray arr = self.__class__(0)
        cdef Memory memproxy = self.mem.proxy(
                i * self.itemsize, count * self.itemsize)
        arr.link_to_memory(memproxy)
        return arr

    def __setslice__(self, int i, int j, arr):
        cdef int count = self._resolve_slice(&i, &j)
        cdef int idx
        cdef BaseArray b_arr
        cdef list l_arr
        cdef tuple t_arr

        if isinstance(arr, BaseArray):
            # fast path
            b_arr = arr
            if count != b_arr.count:
                raise Exception('{} doesnt support reallocation'.format(
                    self.__class__.__name__))
            memcpy(self.mem.data + i * self.itemsize,
                    b_arr.mem.data, count * self.itemsize)
        elif isinstance(arr, list):
            l_arr = arr
            if count != len(l_arr):
                raise Exception('{} doesnt support reallocation'.format(
                    self.__class__.__name__))
            for idx in range(len(l_arr)):
                self[i + idx] = l_arr[idx]
        elif isinstance(arr, tuple):
            t_arr = arr
            if count != len(t_arr):
                raise Exception('{} doesnt support reallocation'.format(
                    self.__class__.__name__))
            for idx in range(len(t_arr)):
                self[i + idx] = t_arr[idx]
        elif isinstance(arr, str):
            for idx in range(len(arr)):
                self[i + idx] = ord(arr[idx])
        else:
            raise Exception('Unsupported source for slice')

    cdef int _resolve_slice(self, int *ip, int *jp):
        cdef int i = ip[0], j = jp[0]
        if i < 0:
            i = self.count + i
        if j < 0:
            j = self.count + j
        if i < 0:
            i = 0
        if i > self.count - 1:
            i = self.count - 1
        if j < 0:
            j = 0
        if j > self.count - 1:
            j = self.count - 1
        ip[0] = i
        jp[0] = j
        return j - i + 1

    def tolist(self):
        cdef list pl = [None, ] * self.count
        cdef int idx
        for idx in range(self.count):
            pl[idx] = self[idx]
        return pl


cdef class FloatArray(BaseArray):

    def __cinit__(self, count):
        self.fdata = NULL
        self.itemsize = sizeof(float)

    cdef void sync_with_memory(self):
        self.fdata = <float *>self.mem.data

    def __setitem__(self, int x, float y):
        if self.fdata != NULL:
            self.fdata[x] = y

    def __getitem__(self, int x):
        if self.fdata != NULL:
            return self.fdata[x]

    def tolist(self):
        cdef list pl = [None, ] * self.count
        cdef int idx
        for idx in range(self.count):
            pl[idx] = self.fdata[idx]
        return pl


cdef class ByteArray(BaseArray):

    def __cinit__(self, count):
        self.cdata = NULL
        self.itemsize = sizeof(unsigned char)

    cdef void sync_with_memory(self):
        self.cdata = <unsigned char *>self.mem.data

    def __setitem__(self, int x, b):
        if self.cdata == NULL:
            return
        if isinstance(b, bytes):
            self.cdata[x] = (<unsigned char*><bytes>b)[0]
        else:
            self.cdata[x] = b

    def __getitem__(self, int x):
        if self.cdata != NULL:
            return self.cdata[x]

    def __setslice__(self, int i, int j, arr):
        cdef int count = self._resolve_slice(&i, &j)
        cdef unsigned char *uc_arr
        if isinstance(arr, bytes) or isinstance(arr, bytearray):
            uc_arr = arr
            memcpy(self.mem.data + i * self.itemsize,
                    uc_arr, count * self.itemsize)
        else:
            BaseArray.__setslice__(self, i, j, arr)

    def tolist(self):
        cdef list pl = [None, ] * self.count
        cdef int idx
        for idx in range(self.count):
            pl[idx] = self.cdata[idx]
        return pl

    def tobytes(self):
        '''
        Returns a bytes representation of the array.
        '''
        cdef bytes py_str = self.cdata[:self.count * self.itemsize]
        return py_str
