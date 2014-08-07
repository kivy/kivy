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

    StencilUnUse:
        # new in kivy 1.3.0, remove the mask previously added
        Rectangle:
            pos: 100, 100
            size: 100, 100

    StencilPop

'''

__all__ = ('StencilPush', 'StencilPop', 'StencilUse', 'StencilUnUse', 'ScissorPush', 'ScissorPop')

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

cdef class Rect:
    '''Rect class used internally by ScissorStack and ScissorPush to determine
    correct clipping area.
    '''
    cdef int _x
    cdef int _y
    cdef int _width
    cdef int _height

    def __init__(self, int x, int y, int width, int height):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def intersect(self, Rect other):
        max_x = min(self._x + self._width, other._x + other._width)
        x = max(self._x, other._x)
        width = max(0, max_x - x)
        max_y = min(self._y + self._height, other._y + other._height)
        y = max(self._y, other._y)
        height = max(0, max_y - y)
        self._x = x
        self._width = width
        self._y = y
        self._height = height


cdef class ScissorStack:
    '''Class used internally to keep track of the current state of 
    glScissors regions. Do not instantiate, prefer to inspect the module's
    scissor_stack.
    '''
    cdef list _stack

    def __init__(self):
        self._stack = []

    property empty:
        def __get__(self):
            return True if len(self._stack) is 0 else False

    property back:
        def __get__(self):
            return self._stack[-1]

    def push(self, element):
        self._stack.append(element)

    def pop(self):
        return self._stack.pop()


cdef ScissorStack scissor_stack = ScissorStack()


cdef class ScissorPush(Instruction):
    '''Push the scissor stack. Provide kwargs of 'x', 'y', 'width', 'height' 
    to control the area and position of the scissoring region. Defaults to 
    0, 0, 100, 100

    Scissor works by clipping all drawing outside of a rectangle starting at
    int x, int y position and having sides of int width by int height in Window
    space coordinates
    '''
    cdef int _x
    cdef int _y
    cdef int _width
    cdef int _height
    cdef Rect _rect

    def __init__(self, **kwargs):
        super(ScissorPush, self).__init__(**kwargs)
        if 'x' in kwargs:
            self._x = kwargs['x']
        else:
            self._x = 0
        if 'y' in kwargs:
            self._y = kwargs['y']
        else:
            self._y = 0
        if 'width' in kwargs:
            self._width = kwargs['width']
        else:
            self._width = 100
        if 'height' in kwargs:
            self._height = kwargs['height']
        else:
            self._height = 100
        self._rect = Rect(self._x, self._y, self._width, self._height)

    cdef void apply(self):
        cdef Rect rect = self._rect
        cdef Rect new_scissor_rect
        cdef Rect back
        if scissor_stack.empty:
            scissor_stack.push(rect)
            glEnable(GL_SCISSOR_TEST)
            glScissor(self._x, self._y, self._width, self._height)
        else:
            new_scissor_rect = Rect(rect._x, rect._y, 
                rect._width, rect._height)
            back = scissor_stack.back
            new_scissor_rect.intersect(back)
            scissor_stack.push(new_scissor_rect)
            glScissor(new_scissor_rect._x, new_scissor_rect._y, 
                new_scissor_rect._width, new_scissor_rect._height)

cdef class ScissorPop(Instruction):
    '''Pop the scissor stack. Call after ScissorPush, once you have completed
    the drawing you wish to be clipped.
    '''

    cdef void apply(self):
        scissor_stack.pop()
        cdef Rect new_scissor_rect
        if scissor_stack.empty:
            glDisable(GL_SCISSOR_TEST)
        else:
            new_scissor_rect = scissor_stack.back
            glScissor(new_scissor_rect._x, new_scissor_rect._y, 
                new_scissor_rect._width, new_scissor_rect._height)


cdef class StencilPush(Instruction):
    '''Push the stencil stack. See the module documentation for more
    information.
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
            raise Exception('Cannot push more than 128 level of stencil.'
                            ' (stack overflow)')

        glEnable(GL_STENCIL_TEST)
        glStencilFunc(GL_ALWAYS, 0, 0)
        glStencilOp(GL_INCR, GL_INCR, GL_INCR)
        glColorMask(0, 0, 0, 0)

cdef class StencilPop(Instruction):
    '''Pop the stencil stack. See the module documentation for more information.
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
    '''Use current stencil buffer as a mask. Check the module documentation for
    more information.
    '''
    def __init__(self, **kwargs):
        super(StencilUse, self).__init__(**kwargs)
        if 'op' in kwargs:
            self._op = _stencil_op_to_gl(kwargs['op'])
        elif 'func_op' in kwargs:
            self._op = _stencil_op_to_gl(kwargs['func_op'])
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
    cdef void apply(self):
        glStencilFunc(GL_ALWAYS, 0, 0)
        glStencilOp(GL_DECR, GL_DECR, GL_DECR)
        glColorMask(0, 0, 0, 0)
