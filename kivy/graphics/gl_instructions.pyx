__all__ = ('ClearColor', 'ColorBuffers')


include "config.pxi"
include "opcodes.pxi"

from c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *
from instructions cimport Instruction



cdef class ClearColor(Instruction):
    ''' ClearColor Graphic Instruction
    Sets the clear color used to clear buffers with glClear function,
    or ClearBuffers graphics instructions.
    '''

    cdef float _r
    cdef float _g
    cdef float _b
    cdef float _a

    def __init__(self, r,g,b,a, **kwargs):
        Instruction.__init__(self, **kwargs)
        self.rgba =  [r,g,b,a]

    cdef void apply(self):
        glClearColor(self._r,self._g,self._b,self._a)

    property rgba:
        '''RGBA used for clear color, list of 4 values in 0-1 range
        '''
        def __get__(self):
            return [self._r, self._b, self._g, self._a]
        def __set__(self, rgba):
            cdef list clear_color =  map(float,rgba)
            self._r = clear_color[0]
            self._g = clear_color[1]
            self._b = clear_color[2]
            self._a = clear_color[3]


cdef class ClearBuffers(Instruction):
    ''' Clearbuffer Graphic Instruction
    Clear the buffers specified by the instructions buffer mask property.
    Same effect as calling glClear(mask)
    '''

    cdef GLbitfield _buffer_mask

    def __init__(self, *args, **kwargs):
        Instruction.__init__(self, *args, **kwargs)
        self._buffer_mask = GL_COLOR_BUFFER_BIT

    cdef void apply(self):
        glClear(self._buffer_mask)

    property mask:
        def __get__(self):
            return self._buffer_mask
        def __set__(self, mask):
            self._buffer_mask = mask

