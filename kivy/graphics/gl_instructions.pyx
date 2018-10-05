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


include "../include/config.pxi"
include "opcodes.pxi"

from kivy.graphics.cgl cimport *
from kivy.graphics.instructions cimport Instruction


cdef class ClearColor(Instruction):
    ''' ClearColor Graphics Instruction.

    .. versionadded:: 1.3.0

    Sets the clear color used to clear buffers with the glClear function or
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

    cdef int apply(self) except -1:
        cgl.glClearColor(self.r, self.g, self.b, self.a)
        return 0

    @property
    def rgba(self):
        '''RGBA color used for the clear color, a list of 4 values in the 0-1
        range.
        '''
        return [self.r, self.b, self.g, self.a]

    @rgba.setter
    def rgba(self, rgba):
        cdef list clear_color = [float(x) for x in rgba]
        self.r = clear_color[0]
        self.g = clear_color[1]
        self.b = clear_color[2]
        self.a = clear_color[3]
        self.flag_update()

    @property
    def rgb(self):
        '''RGB color, a list of 3 values in 0-1 range where alpha will be 1.
        '''
        return [self.r, self.g, self.b]

    @rgb.setter
    def rgb(self, rgb):
        cdef list clear_color = [float(x) for x in rgb]
        self.r = clear_color[0]
        self.g = clear_color[1]
        self.b = clear_color[2]
        self.a = 1
        self.flag_update()

    @property
    def r(self):
        '''Red component, between 0 and 1.
        '''
        return self.r

    @r.setter
    def r(self, r):
        self.r = r
        self.flag_update()

    @property
    def g(self):
        '''Green component, between 0 and 1.
        '''
        return self.g

    @g.setter
    def g(self, g):
        self.g = g
        self.flag_update()

    @property
    def b(self):
        '''Blue component, between 0 and 1.
        '''
        return self.b

    @b.setter
    def b(self, b):
        self.b = b
        self.flag_update()

    @property
    def a(self):
        '''Alpha component, between 0 and 1.
        '''
        return self.a

    @a.setter
    def a(self, a):
        self.a = a
        self.flag_update()


cdef class ClearBuffers(Instruction):
    ''' Clearbuffer Graphics Instruction.

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

    cdef int apply(self) except -1:
        cdef GLbitfield mask = 0
        if self.clear_color:
            mask |= GL_COLOR_BUFFER_BIT
        if self.clear_stencil:
            mask |= GL_STENCIL_BUFFER_BIT
        if self.clear_depth:
            mask |= GL_DEPTH_BUFFER_BIT
        cgl.glClear(mask)
        return 0

    @property
    def clear_color(self):
        '''If True, the color buffer will be cleared.
        '''
        return self.clear_color

    @clear_color.setter
    def clear_color(self, value):
        value = int(value)
        if value == self.clear_color:
            return
        self.clear_color = value

    @property
    def clear_stencil(self):
        '''If True, the stencil buffer will be cleared.
        '''
        return self.clear_stencil

    @clear_stencil.setter
    def clear_stencil(self, value):
        value = int(value)
        if value == self.clear_stencil:
            return
        self.clear_stencil = value

    @property
    def clear_depth(self):
        '''If True, the depth buffer will be cleared.
        '''
        return self.clear_depth

    @clear_depth.setter
    def clear_depth(self, value):
        value = int(value)
        if value == self.clear_depth:
            return
        self.clear_depth = value
