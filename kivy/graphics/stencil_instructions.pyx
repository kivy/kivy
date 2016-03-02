'''
Stencil instructions
====================

.. versionadded:: 1.0.4

.. versionchanged:: 1.3.0
    The stencil operation has been updated to resolve some issues that appeared
    when nested. You **must** now have a StencilUnUse and repeat the same
    operation as you did after StencilPush.

Stencil instructions permit you to draw and use the current drawing as a mask.
They don't give as much control as pure OpenGL, but you can still do fancy
things!

The stencil buffer can be controlled using these 3 instructions:

    - :class:`StencilPush`: push a new stencil layer.
      Any drawing that happens after this will be used as a mask.
    - :class:`StencilUse` : now draw the next instructions and use the stencil
      for masking them.
    - :class:`StencilUnUse` : stop using the stencil i.e. remove the mask and
      draw normally.
    - :class:`StencilPop` : pop the current stencil layer.


You should always respect this scheme:

.. code-block:: kv

    StencilPush

    # PHASE 1: put any drawing instructions to use as a mask here.

    StencilUse

    # PHASE 2: all the drawing here will be automatically clipped by the
    # mask created in PHASE 1.

    StencilUnUse

    # PHASE 3: drawing instructions wil now be drawn without clipping but the
    # mask will still be on the stack. You can return to PHASE 2 at any
    # time by issuing another *StencilUse* command.

    StencilPop

    # PHASE 4: the stencil is now removed from the stack and unloaded.


Limitations
-----------

- Drawing in PHASE 1 and PHASE 3 must not collide or you
  will get unexpected results
- The stencil is activated as soon as you perform a StencilPush
- The stencil is deactivated as soon as you've correctly popped all the stencil
  layers
- You must not play with stencils yourself between a StencilPush / StencilPop
- You can push another stencil after a StencilUse / before the StencilPop
- You can push up to 128 layers of stencils (8 for kivy < 1.3.0)


Example of stencil usage
------------------------

Here is an example, in kv style::

    StencilPush

    # create a rectangular mask with a pos of (100, 100) and a (100, 100) size.
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

    StencilUnUse

    # you must redraw the stencil mask to remove it
    Rectangle:
        pos: 100, 100
        size: 100, 100

    StencilPop

'''

__all__ = ('StencilPush', 'StencilPop', 'StencilUse', 'StencilUnUse')

include "config.pxi"
include "opcodes.pxi"
include "gl_debug_logger.pxi"

from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_MOCK == 1:
    from kivy.graphics.c_opengl_mock cimport *
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
    '''Push the stencil stack. See the module documentation for more
    information.
    '''
    cdef int apply(self) except -1:
        global _stencil_level, _stencil_in_push
        if _stencil_in_push:
            raise Exception('Cannot use StencilPush inside another '
                            'StencilPush.\nUse StencilUse before.')
        _stencil_in_push = 1
        _stencil_level += 1

        if _stencil_level == 1:
            glStencilMask(0xff)
            log_gl_error('StencilPush.apply-glStencilMask')
            glClearStencil(0)
            log_gl_error('StencilPush.apply-glClearStencil')
            glClear(GL_STENCIL_BUFFER_BIT)
            log_gl_error('StencilPush.apply-glClear(GL_STENCIL_BUFFER_BIT)')
        if _stencil_level > 128:
            raise Exception('Cannot push more than 128 level of stencil.'
                            ' (stack overflow)')

        glEnable(GL_STENCIL_TEST)
        log_gl_error('StencilPush.apply-glEnable(GL_STENCIL_TEST)')
        glStencilFunc(GL_ALWAYS, 0, 0)
        log_gl_error('StencilPush.apply-glStencilFunc')
        glStencilOp(GL_INCR, GL_INCR, GL_INCR)
        log_gl_error('StencilPush.apply-glStencilOp')
        glColorMask(0, 0, 0, 0)
        log_gl_error('StencilPush.apply-glColorMask')
        return 0

cdef class StencilPop(Instruction):
    '''Pop the stencil stack. See the module documentation for more information.
    '''
    cdef int apply(self) except -1:
        global _stencil_level, _stencil_in_push
        if _stencil_level == 0:
            raise Exception('Too much StencilPop (stack underflow)')
        _stencil_level -= 1
        _stencil_in_push = 0
        glColorMask(1, 1, 1, 1)
        log_gl_error('StencilPop.apply-glColorMask')
        if _stencil_level == 0:
            glDisable(GL_STENCIL_TEST)
            log_gl_error('StencilPop.apply-glDisable')
            return 0
        # reset for previous
        glStencilFunc(GL_EQUAL, _stencil_level, 0xff)
        log_gl_error('StencilPop.apply-glStencilFunc')
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        log_gl_error('StencilPop.apply-glStencilOp')
        return 0


cdef class StencilUse(Instruction):
    '''Use current stencil buffer as a mask. Check the module documentation for
    more information.
    '''
    def __init__(self, **kwargs):
        super(StencilUse, self).__init__(**kwargs)
        if 'op' in kwargs:
            self._op = _stencil_op_to_gl(kwargs['op'])
        else:
            self._op = GL_EQUAL

    cdef int apply(self) except -1:
        global _stencil_in_push
        _stencil_in_push = 0
        glColorMask(1, 1, 1, 1)
        log_gl_error('StencilUse.apply-glColorMask')
        glStencilFunc(self._op, _stencil_level, 0xff)
        log_gl_error('StencilUse.apply-glStencilFunc')
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        log_gl_error('StencilUse.apply-glStencilOp')
        return 0

    property func_op:
        '''Determine the stencil operation to use for glStencilFunc(). Can be
        one of 'never', 'less', 'equal', 'lequal', 'greater', 'notequal',
        'gequal' or 'always'.

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
    cdef int apply(self) except -1:
        glStencilFunc(GL_ALWAYS, 0, 0)
        log_gl_error('StencilUnUse.apply-glStencilFunc')
        glStencilOp(GL_DECR, GL_DECR, GL_DECR)
        log_gl_error('StencilUnUse.apply-glStencilOp')
        glColorMask(0, 0, 0, 0)
        log_gl_error('StencilUnUse.apply-glColorMask')
        return 0
