"""
Canvas - abstraction
=========================================================

Abstract canvas system without OpenGL/graphics-specific implementation.
Focuses on the core hierarchical instruction system.
"""

__all__ = (
    "Instruction",
    "InstructionGroup",
    "ContextInstruction",
    "VertexInstruction",
    "Canvas",
    "CanvasBase",
    "RenderContext",
    "Callback",
)

from weakref import proxy


widget_uid = 0


class ObjectWithUid:
    """
    (internal) This class assists in providing unique identifiers for class
    instances. It is not intended for direct usage.
    """

    def __init__(self):
        global widget_uid
        widget_uid += 1
        self.uid = widget_uid


class Instruction(ObjectWithUid):
    """Base instruction class for all graphics operations."""

    # Flag constants
    NEEDS_UPDATE = 1

    def __init__(self, **kwargs):
        super().__init__()
        self.__proxy_ref = None
        self.flags = 0
        self.parent = None
        self.group = kwargs.get("group", None)

        if not kwargs.get("noadd"):
            self.parent = getActiveCanvas()
            if self.parent:
                self.parent.add(self)

    def apply(self):
        """Execute the instruction - override in subclasses."""
        # Ensure flag is cleared after applying
        self.flag_update_done()
        return 0

    def flag_update(self, do_parent=True):
        """Mark instruction as needing update."""
        if do_parent and self.parent is not None:
            self.parent.flag_update()
        self.flags |= self.NEEDS_UPDATE

    def flag_data_update(self):
        """Mark instruction data as changed."""
        self.flag_update()

    def flag_update_done(self):
        """Clear update flags."""
        self.flags &= ~self.NEEDS_UPDATE

    def set_parent(self, parent):
        """Set parent instruction group."""
        self.parent = parent

    def reload(self):
        """Reload instruction state."""
        self.flags |= self.NEEDS_UPDATE

    @property
    def needs_redraw(self):
        """Check if instruction needs redraw."""
        return (self.flags & self.NEEDS_UPDATE) > 0

    @property
    def proxy_ref(self):
        """Return a proxy reference to the Instruction i.e. without creating a
        reference of the widget. See `weakref.proxy
        <http://docs.python.org/2/library/weakref.html?highlight=proxy#weakref.proxy>`_
        for more information.

        .. versionadded:: 1.7.2
        """
        if self.__proxy_ref is None:
            self.__proxy_ref = proxy(self)
        return self.__proxy_ref


class InstructionGroup(Instruction):
    """Group of instructions that can be managed as a unit."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.children = []
        self.compiled_children = None

    def apply(self):
        """Apply all child instructions."""
        for child in self.children:
            child.apply()
        # Clear the update flag after applying all children
        self.flag_update_done()
        return 0

    def add(self, instruction):
        """Add instruction to group."""
        instruction.parent = self
        self.children.append(instruction)
        self.flag_data_update()

    def insert(self, index, instruction):
        """Insert instruction at specific position."""
        instruction.parent = self
        self.children.insert(index, instruction)
        self.flag_data_update()

    def remove(self, instruction):
        """Remove instruction from group."""
        if instruction in self.children:
            self.children.remove(instruction)
            instruction.parent = None
            self.flag_data_update()

    def indexof(self, instruction):
        """Get index of instruction in group."""
        try:
            return self.children.index(instruction)
        except ValueError:
            return -1

    def length(self):
        """Get number of children."""
        return len(self.children)

    def clear(self):
        """Remove all instructions."""
        for child in self.children[:]:
            self.remove(child)

    def remove_group(self, groupname):
        """Remove all instructions with specific group name."""
        for child in self.children[:]:
            if child.group == groupname:
                self.remove(child)

    def get_group(self, groupname):
        """Get all instructions with specific group name."""
        return [c for c in self.children if c.group == groupname]

    def reload(self):
        """Reload group and all children."""
        super().reload()
        for child in self.children:
            child.reload()

    # @property
    # def needs_redraw(self):
    #     """Check if group or any children need redraw."""
    #     if super().needs_redraw:
    #         return True
    #     return any(child.needs_redraw for child in self.children)


class ContextInstruction(Instruction):
    """Instruction that modifies rendering context state."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context_state = {}
        self.context_push = []
        self.context_pop = []

    def apply(self):
        """Apply context changes - override for specific implementation."""
        # Context manipulation would happen here in concrete implementation
        super().apply()  # This will clear the flag
        return 0

    def set_state(self, name, value):
        """Set context state value."""
        self.context_state[name] = value
        self.flag_update()

    def push_state(self, name):
        """Push state onto stack."""
        self.context_push.append(name)
        self.flag_update()

    def pop_state(self, name):
        """Pop state from stack."""
        self.context_pop.append(name)
        self.flag_update()


class VertexInstruction(Instruction):
    """Instruction for drawing visual elements."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._texture = None
        self._tex_coords = [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]

    def build(self):
        """Build vertex data - override in subclasses."""
        pass

    def apply(self):
        """Apply vertex instruction."""
        # Always build if needed, then clear flag
        if self.needs_redraw:
            self.build()

        # Always clear the flag after apply
        self.flag_update_done()
        
        # Drawing would happen here in concrete implementation
        return 0


class Callback(Instruction):
    """Instruction that executes a callback function."""

    def __init__(self, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.func = callback
        self.reset_context = kwargs.get("reset_context", False)

    def ask_update(self):
        """Request canvas update."""
        self.flag_data_update()

    def apply(self):
        """Execute callback function."""
        result = False
        if self.func is not None:
            result = self.func(self)

        # Always clear the flag after callback execution
        self.flag_update_done()
        return 0

    @property
    def callback(self):
        """Get/set callback function."""
        return self.func

    @callback.setter
    def callback(self, func):
        if self.func != func:
            self.func = func
            self.flag_data_update()


class CanvasBase(InstructionGroup):
    """Base canvas with context manager support."""

    def __enter__(self):
        pushActiveCanvas(self)
        return self

    def __exit__(self, *args):
        popActiveCanvas()


class Canvas(CanvasBase):
    """Main canvas class for managing drawing instructions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._opacity = kwargs.get("opacity", 1.0)
        self._before = None
        self._after = None

    def clear(self):
        """Clear all instructions except before/after groups."""
        for child in self.children[:]:
            if child is self._before or child is self._after:
                continue
            self.remove(child)

    def draw(self):
        """Execute all instructions."""
        self.apply()

    def apply(self):
        """Apply canvas with opacity handling."""
        # Opacity would be handled by rendering system
        super().apply()
        return 0

    def ask_update(self):
        """Request canvas update."""
        self.flag_data_update()

    @property
    def before(self):
        """Get before instruction group."""
        if self._before is None:
            self._before = CanvasBase()
            self.insert(0, self._before)
        return self._before

    @property
    def after(self):
        """Get after instruction group."""
        if self._after is None:
            self._after = CanvasBase()
            self.add(self._after)
        return self._after

    @property
    def has_before(self):
        """Check if before group exists."""
        return self._before is not None

    @property
    def has_after(self):
        """Check if after group exists."""
        return self._after is not None

    @property
    def opacity(self):
        """Get/set canvas opacity."""
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        if self._opacity != value:
            self._opacity = value
            self.flag_data_update()


class RenderContext(Canvas):
    """Canvas with rendering context and state management."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state_stacks = {
            "opacity": [1.0],
            "color": [[1.0, 1.0, 1.0, 1.0]],
        }

    def set_state(self, name, value):
        """Set rendering state value."""
        if name not in self.state_stacks:
            self.state_stacks[name] = [value]
            self.flag_update()
        else:
            stack = self.state_stacks[name]
            if value != stack[-1]:
                stack[-1] = value
                self.flag_update()

    def get_state(self, name):
        """Get current state value."""
        return self.state_stacks[name][-1]

    def push_state(self, name):
        """Push current state onto stack."""
        stack = self.state_stacks[name]
        stack.append(stack[-1])
        self.flag_update()

    def pop_state(self, name):
        """Pop state from stack."""
        stack = self.state_stacks[name]
        if len(stack) > 1:
            oldvalue = stack.pop()
            if oldvalue != stack[-1]:
                self.flag_update()

    def push_states(self, names):
        """Push multiple states."""
        for name in names:
            self.push_state(name)

    def pop_states(self, names):
        """Pop multiple states."""
        for name in names:
            self.pop_state(name)

    def enter(self):
        """Enter rendering context."""
        pushActiveContext(self)

    def leave(self):
        """Leave rendering context."""
        popActiveContext()

    def apply(self):
        """Apply context with state management."""
        keys = list(self.state_stacks.keys())
        self.enter()
        self.push_states(keys)
        super().apply()
        self.pop_states(keys)
        self.leave()
        # Flag is cleared by super().apply()
        self.flag_update_done()
        return 0

    def __setitem__(self, key, value):
        self.set_state(key, value)

    def __getitem__(self, key):
        return self.get_state(key)


# Global canvas management
_ACTIVE_CANVAS = None
_CANVAS_STACK = []


def getActiveCanvas():
    """Get currently active canvas."""
    global _ACTIVE_CANVAS
    return _ACTIVE_CANVAS


def pushActiveCanvas(canvas):
    """Push canvas onto active stack."""
    global _ACTIVE_CANVAS, _CANVAS_STACK
    _CANVAS_STACK.append(_ACTIVE_CANVAS)
    _ACTIVE_CANVAS = canvas


def popActiveCanvas():
    """Pop canvas from active stack."""
    global _ACTIVE_CANVAS, _CANVAS_STACK
    _ACTIVE_CANVAS = _CANVAS_STACK.pop() if _CANVAS_STACK else None


# Global context management
_ACTIVE_CONTEXT = None
_CONTEXT_STACK = []


def getActiveContext():
    """Get currently active rendering context."""
    global _ACTIVE_CONTEXT
    return _ACTIVE_CONTEXT


def pushActiveContext(context):
    """Push context onto active stack."""
    global _ACTIVE_CONTEXT, _CONTEXT_STACK
    _CONTEXT_STACK.append(_ACTIVE_CONTEXT)
    _ACTIVE_CONTEXT = context


def popActiveContext():
    """Pop context from active stack."""
    global _ACTIVE_CONTEXT, _CONTEXT_STACK
    _ACTIVE_CONTEXT = _CONTEXT_STACK.pop() if _CONTEXT_STACK else None

