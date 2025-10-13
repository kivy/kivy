"""
Motion Event Behaviors
======================

This module provides generic motion event filtering behaviors that work with
any motion event type (hover, drag, custom events, etc.).

These behaviors are commonly used with HoverBehavior from hover_behavior.py
but are designed to be generic and reusable with any motion event system.

Public Components:

1. MotionCollideBehavior (Mixin):
   Filters motion events to only process those within widget bounds or grabbed.
   Essential for RecycleView/ScrollView to prevent conflicts outside visible area.

2. MotionBlockBehavior (Mixin):
   Blocks unregistered motion events from passing through widget bounds.
   Makes widgets "opaque" to motion events, preventing leak-through to
   background widgets.

Example Usage with Hover:
    from kivy.uix.scrollview import ScrollView
    from hover_behavior import HoverBehavior
    from motion_behaviors import MotionCollideBehavior

    class HoverScrollView(MotionCollideBehavior, ScrollView):
        # Filters hover events outside stencil bounds
        pass

    class HoverItem(HoverBehavior, MotionCollideBehavior, Widget):
        # Only receives hover when visible and colliding
        pass

Example Usage with Custom Events:
    class DraggableItem(MotionCollideBehavior, Widget):
        # Only processes drag events inside bounds
        pass

    class OpaqueOverlay(MotionBlockBehavior, Widget):
        # Blocks all unregistered motion types
        pass
"""

__all__ = ("MotionCollideBehavior", "MotionBlockBehavior")


class MotionCollideBehavior:
    """Mixin to filter motion events based on collision detection.

    This mixin overrides on_motion to only process events that either:
    1. Collide with the widget's bounds, OR
    2. Are grabbed events (motion_event.grab_current is self)

    Generic Design:
        Works with ANY motion event type (hover, drag, custom events).
        Commonly used with HoverBehavior but not limited to hover events.

    Primary Use Case - StencilView:
        Essential for widgets that use stencil clipping (RecycleView, ScrollView).
        Without this mixin, widgets outside the stencil bounds can still receive
        motion events, leading to confusing behavior where invisible items respond.

    Example - With HoverBehavior:
        from hover_behavior import HoverBehavior

        class HoverRecycleView(MotionCollideBehavior, RecycleView):
            pass

        class HoverItem(HoverBehavior, MotionCollideBehavior, Label):
            pass

        # Now only visible items receive hover events
        # Items scrolled out of view are automatically ignored

    Example - With Custom Motion Events:
        class DraggableItem(MotionCollideBehavior, Widget):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.register_for_motion_event('drag')

            def on_motion(self, event_type, me):
                # Only processes drag events inside bounds
                return super().on_motion(event_type, me)

    Technical Note:
        The collision check uses widget.collide_point(*motion_event.pos), which
        tests against the widget's bounding box. For complex shapes, override
        collide_point() in your widget class for custom collision logic.

    Grabbed Events:
        Grabbed events always pass through, even if they don't collide.
        This ensures proper event completion - if a widget grabbed an event
        (e.g., on hover enter), it must receive the end event even if the
        cursor moved outside bounds.
    """

    def on_motion(self, event_type: str, motion_event) -> bool:
        """Filter motion events by collision or grab status.

        Only processes events that:
        - Are currently grabbed by this widget, OR
        - Have position data and collide with widget bounds

        Args:
            event_type: Motion event type ("begin", "update", "end")
            motion_event: MotionEvent to potentially filter

        Returns:
            bool: Result of super().on_motion() if passed filter,
            False otherwise
        """
        # Filter out non-qualifying events
        if (
            motion_event.grab_current is self
            or "pos" in motion_event.profile
            and self.collide_point(*motion_event.pos)
        ):
            return super().on_motion(event_type, motion_event)
        return False


class MotionBlockBehavior:
    """Mixin to block unregistered motion events from passing through.

    Makes widgets "opaque" to motion events they haven't registered to handle.
    When a motion event collides with the widget but the widget hasn't
    registered for that event type, the event is blocked from propagating to
    widgets behind it.

    Generic Design:
        Works with ANY motion event type (hover, drag, custom events).
        Prevents motion events from "leaking through" foreground widgets to
        background widgets.

    Use Cases:

    Blocking Hover Leak-Through:
        Prevent hover events from reaching widgets behind foreground elements.

        Example:
            from hover_behavior import HoverBehavior

            class OpaqueButton(MotionBlockBehavior, Button):
                pass

            layout = FloatLayout()
            layout.add_widget(HoverScrollView())  # Background
            layout.add_widget(OpaqueButton())     # Foreground

            # Hovering over button won't trigger ScrollView hover ✓

    Blocking Custom Motion Events:
        Works with any motion event type, not just hover.

        Example:
            class OpaqueDraggable(MotionBlockBehavior, Widget):
                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    # Don't register for 'drag' events
                    # But block them from passing through
                    pass

            # Drag events won't leak through to widgets behind

    Comparison with HoverBehavior:
        - MotionBlockBehavior: Blocks ALL unregistered motion event types
        - HoverBehavior (hover_mode='self'): Only blocks hover events with
          more fine-grained control

        For hover-specific blocking with more control, consider using
        HoverBehavior with hover_mode='self' instead.

    Technical Note:
        The collision check uses widget.collide_point(*motion_event.pos).
        For custom collision shapes, override collide_point() in your widget.

    Grabbed Events:
        Grabbed events always pass through, even if not registered.
        This ensures proper event lifecycle - if a widget grabs an event,
        it must receive all subsequent updates and the end event.
    """

    def on_motion(self, event_type: str, motion_event) -> bool:
        """Block unregistered motion events that collide with widget.

        Processing logic:
        1. If grabbed by this widget -> pass to super() (process)
        2. If collides but NOT registered -> return True (block)
        3. Otherwise -> pass to super() (continue propagation)

        Args:
            event_type: Motion event type ("begin", "update", "end")
            motion_event: MotionEvent to potentially block

        Returns:
            bool: True if event was blocked or handled, False otherwise
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
