include 'opcodes.pxi'

from instructions cimport Instruction, RenderContext, ContextInstruction

cdef class GraphicsCompiler:
    cdef InstructionGroup compile(self, InstructionGroup group):
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
                if rc.flags & GI_NEED_UPDATE:
                    ci.flags &= ~GI_IGNORE
                else:
                    ci.flags |= GI_IGNORE
            else:
                c.apply()

        if rc:
            rc.flag_update()

        group.flags |= GI_NO_APPLY_ONCE

        return group
