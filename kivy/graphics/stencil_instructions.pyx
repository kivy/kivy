'''
Stencil instructions
====================

.. versionadded:: 1.0.4

Stencil instructions permit you to draw and use the current drawing as a mask.
Even if you don't have as much control as OpenGL, you can still do fancy things
:=)

The stencil buffer can be controled with theses 3 instructions :

    - :class:`StencilPush`
    - :class:`StencilUse`
    - :class:`StencilPop`

Here is a global scheme to respect :

    - :class:`StencilPush` : push a new stencil layer
    - any drawing that happening here will be used as a mask
    - :class:`StencilUse` : now draw the next instructions and use the stencil
      for masking them
    - :class:`StencilPop` : pop the current stencil layer.

Limitations
-----------

- The stencil is activated as soon as you're doing a StencilPush
- The stencil is deactivated as soon as you've correctly pop all the stencils
  layers
- You must not play with stencil yourself between a StencilPush / StencilPop
- You can push again the stencil after a StencilUse / before the StencilPop
- You can push up to 8 layers of stencils.


Example of stencil usage
------------------------

Here is an example, in kv style::

    StencilPush

    # create a rectangle mask, from pos 100, 100, with a 100, 100 size.
    Rectangle:
        pos: 100, 100
        size: 100, 100

    StencilUse

    # we want to show a big green rectangle, however, the previous stencil
    # mask will crop us :)
    Color:
        rgb: 0, 1, 0
    Rectangle:
        size: 900, 900

    StencilPop

'''

__all__ = ('StencilPush', 'StencilPop', 'StencilUse')

include "config.pxi"
include "opcodes.pxi"

from c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from c_opengl_debug cimport *
from instructions cimport Instruction
from kivy.utils import platform

cdef int _stencil_level = -1
cdef int _stencil_in_push = 0
cdef int _stencil_table[8]
_stencil_table[:] = [1, 3, 7, 15, 31, 63, 127, 255]

cdef class StencilPush(Instruction):
    '''Push the stencil stack. See module documentation for more information.
    '''
    cdef void apply(self):
        global _stencil_level, _stencil_in_push
        if _stencil_in_push:
            raise Exception('Cannot use StencilPush inside another '
                            'StencilPush.\nUse StencilUse before.')
        _stencil_in_push = 1
        _stencil_level += 1

        if _stencil_level == 0:
            glClearStencil(0)
            glClear(GL_STENCIL_BUFFER_BIT)
        if _stencil_level > 8:
            raise Exception('Cannot push more than 8 level of stencil.'
                            ' (stack overflow)')

        glEnable(GL_STENCIL_TEST)

        glStencilMask(1 << _stencil_level)
        glStencilFunc(GL_NEVER, 1 << _stencil_level, 1 << _stencil_level)
        glStencilOp(GL_REPLACE, GL_REPLACE, GL_REPLACE)
        if platform() != 'android':
            glColorMask(0, 0, 0, 0)

cdef class StencilPop(Instruction):
    '''Pop the stencil stack. See module documentation for more information.
    '''
    cdef void apply(self):
        global _stencil_level, _stencil_in_push
        if _stencil_level == -1:
            raise Exception('Too much StencilPop (stack underflow)')
        _stencil_level -= 1
        _stencil_in_push = 0
        if _stencil_level == -1:
            glDisable(GL_STENCIL_TEST)
            glColorMask(1, 1, 1, 1)
            return
        # reset for previous
        glColorMask(1, 1, 1, 1)
        cdef int mask = _stencil_table[_stencil_level]
        glStencilFunc(GL_EQUAL, mask, mask)
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)


cdef class StencilUse(Instruction):
    '''Use current stencil buffer as a mask. Check module documentation for more
    information.
    '''
    cdef void apply(self):
        global _stencil_in_push
        _stencil_in_push = 0
        cdef int mask = _stencil_table[_stencil_level]
        glColorMask(1, 1, 1, 1)
        glStencilFunc(GL_EQUAL, mask, mask)
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)

