from instructions cimport *

cdef class Canvas(InstructionGroup):
    cpdef draw(self):
        self.apply()

    def __enter__(self):
        pushActiveCanvas(self)

    def __exit__(self):
        popActiveCanvas()


# Active Canvas and getActiveCanvas function is used
# by instructions, so they know which canvas to add
# tehmselves to
cdef Canvas ACTIVE_CANVAS = None

cdef Canvas getActiveCanvas():
    global ACTIVE_CANVAS
    return ACTIVE_CANVAS


# Canvas Stack, for internal use so canvas can be bound 
# inside other canvas, and restroed when other canvas is done
cdef list CANVAS_STACK = list()

cdef pushActiveCanvas(Canvas c):
    global ACTIVE_CANVAS, CANVAS_STACK
    CANVAS_STACK.append(ACTIVE_CANVAS)
    ACTIVE_CANVAS = c

cdef popActiveCanvas():
    global ACTIVE_CANVAS, CANVAS_STACK
    ACTIVE_CANVAS = CANVAS_STACK.pop()

