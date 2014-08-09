include "config.pxi"
include "opcodes.pxi"

from kivy.graphics.c_opengl cimport *
IF USE_OPENGL_DEBUG == 1:
    from kivy.graphics.c_opengl_debug cimport *
from kivy.graphics.instructions cimport Instruction

cdef class Rect:
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


scissor_stack = ScissorStack()


cdef class ScissorPush(Instruction):
    cdef int _x
    cdef int _y
    cdef int _width
    cdef int _height
    cdef bint _on
    cdef Rect _rect

    property x:
        def __get__(self):
            return self._x
        def __set__(self, value):
            self._x = value
            self._rect = Rect(self._x, self._y, self._width, self._height)
            self.flag_update()

    property y:
        def __get__(self):
            return self._y
        def __set__(self, value):
            self._y = value
            self._rect = Rect(self._x, self._y, self._width, self._height)
            self.flag_update()

    property width:
        def __get__(self):
            return self._width
        def __set__(self, value):
            self._width = value
            self._rect = Rect(self._y, self._y, self._width, self._height)
            self.flag_update()

    property height:
        def __get__(self):
            return self._height
        def __set__(self, value):
            self._height = value
            self._rect = Rect(self._y, self._y, self._width, self._height)
            self.flag_update()

    property pos:
        def __get__(self):
            return self._x, self._y
        def __set__(self, value):
            self._x, self._y = value
            self._rect = Rect(self._x, self._y, self._width, self._height)
            self.flag_update()

    property size:
        def __get__(self):
            return self._width, self._height
        def __set__(self, value):
            self._width, self._height = value
            self._rect = Rect(self._x, self._y, self._width, self._height)
            self.flag_update()

    def __init__(self, **kwargs):
        super(ScissorPush, self).__init__(**kwargs)
        pos = kwargs.get('pos', (kwargs.get('x', 0), kwargs.get('y', 0)))
        self._x, self._y = kwargs.get(
            'pos', (
                kwargs.get('x', 0),
                kwargs.get('y', 0)
                )
            )
        self._width, self._height = kwargs.get(
            'size', (
                kwargs.get('width', 100),
                kwargs.get('height', 100)
                )
            )
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

    cdef void apply(self):
        scissor_stack.pop()
        cdef Rect new_scissor_rect
        if scissor_stack.empty:
            glDisable(GL_SCISSOR_TEST)
        else:
            new_scissor_rect = scissor_stack.back
            glScissor(new_scissor_rect._x, new_scissor_rect._y, 
                new_scissor_rect._width, new_scissor_rect._height)
