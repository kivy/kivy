'''
Graphics compiler
=================

Before rendering an :class:`~kivy.graphics.instructions.InstructionGroup`, we
are compiling the group, in order to reduce the number of instructions executed
at rendering time.

Reducing the context instructions
---------------------------------

Imagine that you have a scheme like this::

    Color(1, 1, 1)
    Rectangle(source='button.png', pos=(0, 0), size=(20, 20))
    Color(1, 1, 1)
    Rectangle(source='button.png', pos=(10, 10), size=(20, 20))
    Color(1, 1, 1)
    Rectangle(source='button.png', pos=(10, 20), size=(20, 20))

The real instruction seen by the graphics canvas would be::

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
change the context.  We can reduce them to::

    Color: change 'color' context to 1, 1, 1
    BindTexture: change 'texture0' to `button.png texture`
    Rectangle: push vertices (x1, y1...) to vbo & draw
    Rectangle: push vertices (x1, y1...) to vbo & draw
    Rectangle: push vertices (x1, y1...) to vbo & draw

This is what the compiler does in the first place, by flagging all the unused
instruction with GI_IGNORE flag. As soon as a Color content change, the whole
InstructionGroup will be recompiled, and maybe a previous unused Color will be
used at the next compilation.


Note to any Kivy contributor / internal developer:

- All context instructions are checked if they are changing anything on the
  cache
- We must ensure that a context instruction are needed into our current Canvas.
- We must ensure that we don't depend of any other canvas
- We must reset our cache if one of our children is another instruction group,
  because we don't know if they are doing weird things or not.

'''

include 'opcodes.pxi'

from kivy.graphics.instructions cimport Instruction, RenderContext, ContextInstruction
from kivy.graphics.context_instructions cimport BindTexture

cdef class GraphicsCompiler:
    cdef InstructionGroup compile(self, InstructionGroup group):
        cdef int count = 0
        cdef Instruction c
        cdef ContextInstruction ci
        cdef RenderContext rc = None, oldrc = None
        cdef dict cs_by_rc = {}
        cdef list cs

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
                oldrc = rc
                rc = ci.get_context()

                # flag the old one as need update, if it's a new one
                if rc is not oldrc and oldrc is not None:
                    oldrc.flag_update(0)

                # it's a new render context, track changes.
                rc.flag_update_done()

                # apply the instruction
                ci.apply()

                # whatever happen, flag as needed (ie not ignore this one.)
                ci.flags &= ~GI_IGNORE

                # before flag as ignore, we must ensure that all the states
                # inside this context instruction are not needed at all.
                # if a state has never been in the cache yet, we can't ignore
                # it.
                if rc not in cs_by_rc:
                    cs = cs_by_rc[rc] = []
                else:
                    cs = cs_by_rc[rc]
                needed = 0

                if isinstance(ci, BindTexture):

                    # on texture case, bindtexture don't use context_state
                    # to transfer changes on render context, but use directly
                    # rendercontext.set_texture(). So we have no choice to try the
                    # apply(), and saving in cs, as a texture0
                    if 'texture0' not in cs:
                        cs.append('texture0')
                        needed = 1

                else:

                    for state in ci.context_state:
                        if state in cs:
                            continue
                        needed = 1
                        cs.append(state)

                # unflag the instruction only if it's not needed
                # and if the render context have not been changed
                if needed == 0 and not (rc.flags & GI_NEEDS_UPDATE):
                    ci.flags |= GI_IGNORE
                    count += 1
            else:
                if isinstance(c, InstructionGroup):
                    # we have potentially new childs, and them can fuck up our
                    # compilation, so reset our current cache.
                    cs_by_rc = {}
                c.apply()

        if rc:
            rc.flag_update(0)

        group.flags |= GI_NO_APPLY_ONCE

        return group
