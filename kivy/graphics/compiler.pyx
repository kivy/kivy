'''
Graphics compiler
=================

Before rendering an :class:`~kivy.graphics.instructions.InstructionGroup`, we
are compiling the group, in order to reduce the number of instructions executed
at rendering time.

Reducing the context instructions
---------------------------------

Imagine that you have a scheme like this ::

    Color(1, 1, 1)
    Rectangle(source='button.png', pos=(0, 0), size=(20, 20))
    Color(1, 1, 1)
    Rectangle(source='button.png', pos=(10, 10), size=(20, 20))
    Color(1, 1, 1)
    Rectangle(source='button.png', pos=(10, 20), size=(20, 20))

The real instruction seen by the graphics canvas would be ::

    Color: change 'color' context to 1, 1, 1
    BindTexture: change 'texture0' to `button.png texture`
    Rectangle: push vertices (x1, y1...) to vbo & draw
    Color: change 'color' context to 1, 1, 1
    BindTexture: change 'texture0' to `button.png texture`
    Rectangle: push vertices (x1, y1...) to vbo & draw
    Color: change 'color' context to 1, 1, 1
    BindTexture: change 'texture0' to `button.png texture`
    Rectangle: push vertices (x1, y1...) to vbo & draw

Only the first :class:`~kivy.graphics.context_instructions.Color` and
:class:`~kivy.graphics.context_instructions.BindTexture` are useful, and really
change the context.  We can reduce them to ::

    Color: change 'color' context to 1, 1, 1
    BindTexture: change 'texture0' to `button.png texture`
    Rectangle: push vertices (x1, y1...) to vbo & draw
    Rectangle: push vertices (x1, y1...) to vbo & draw
    Rectangle: push vertices (x1, y1...) to vbo & draw

This is what the compiler does in the first place, by flagging all the unused
instruction with GI_IGNORE flag. As soon as a Color content change, the whole
InstructionGroup will be recompiled, and maybe a previous unused Color will be
used at the next compilation.

'''

include 'opcodes.pxi'

from instructions cimport Instruction, RenderContext, ContextInstruction

cdef class GraphicsCompiler:
    cdef InstructionGroup compile(self, InstructionGroup group):
        return group

        '''
        cdef Instruction c
        cdef ContextInstruction ci
        cdef RenderContext rc = None

        # Very simple compiler. We will apply all the element in the group.
        # If the render context is not changed between 2 call, we'll think that
        # the instruction could be ignored during the next frame. So flag as
        # GI_IGNORE.
        # Also, flag ourself as GL_NO_APPLY_ONCE, to prevent to reapply all the
        # instructions when the compiler is leaving.

        for c in group.children:

            # Select only the instructions who modify the context
            if c.flags & GI_CONTEXT_MOD:
                # convert as a ContextInstruction
                ci = c

                # get the context, and flag as done
                rc = ci.get_context()
                rc.flag_update_done()

                # apply the instruction
                ci.apply()

                # if the context didn't change at all, ignore the instruction
                if rc.flags & GI_NEEDS_UPDATE:
                    ci.flags &= ~GI_IGNORE
                else:
                    ci.flags |= GI_IGNORE
            else:
                c.apply()

        if rc:
            rc.flag_update()

        group.flags |= GI_NO_APPLY_ONCE

        return group
        '''
