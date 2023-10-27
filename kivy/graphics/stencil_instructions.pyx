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

    # PHASE 3: put the same drawing instruction here as you did in PHASE 1

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

include "../include/config.pxi"
include "opcodes.pxi"
include "gl_debug_logger.pxi"

from kivy.graphics.cgl cimport *
from kivy.compat import PY2
from kivy.graphics.instructions cimport Instruction

cdef dict DEFAULT_STATE = {
    "level": 0,
    "in_push": False,
    "op": None,
    "gl_stencil_func": None,
    "clear_stencil": True
}

cdef dict _stencil_state = DEFAULT_STATE.copy()

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
        raise Exception('Unknown <%s> stencil op' % x)


cdef get_stencil_state():
    global _stencil_state
    return _stencil_state.copy()


cdef void restore_stencil_state(dict state):
    global _stencil_state
    _stencil_state = state.copy()
    stencil_apply_state(_stencil_state, True)


cdef void reset_stencil_state():
    restore_stencil_state(DEFAULT_STATE)


cdef void stencil_apply_state(dict state, restore_only):
    # apply state for stencil here. This allow to reapply a state
    # easily when using FBO, or linking to other GL subprogram
    if state["op"] is None:
        cgl.glDisable(GL_STENCIL_TEST)

    elif state["op"] == "push":
        # Push the stencil stack, ready to draw a mask

        if not restore_only:
            state["level"] += 1
            state["in_push"] = True

        if state["level"] == 1:
            cgl.glStencilMask(0xff)
            log_gl_error('StencilPush.apply-glStencilMask')
            if state["clear_stencil"]:
                cgl.glClearStencil(0)
                log_gl_error('StencilPush.apply-glClearStencil')
                cgl.glClear(GL_STENCIL_BUFFER_BIT)
                log_gl_error('StencilPush.apply-glClear(GL_STENCIL_BUFFER_BIT)')
        elif state["level"] > 128:
            raise Exception('Cannot push more than 128 level of stencil.'
                            ' (stack overflow)')

        cgl.glEnable(GL_STENCIL_TEST)
        log_gl_error('StencilPush.apply-glEnable(GL_STENCIL_TEST)')
        cgl.glStencilFunc(GL_ALWAYS, 1, 0xff)
        log_gl_error('StencilPush.apply-glStencilFunc')
        cgl.glStencilOp(GL_INCR, GL_INCR, GL_INCR)
        log_gl_error('StencilPush.apply-glStencilOp')
        cgl.glColorMask(False, False, False, False)
        log_gl_error('StencilPush.apply-glColorMask')


    elif state["op"] == "pop":
        # Pop the stencil stack

        if not restore_only:
            if state["level"] == 0:
                raise Exception('Too much StencilPop (stack underflow)')
            state["level"] -= 1
            state["in_push"] = False

        cgl.glColorMask(True, True, True, True)
        log_gl_error('StencilPop.apply-glColorMask')
        if state["level"] == 0:
            cgl.glDisable(GL_STENCIL_TEST)
            log_gl_error('StencilPop.apply-glDisable')
            return
        # reset for previous
        cgl.glStencilFunc(GL_EQUAL, state["level"], 0xff)
        log_gl_error('StencilPop.apply-glStencilFunc')
        cgl.glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        log_gl_error('StencilPop.apply-glStencilOp')


    elif state["op"] == "use":
        # Use the current stencil buffer to cut the drawing
        if not restore_only:
            state["in_push"] = False
        cgl.glColorMask(True, True, True, True)
        log_gl_error('StencilUse.apply-glColorMask')
        cgl.glStencilFunc(state["gl_stencil_func"], state["level"], 0xff)
        log_gl_error('StencilUse.apply-glStencilFunc')
        cgl.glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        cgl.glEnable(GL_STENCIL_TEST)
        log_gl_error('StencilUse.apply-glStencilOp')

    elif state["op"] == "unuse":
        # Ready to undraw the mask
        cgl.glStencilFunc(GL_GREATER, 0xff, 0xff)
        log_gl_error('StencilUnUse.apply-glStencilFunc')
        cgl.glStencilOp(GL_DECR, GL_DECR, GL_DECR)
        log_gl_error('StencilUnUse.apply-glStencilOp')
        cgl.glColorMask(False, False, False, False)
        log_gl_error('StencilUnUse.apply-glColorMask')


cdef class StencilPush(Instruction):
    '''Push the stencil stack. See the module documentation for more
    information.

    '''

    def __init__(self, **kwargs):
        super(StencilPush, self).__init__(**kwargs)
        self._clear_stencil = self._check_bool(kwargs.get('clear_stencil', True))

    cdef bint _check_bool(self, object value):
        if not isinstance(value, bool):
            raise TypeError(
                f"'clear_stencil' accept only boolean values (True or False), got {type(value)}."
            )
        return value

    cdef int apply(self) except -1:
        _stencil_state["op"] = "push"
        _stencil_state["clear_stencil"] = self._clear_stencil
        stencil_apply_state(_stencil_state, False)
        return 0

    @property
    def clear_stencil(self):
        '''``clear_stencil`` allow to disable stencil clearing in the ``StencilPush``
        phase. This option essentially disables the invocation of the functions
        ``cgl.glClearStencil(0)`` and ``cgl.glClear(GL_STENCIL_BUFFER_BIT).``

        If ``True``, the stencil will be cleaned in the ``StencilPush`` phase, if
        ``False``, it will not be cleaned.

        .. note::
            It is **highly recommended** to set ``clear_stencil=False`` for improved
            performance and reduced GPU usage (especially if there are hundreds of
            instructions). However, if any side effects (such as artifacts or inaccurate
            behavior of ``StencilPush``) occur, it is advisable to re-enable the clearing
            instructions with ``clear_stencil=True.``

        .. versionadded:: 2.3.0
        '''
        return self._clear_stencil

    @clear_stencil.setter
    def clear_stencil(self, value):
        cdef int clear_stencil = self._check_bool(value)
        if clear_stencil != self._clear_stencil:
            self._clear_stencil = clear_stencil
            self.flag_data_update()


cdef class StencilPop(Instruction):
    '''Pop the stencil stack. See the module documentation for more information.
    '''
    cdef int apply(self) except -1:
        _stencil_state["op"] = "pop"
        stencil_apply_state(_stencil_state, False)
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
        _stencil_state["gl_stencil_func"] = self._op
        _stencil_state["op"] = "use"
        stencil_apply_state(_stencil_state, False)
        return 0

    @property
    def func_op(self):
        '''Determine the stencil operation to use for glStencilFunc(). Can be
        one of 'never', 'less', 'equal', 'lequal', 'greater', 'notequal',
        'gequal' or 'always'.

        By default, the operator is set to 'equal'.

        .. versionadded:: 1.5.0
        '''

        index = _gl_stencil_op.values().index(self._op)
        if PY2:
            return _gl_stencil_op.keys()[index]
        else:
            return list(_gl_stencil_op.keys())[index]

    @func_op.setter
    def func_op(self, x):
        cdef int op = _stencil_op_to_gl(x)
        if op != self._op:
            self._op = op
            self.flag_data_update()


cdef class StencilUnUse(Instruction):
    '''Use current stencil buffer to unset the mask.
    '''
    cdef int apply(self) except -1:
        _stencil_state["op"] = "unuse"
        stencil_apply_state(_stencil_state, False)
        return 0
