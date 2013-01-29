'''
Stencil instructions
====================

.. versionadded:: 1.0.4

.. versionchanged:: 1.3.0
    The stencil operation have been updated to resolve some issues appearing
    when nested. You **must** know have a StencilUnUse and repeat the same
    operation as you did after StencilPush.

Stencil instructions permit you to draw and use the current drawing as a mask.
Even if you don't have as much control as OpenGL, you can still do fancy things
:=)

The stencil buffer can be controled with theses 3 instructions :

    - :class:`StencilPush`: push a new stencil layer
      any drawing that happening here will be used as a mask
    - :class:`StencilUse` : now draw the next instructions and use the stencil
      for masking them
    - :class:`StencilUnUse` : stop drawing, and use the stencil to remove the
      mask
    - :class:`StencilPop` : pop the current stencil layer.


Here is a global scheme to respect::

.. code-block:: kv

    StencilPush

    # PHASE 1: put here any drawing instruction to use as a mask

    StencilUse

    # PHASE 2: all the drawing here will be automatically clipped by the previous mask

    StencilUnUse

    # PHASE 3: put here the same drawing instruction as you did in PHASE 1

    StencilPop



Limitations
-----------

- Drawing in PHASE 1 and PHASE 3 must not collide between each others, or you
  will get unexpected result.
- The stencil is activated as soon as you're doing a StencilPush
- The stencil is deactivated as soon as you've correctly pop all the stencils
  layers
- You must not play with stencil yourself between a StencilPush / StencilPop
- You can push again the stencil after a StencilUse / before the StencilPop
- You can push up to 128 layers of stencils. (8 for kivy < 1.3.0)


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

    StencilUnUse:
        # new in kivy 1.3.0, remove the mask previoulsy added
        Rectangle:
            pos: 100, 100
            size: 100, 100

    StencilPop

'''

__all__ = ('StencilPush', 'StencilPop', 'StencilUse', 'StencilUnUse')

include "config.pxi"
include "opcodes.pxi"

from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.graphics.instructions cimport Instruction

cdef int _stencil_level = 0
cdef int _stencil_in_push = 0


cdef dict _gl_stencil_op = {
    'never': GL_NEVER, 'less': GL_LESS, 'equal': GL_EQUAL,
    'lequal': GL_LEQUAL, 'greater': GL_GREATER, 'notequal': GL_NOTEQUAL,
    'gequal': GL_GEQUAL, 'always': GL_ALWAYS }


cdef inline int _stencil_op_to_gl(x):
    '''Return the GL numeric value from a stencil operator
    '''
    x = x.lower()
    try:
        return _gl_stencil_op[x]
    except KeyError:
        raise Exception('Unknow <%s> stencil op' % x)


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

        if _stencil_level == 1:
            glStencilMask(0xff)
            glClearStencil(0)
            glClear(GL_STENCIL_BUFFER_BIT)
        if _stencil_level > 128:
            raise Exception('Cannot push more than 8 level of stencil.'
                            ' (stack overflow)')

        glEnable(GL_STENCIL_TEST)
        glStencilFunc(GL_ALWAYS, 0, 0)
        glStencilOp(GL_INCR, GL_INCR, GL_INCR)
        glColorMask(0, 0, 0, 0)

cdef class StencilPop(Instruction):
    '''Pop the stencil stack. See module documentation for more information.
    '''
    cdef void apply(self):
        global _stencil_level, _stencil_in_push
        if _stencil_level == 0:
            raise Exception('Too much StencilPop (stack underflow)')
        _stencil_level -= 1
        _stencil_in_push = 0
        glColorMask(1, 1, 1, 1)
        if _stencil_level == 0:
            glDisable(GL_STENCIL_TEST)
            return
        # reset for previous
        glStencilFunc(GL_EQUAL, _stencil_level, 0xff)
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)


cdef class StencilUse(Instruction):
    '''Use current stencil buffer as a mask. Check module documentation for more
    information.
    '''
    def __init__(self, **kwargs):
        super(StencilUse, self).__init__(**kwargs)
        if 'op' in kwargs:
            self._op = _stencil_op_to_gl(kwargs['op'])
        else:
            self._op = GL_EQUAL

    cdef void apply(self):
        global _stencil_in_push
        _stencil_in_push = 0
        glColorMask(1, 1, 1, 1)
        glStencilFunc(self._op, _stencil_level, 0xff)
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)

    property func_op:
        '''Determine the stencil operation to use for glStencilFunc(). Can be
        one of 'never', 'less', 'equal', 'lequal', 'greater', 'notequal',
        'gequal', 'always'.

        By default, the operator is set to 'equal'.

        .. versionadded:: 1.5.0
        '''

        def __get__(self):
            index = _gl_stencil_op.values().index(self._op)
            return _gl_stencil_op.keys()[index]

        def __set__(self, x):
            cdef int op = _stencil_op_to_gl(x)
            if op != self._op:
                self._op = op
                self.flag_update()


cdef class StencilUnUse(Instruction):
    '''Use current stencil buffer to unset the mask.
    '''
    cdef void apply(self):
        glStencilFunc(GL_ALWAYS, 0, 0)
        glStencilOp(GL_DECR, GL_DECR, GL_DECR)
        glColorMask(0, 0, 0, 0)
