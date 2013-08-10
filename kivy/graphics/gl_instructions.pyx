'''
GL instructions
===============

.. versionadded:: 1.3.0

Clearing an FBO
---------------

To clear an FBO, you can use :class:`ClearColor` and :class:`ClearBuffers`
instructions like this example::

    self.fbo = Fbo(size=self.size)
    with self.fbo:
        ClearColor(0, 0, 0, 0)
        ClearBuffers()

'''

__all__ = ('ClearColor', 'ClearBuffers')


include "config.pxi"
include "opcodes.pxi"

from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *
from kivy.graphics.instructions cimport Instruction


cdef class ClearColor(Instruction):
    ''' ClearColor Graphic Instruction.

    .. versionadded:: 1.3.0

    Sets the clear color used to clear buffers with glClear function, or
    :class:`ClearBuffers` graphics instructions.
    '''

    cdef float r
    cdef float g
    cdef float b
    cdef float a

    def __init__(self, r, g, b, a, **kwargs):
        Instruction.__init__(self, **kwargs)
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    cdef void apply(self):
        glClearColor(self.r, self.g, self.b, self.a)

    property rgba:
        '''RGBA used for clear color, list of 4 values in 0-1 range
        '''
        def __get__(self):
            return [self.r, self.b, self.g, self.a]
        def __set__(self, rgba):
            cdef list clear_color = [float(x) for x in rgba]
            self.r = clear_color[0]
            self.g = clear_color[1]
            self.b = clear_color[2]
            self.a = clear_color[3]
            self.flag_update()

    property rgb:
        '''RGB color, list of 3 values in 0-1 range, alpha will be 1.
        '''
        def __get__(self):
            return [self.r, self.g, self.b]
        def __set__(self, rgb):
            cdef list clear_color = [float(x) for x in rgb]
            self.r = clear_color[0]
            self.g = clear_color[1]
            self.b = clear_color[2]
            self.a = 1
            self.flag_update()

    property r:
        '''Red component, between 0-1
        '''
        def __get__(self):
            return self.r
        def __set__(self, r):
            self.r = r
            self.flag_update()

    property g:
        '''Green component, between 0-1
        '''
        def __get__(self):
            return self.g
        def __set__(self, g):
            self.g = g
            self.flag_update()

    property b:
        '''Blue component, between 0-1
        '''
        def __get__(self):
            return self.b
        def __set__(self, b):
            self.b = b
            self.flag_update()

    property a:
        '''Alpha component, between 0-1
        '''
        def __get__(self):
            return self.a
        def __set__(self, a):
            self.a = a
            self.flag_update()


cdef class ClearBuffers(Instruction):
    ''' Clearbuffer Graphic Instruction

    .. versionadded:: 1.3.0

    Clear the buffers specified by the instructions buffer mask property.
    By default, only the coloc buffer is cleared.
    '''

    cdef int clear_color
    cdef int clear_stencil
    cdef int clear_depth

    def __init__(self, *args, **kwargs):
        Instruction.__init__(self, *args, **kwargs)
        self.clear_color = int(kwargs.get('clear_color', 1))
        self.clear_stencil = int(kwargs.get('clear_stencil', 0))
        self.clear_depth = int(kwargs.get('clear_depth', 0))

    cdef void apply(self):
        cdef GLbitfield mask = 0
        if self.clear_color:
            mask |= GL_COLOR_BUFFER_BIT
        if self.clear_stencil:
            mask |= GL_STENCIL_BUFFER_BIT
        if self.clear_depth:
            mask |= GL_DEPTH_BUFFER_BIT
        glClear(mask)

    property clear_color:
        '''If true, the color buffer will be cleared
        '''
        def __get__(self):
            return self.clear_color
        def __set__(self, value):
            value = int(value)
            if value == self.clear_color:
                return
            self.clear_color = value

    property clear_stencil:
        '''If true, the stencil buffer will be cleared
        '''
        def __get__(self):
            return self.clear_stencil
        def __set__(self, value):
            value = int(value)
            if value == self.clear_stencil:
                return
            self.clear_stencil = value

    property clear_depth:
        '''If true, the depth buffer will be cleared
        '''
        def __get__(self):
            return self.clear_depth
        def __set__(self, value):
            value = int(value)
            if value == self.clear_depth:
                return
            self.clear_depth = value
