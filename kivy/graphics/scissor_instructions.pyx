'''
Scissor Instructions
====================

.. versionadded:: 1.9.1


Scissor instructions clip your drawing area into a rectangular region.

- :class:`ScissorPush`: Begins clipping, sets the bounds of the clip space
- :class:`ScissorPop`: Ends clipping

The area provided to clip is in screenspace pixels and must be provided as
integer values not floats.

The following code will draw a circle ontop of our widget while clipping
the circle so it does not expand beyond the widget borders.

.. code-block:: python

    with self.canvas.after:
        #If our widget is inside another widget that modified the coordinates
        #spacing (such as ScrollView) we will want to convert to Window coords
        x,y = self.to_window(*self.pos)
        width, height = self.size
        #We must convert from the possible float values provided by kivy
        #widgets to an integer screenspace, in python3 round returns an int so
        #the int cast will be unnecessary.
        ScissorPush(x=int(round(x)), y=int(round(y)),
            width=int(round(width)), height=int(round(height)))
        Color(rgba=(1., 0., 0., .5))
        Ellipse(size=(width*2., height*2.),
            pos=self.center)
        ScissorPop()
'''
include "../include/config.pxi"
include "opcodes.pxi"

from kivy.graphics.cgl cimport *
from kivy.graphics.instructions cimport Instruction

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


scissor_stack = ScissorStack()


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
            self._rect = Rect(self._x, self._y, self._width, self._height)
            self.flag_update()

    property height:
        def __get__(self):
            return self._height
        def __set__(self, value):
            self._height = value
            self._rect = Rect(self._x, self._y, self._width, self._height)
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
        self._x, self._y = kwargs.pop(
            'pos', (
                kwargs.pop('x', 0),
                kwargs.pop('y', 0)
                )
            )
        self._width, self._height = kwargs.pop(
            'size', (
                kwargs.pop('width', 100),
                kwargs.pop('height', 100)
                )
            )
        super(ScissorPush, self).__init__(**kwargs)
        self._rect = Rect(self._x, self._y, self._width, self._height)

    cdef int apply(self) except -1:
        cdef Rect rect = self._rect
        cdef Rect new_scissor_rect
        cdef Rect back
        if scissor_stack.empty:
            scissor_stack.push(rect)
            cgl.glEnable(GL_SCISSOR_TEST)
            cgl.glScissor(self._x, self._y, self._width, self._height)
        else:
            new_scissor_rect = Rect(rect._x, rect._y,
                rect._width, rect._height)
            back = scissor_stack.back
            new_scissor_rect.intersect(back)
            scissor_stack.push(new_scissor_rect)
            cgl.glScissor(new_scissor_rect._x, new_scissor_rect._y,
                new_scissor_rect._width, new_scissor_rect._height)

cdef class ScissorPop(Instruction):
    '''Pop the scissor stack. Call after ScissorPush, once you have completed
    the drawing you wish to be clipped.
    '''

    cdef int apply(self) except -1:
        scissor_stack.pop()
        cdef Rect new_scissor_rect
        if scissor_stack.empty:
            cgl.glDisable(GL_SCISSOR_TEST)
        else:
            new_scissor_rect = scissor_stack.back
            cgl.glScissor(new_scissor_rect._x, new_scissor_rect._y,
                new_scissor_rect._width, new_scissor_rect._height)
