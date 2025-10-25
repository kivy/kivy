"""
Motion Event Behaviors
======================

The :class:`~kivy.uix.behaviors.motion.MotionCollideBehavior` and
:class:`~kivy.uix.behaviors.motion.MotionBlockBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ classes provide generic
motion event filtering for any motion event type (hover, drag, custom events).

These behaviors are commonly used with :class:`~kivy.uix.behaviors.hover.HoverBehavior`
but are designed to be generic and reusable with any motion event system.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

Components
----------

**MotionCollideBehavior**:
    Filters motion events to only process those within widget bounds or grabbed.
    Essential for :class:`~kivy.uix.recycleview.RecycleView` and
    :class:`~kivy.uix.scrollview.ScrollView` to prevent conflicts outside
    visible area.

**MotionBlockBehavior**:
    Blocks unregistered motion events from passing through widget bounds.
    Makes widgets "opaque" to motion events, preventing leak-through to
    background widgets.

Examples
--------

Using MotionCollideBehavior with HoverBehavior::

    from kivy.uix.scrollview import ScrollView
    from kivy.uix.label import Label
    from kivy.uix.behaviors.hover import HoverBehavior
    from kivy.uix.behaviors.motion import MotionCollideBehavior

    class HoverScrollView(MotionCollideBehavior, ScrollView):
        # Filters hover events outside stencil bounds
        pass

    class HoverItem(HoverBehavior, MotionCollideBehavior, Label):
        def on_enter(self):
            self.color = [1, 0, 0, 1]  # Red on hover

        def on_leave(self):
            self.color = [1, 1, 1, 1]  # White normally

Using MotionBlockBehavior to prevent event leak-through::

    from kivy.uix.button import Button
    from kivy.uix.floatlayout import FloatLayout
    from motion_behaviors import MotionBlockBehavior

    class OpaqueButton(MotionBlockBehavior, Button):
        # Blocks unregistered motion events from passing through
        pass

    layout = FloatLayout()
    layout.add_widget(HoverScrollView())  # Background
    layout.add_widget(OpaqueButton())     # Foreground
    # Hovering over button won't trigger ScrollView hover

Important Notes
---------------

**DO NOT** use :class:`~kivy.uix.behaviors.motion.MotionCollideBehavior` and
:class:`~kivy.uix.behaviors.motion.MotionBlockBehavior` together on the same
widget. They serve different purposes:

- **MotionCollideBehavior**: Filters events outside widget bounds
    * Use for: Items in RecycleView/ScrollView
    * Purpose: Ignore events when widget is outside visible area

- **MotionBlockBehavior**: Blocks unregistered event types from passing through
    * Use for: Overlay widgets, modal dialogs, foreground elements
    * Purpose: Prevent events from leaking to widgets behind

Combining them creates redundant or conflicting logic.

See :class:`~kivy.uix.behaviors.motion.MotionCollideBehavior` and
:class:`~kivy.uix.behaviors.motion.MotionBlockBehavior` for details.
"""

__all__ = ("MotionCollideBehavior", "MotionBlockBehavior")


class MotionCollideBehavior:
    """Mixin to filter motion events based on collision detection.

    This mixin overrides :meth:`on_motion` to only process events that either:

    1. Collide with the widget's bounds, OR
    2. Are grabbed events (motion_event.grab_current is self)

    Generic Design
    --------------
    Works with ANY motion event type (hover, drag, custom events).
    Commonly used with :class:`~kivy.uix.behaviors.hover.HoverBehavior` but
    not limited to hover events.

    Primary Use Case - StencilView
    -------------------------------
    Essential for widgets that use stencil clipping
    (:class:`~kivy.uix.recycleview.RecycleView`,
    :class:`~kivy.uix.scrollview.ScrollView`). Without this mixin, widgets
    outside the stencil bounds can still receive motion events, leading to
    confusing behavior where invisible items respond.

    Technical Note
    --------------
    The collision check uses :meth:`widget.collide_point(*motion_event.pos)`,
    which tests against the widget's bounding box. For complex shapes, override
    :meth:`collide_point()` in your widget class for custom collision logic.

    Grabbed Events
    --------------
    Grabbed events always pass through, even if they don't collide. This ensures
    proper event completion - if a widget grabbed an event (e.g., on hover
    enter), it must receive the end event even if the cursor moved outside
    bounds.
    """

    def on_motion(self, event_type: str, motion_event) -> bool:
        """Filter motion events by collision or grab status.

        Only processes events that:

        - Are currently grabbed by this widget, OR
        - Have position data and collide with widget bounds

        :param event_type: Motion event type ("begin", "update", "end")
        :param motion_event: MotionEvent to potentially filter
        :return: Result of super().on_motion() if passed filter, False otherwise
        """
        is_grabbed = motion_event.grab_current is self
        has_position = "pos" in motion_event.profile
        collides = has_position and self.collide_point(*motion_event.pos)

        # Process only grabbed events or events within bounds
        if is_grabbed or collides:
            return super().on_motion(event_type, motion_event)

        # Filter out non-qualifying events
        return False


class MotionBlockBehavior:
    """Mixin to block unregistered motion events from passing through.

    Makes widgets "opaque" to motion events they haven't registered to handle.
    When a motion event collides with the widget but the widget hasn't
    registered for that event type, the event is blocked from propagating to
    widgets behind it.

    Generic Design
    --------------
    Works with ANY motion event type (hover, drag, custom events). Prevents
    motion events from "leaking through" foreground widgets to background
    widgets.

    Comparison with HoverBehavior
    ------------------------------
    - **MotionBlockBehavior**: Blocks ALL unregistered motion event types
    - **HoverBehavior** (hover_mode='self'): Only blocks hover events with
      more fine-grained control

    For hover-specific blocking with more control, consider using
    :class:`~kivy.uix.behaviors.hover.HoverBehavior` with hover_mode='self'
    instead.

    Technical Note
    --------------
    The collision check uses :meth:`widget.collide_point(*motion_event.pos)`.
    For custom collision shapes, override :meth:`collide_point()` in your
    widget.

    Grabbed Events
    --------------
    Grabbed events always pass through, even if not registered. This ensures
    proper event lifecycle - if a widget grabs an event, it must receive all
    subsequent updates and the end event.
    """

    def on_motion(self, event_type: str, motion_event) -> bool:
        """Block unregistered motion events that collide with widget.

        Processing logic:

        1. If grabbed by this widget -> pass to super() (process)
        2. If collides but NOT registered -> return True (block)
        3. Otherwise -> pass to super() (continue propagation)

        :param event_type: Motion event type ("begin", "update", "end")
        :param motion_event: MotionEvent to potentially block
        :return: True if event was blocked or handled, False otherwise
        """
        # Grabbed events always pass through
        if motion_event.grab_current is self:
            return super().on_motion(event_type, motion_event)

        # Check collision and registration
        has_position = "pos" in motion_event.profile
        collides = has_position and self.collide_point(*motion_event.pos)
        is_registered = motion_event.type_id in self.motion_filter

        # Block if collides but not registered
        if collides and not is_registered:
            return True

        # Pass through to normal processing
        return super().on_motion(event_type, motion_event)
