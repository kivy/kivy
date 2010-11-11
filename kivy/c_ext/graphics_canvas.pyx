__all__ = ('Canvas', )

include "graphics_common.pxi"

from kivy.logger import Logger
from graphics_instruction cimport ContextInstruction
from graphics_instr_base cimport CanvasDraw

cdef Canvas _active_canvas = None
cdef int _active_canvas_after = 0

def Canvas_active_instance():
    return _active_canvas

cdef class CanvasAfter:
    def __init__(self, canvas):
        self.canvas = canvas

    def __enter__(self):
        self.canvas.__enter__(after=1)

    def __exit__(self, extype, value, traceback):
        self.canvas.__exit__(extype, value, traceback, after=1)

cdef class Canvas:

    active = Canvas_active_instance

    def __cinit__(self):
        self._context = GraphicContext.instance()
        self._canvas_after = CanvasAfter(self)
        self.vertex_buffer = VBO()
        self.texture_map = []
        self._batch = []
        self._batch_after = []
        self._children = []

        self._need_compile = 1
        self.batch_slices = []
        self.num_slices = 0

    property need_compile:
        def __set__(self, int i):
            if i:
                self.context.post_update()
            self._need_compile = i
        def __get__(self):
            return self._need_compile

    property context:
        def __get__(self):
            return self._context

    property batch:
        def __get__(self):
            return self._batch

    property after:
        def __get__(self):
            return self._canvas_after

    cpdef trigger(self):
        self._context.trigger()

    def __enter__(self, after=0):
        global _active_canvas, _active_canvas_after
        if _active_canvas:
            raise Exception('Cannot stack canvas usage.')
        _active_canvas = self
        _active_canvas_after = after

    def __exit__(self, extype, value, traceback, after=0):
        global _active_canvas, _active_canvas_after
        _active_canvas = None
        _active_canvas_after = after

    cpdef add_canvas(self, Canvas canvas):
        if not canvas in self._children:
            self._children.append(canvas)
        self._need_compile = 1

    cpdef remove_canvas(self, Canvas canvas):
        if canvas in self._children:
            self._children.remove(canvas)
        self._need_compile = 1

    cdef add(self, GraphicInstruction instruction):
        self.need_compile = 1
        if _active_canvas_after:
            self._batch_after.append(instruction)
        else:
            self._batch.append(instruction)

    cdef remove(self, GraphicInstruction instruction):
        self.need_compile = 1
        if _active_canvas_after:
            self._batch_after.remove(instruction)
        else:
            self._batch.remove(instruction)

    cdef update(self, instruction):
        ''' called by graphic instructions taht are part of the canvas,
            when they have been changed in some way '''
        self.need_compile = 1

    cdef compile_init(self):
        self.texture_map = []
        self.batch_slices = []

        # to prevent to regenerate object from previous compilation
        # remove all the object flagged as GI_COMPILER
        self._batch = self.compile_strip_compiler(self._batch)
        self._batch_after = self.compile_strip_compiler(self._batch_after)

    cdef list compile_strip_compiler(self, list batch):
        cdef GraphicInstruction x
        return [x for x in batch if not (x.code & GI_COMPILER)]

    cdef compile(self):
        Logger.trace('GCanvas: start compilation')

        self.compile_init()
        with self:
            self.compile_batch(self._batch)
            self.compile_children()
        with self.after:
            self.compile_batch(self._batch_after)

    cdef compile_batch(self, list batch):
        cdef GraphicInstruction item
        cdef int slice_start = -1
        cdef int slice_stop  = -1
        cdef int i, code, batch_len

        # care about the batch. since we adding instruction, the size can change
        # while we are iterating.
        batch_len = len(batch)

        # always start with binding vbo
        if batch_len:
            self.batch_slices.append(('bind', None))

        for i in xrange(batch_len):
            item = batch[i]
            code = item.code
            # the instruction modifies the context, so we cant combine the drawing
            # calls before and after it
            if code & GI_CONTEXT_MOD:
                #first compile the slices we been loopiing over which we can combine
                #from slice_start to slice_stop. (using compile_slice() )
                #add the context modifying instruction to batch_slices
                #reset slice start/stop index
                self.compile_slice('draw', batch, slice_start, slice_stop)
                self.batch_slices.append(('instruction', item))
                slice_start = slice_stop = -1

            # the instruction pushes vertices to the pipeline and doesnt modify
            # the context, so we can happily combine it with any prior or follwing
            # instructions that do the same, just keep incrementing slice stop index
            # until we cant combine any more, then well call compile_slice()
            elif code & GI_VERTEX_DATA:
                slice_stop = i
                if slice_start == -1:
                    slice_start = i

        # maybe we ended on an slice of vartex data, whcih we didnt push yet
        self.compile_slice('draw', batch, slice_start, slice_stop)

    cdef compile_children(self):
        cdef Canvas child
        cdef GraphicInstruction instr
        for child in self._children:
            instr = CanvasDraw(child)
            instr.code |= GI_COMPILER
            self.batch_slices.append(('instruction', instr))

    cdef compile_slice(self, str command, list batch, slice_start, slice_end):
        Logger.trace('Canvas: compiling slice: %s' % str((
                     slice_start, slice_end, command)))
        cdef GraphicInstruction item
        cdef VertexDataInstruction vdi
        cdef Buffer b = Buffer(sizeof(GLint))
        cdef int v, i
        cdef GraphicInstruction instr

        # check if we have a valid slice
        if slice_start == -1:
            return

        # loop over all the whole slice, and combine all instructions
        for item in batch[slice_start:slice_end+1]:
            if isinstance(item, VertexDataInstruction):
                vdi = item
                # add the vertex indices to be drawn from this item
                for i in range(vdi.num_elements):
                    v = vdi.element_data[i]
                    b.add(&v, NULL, 1)

            # handle textures (should go somewhere else?,
            # maybe set GI_CONTEXT_MOD FLAG ALSO?)
            if item.texture:
                instr = BindTexture(item.texture)
            else:
                instr = BindTexture(None)

            # flags the instruction as a generated one
            instr.code |= GI_COMPILER
            self.batch_slices.append(('instruction', instr))
            self.batch_slices.append((command, b))
            b = Buffer(sizeof(GLint))

        # last slice, all done, only have to add if there is actually somethign in it
        if b.count() > 0:
            self.batch_slices.append((command, b))

    cpdef draw(self):
        # early binding to prevent some python overhead
        self._draw()

    cdef _draw(self):
        cdef int i
        cdef Buffer b
        cdef ContextInstruction ci

        if self.need_compile:
            self.compile()
            self.need_compile = 0

        for command, item in self.batch_slices:
            if command == 'bind':
                self.vertex_buffer.bind()
                attr = VERTEX_ATTRIBUTES[0]
                glBindBuffer(GL_ARRAY_BUFFER, self.vertex_buffer.id)
            elif command == 'instruction':
                ci = item
                ci.apply()
            elif command == 'draw':
                b = item
                self.context.flush()
                glDrawElements(GL_TRIANGLES, b.count(), GL_UNSIGNED_INT, b.pointer())

        self.context.finish_frame()

