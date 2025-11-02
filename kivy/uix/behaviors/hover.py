"""
Hover Behavior
==============

The :class:`~kivy.uix.behaviors.hover.HoverBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class provides hover detection
and event handling for Kivy widgets. You can combine this class with other
widgets to add specialized hover events (on_hover_enter, on_hover_update,
on_hover_leave) and reactive hover state tracking.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

Related Behaviors
-----------------

For most hover use cases, you'll want to combine
:class:`~kivy.uix.behaviors.hover.HoverBehavior` with generic motion event
filters from :mod:`~kivy.uix.behaviors.motion`:

- :class:`~kivy.uix.behaviors.motion.MotionCollideBehavior`: Filters motion
  events to only process those within widget bounds. Essential for
  :class:`~kivy.uix.recycleview.RecycleView` and
  :class:`~kivy.uix.scrollview.ScrollView` to prevent hover conflicts outside
  visible area.

- :class:`~kivy.uix.behaviors.motion.MotionBlockBehavior`: Blocks unregistered
  motion events from passing through. Makes widgets "opaque" to motion events,
  preventing leak-through.

Examples
--------

Basic hover with visual feedback::

    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.behaviors import ButtonBehavior
    from kivy.uix.behaviors.hover import HoverBehavior

    class HoverButton(HoverBehavior, ButtonBehavior, Label):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.text = 'Hover me!'

        def on_hovered(self, instance, is_hovered):
            # Visual feedback: red when hovered, white otherwise
            self.color = [1, 0, 0, 1] if is_hovered else [1, 1, 1, 1]

        def on_hover_enter(self, motion_event):
            print(f"Mouse entered at {motion_event.pos}")

        def on_hover_leave(self, motion_event):
            print(f"Mouse left at {motion_event.pos}")

    class SampleApp(App):
        def build(self):
            return HoverButton()

    SampleApp().run()

Using with ScrollView and collision filtering::

    from kivy.uix.scrollview import ScrollView
    from kivy.uix.label import Label
    from kivy.uix.behaviors.hover import HoverBehavior
    from kivy.uix.behaviors.motion import MotionCollideBehavior

    class HoverScrollView(MotionCollideBehavior, ScrollView):
        # Filters hover events outside stencil bounds
        pass

    class HoverItem(HoverBehavior, MotionCollideBehavior, Label):
        def on_hovered(self, instance, is_hovered):
            self.color = [1, 0, 0, 1] if is_hovered else [1, 1, 1, 1]

    # Now only visible items receive hover events
    # Items scrolled out of view are automatically ignored

Blocking hover leak-through to background widgets::

    from kivy.uix.button import Button
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.behaviors.motion import MotionBlockBehavior

    class OpaqueButton(MotionBlockBehavior, Button):
        # Blocks all unregistered motion events from passing through
        pass

    layout = FloatLayout()
    layout.add_widget(HoverScrollView())  # Background
    layout.add_widget(OpaqueButton())     # Foreground
    # Hovering over button won't trigger ScrollView hover

Configuring hover update behavior::

    from kivy.uix.behaviors.hover import HoverBehavior

    # Disable hover re-dispatching for stationary mouse
    HoverBehavior.set_hover_update_interval(-1)

    # Re-dispatch once after 0.1s (max 10 updates per second)
    HoverBehavior.set_hover_update_interval(0.1)

    # Default: re-dispatch once after 1/30s (max 30 updates per second)
    HoverBehavior.set_hover_update_interval(1/30)

See :class:`~kivy.uix.behaviors.hover.HoverBehavior` for details.
"""

__all__ = ("HoverBehavior",)

from collections import defaultdict
from enum import Enum
from typing import Dict, List, Tuple

from kivy.clock import Clock
from kivy.eventmanager import MODE_DONT_DISPATCH, EventManagerBase
from kivy.loader import Logger
from kivy.properties import AliasProperty, DictProperty, OptionProperty


class HoverEventType(str, Enum):
    """Event type identifiers for hover-related events.

    Used to distinguish between different categories of hover events
    in the event system.
    """

    HOVER = "hover"


class HoverMotionType(str, Enum):
    """Motion phase identifiers for hover interactions.

    Tracks the lifecycle of a hover event from start to finish:
    - BEGIN: Initial hover detection
    - UPDATE: Continuous hover movement
    - END: Hover termination
    """

    BEGIN = "begin"
    UPDATE = "update"
    END = "end"


class HoverMode(str, Enum):
    """Hover event propagation modes.

    Controls how hover events are distributed through the widget hierarchy:
    - DEFAULT: Dispatch to children first, then self if not accepted
    - ALL: Dispatch to both children AND self
    - SELF: Skip children, dispatch only to self
    """

    DEFAULT = "default"
    ALL = "all"
    SELF = "self"


class _HoverManager(EventManagerBase):
    """(Internal) Global manager for dispatching hover events through the widget
    tree.

    This is an internal implementation. Users should not interact with
    this class directly. It is automatically registered by
    :class:`~kivy.uix.behaviors.hover.HoverBehavior` on first use.

    Responsibilities:
        - Receives hover events from :class:`~kivy.core.window.Window`
        - Transforms coordinates to window space
        - Dispatches through widget tree via on_motion protocol
        - Tracks grabbed widgets between frames
        - Synthesizes hover leave events when widgets lose hover

    Static Hover Re-dispatching:
        Re-dispatches hover events once when the mouse position hasn't changed
        AND the time since last dispatch exceeds ``hover_update_interval``. This
        ensures widgets receive proper hover events (enter/update/leave) when:

        - Mouse is stationary but content scrolls (RecycleView/ScrollView)
        - Widget moves/resizes under cursor
        - Disabled widgets become enabled under cursor

        The interval is controlled via
        :meth:`HoverBehavior.set_hover_update_interval`.
        Set interval to negative value to disable this feature entirely.

    Event Flow:
        1. Window generates hover event (mouse movement without buttons)
        2. Manager transforms event coordinates
        3. Event propagates through widget tree
        4. HoverBehavior widgets handle and update state
        5. Manager tracks grabbed widgets
        6. On next frame, sends leave events to ungrabbed widgets

    Grab List Management:
        Maintains history of grabbed widgets between frames to properly
        synthesize leave events. When mouse moves from widget A to B,
        Kivy doesn't send automatic end events - we detect this by
        comparing grab lists.
    """

    type_ids = (HoverEventType.HOVER.value,)
    hover_update_interval = 1 / 30.0

    def __init__(self, **kwargs):
        super().__init__()
        # Track event history: uid -> [(event, grab_list)]
        # Keep last 2 frames to compare grab states
        self._events: Dict[int, List[Tuple]] = defaultdict(list)

        self._event_times = {}  # me.uid -> Clock.get_time()
        self._clock_event = Clock.create_trigger(
            self._dispatch_from_clock, interval=True
        )

    def start(self):
        """Initialize manager. Called when registered with Window."""
        if self.hover_update_interval >= 0:
            self._clock_event()

    def stop(self):
        """Stop manager and cleanup resources. Can be called on Window shutdown."""
        self._events.clear()

        self._event_times.clear()
        if self._clock_event:
            self._clock_event.cancel()
            self._clock_event = None

    def update_hover_interval(self, interval):
        """Update the hover update interval.

        :param interval: Seconds between updates, or negative to disable
        """
        self.hover_update_interval = interval

        if interval >= 0:
            self._clock_event.timeout = interval
            if not self._clock_event.is_triggered:
                self._clock_event()
        else:
            self._clock_event.cancel()

    def dispatch(self, event_type: str, motion_event) -> bool:
        """Main entry point for hover event dispatch.

        Orchestrates the hover event lifecycle:

        1. Saves current grab list
        2. Dispatches to widget tree
        3. Stores event history
        4. Sends leave events to ungrabbed widgets
        5. Cleans up completed events

        :param event_type: Type of event ("begin", "update", "end")
        :param motion_event: :class:`~kivy.input.motionevent.MotionEvent` instance
        :return: True if any widget accepted the event
        """
        # Save original grab list for other event managers
        original_grab_list = motion_event.grab_list[:]
        del motion_event.grab_list[:]

        # Dispatch to widget tree
        was_accepted = self._dispatch_to_widgets(event_type, motion_event)

        # Store this frame's state for next frame comparison
        self._events[motion_event.uid].insert(
            0, (motion_event, motion_event.grab_list[:])
        )

        self._event_times[motion_event.uid] = Clock.get_time()

        # Check for widgets that lost hover
        if len(self._events[motion_event.uid]) == 2:
            _, previous_grab_list = self._events[motion_event.uid].pop()
            self._send_leave_events_to_ungrabbed_widgets(
                motion_event, previous_grab_list
            )

        # Clean up completed events
        if event_type == HoverMotionType.END:
            del self._events[motion_event.uid]
            del self._event_times[motion_event.uid]

        # Restore original grab list
        motion_event.grab_list[:] = original_grab_list
        return was_accepted

    def _dispatch_to_widgets(self, event_type: str, motion_event) -> bool:
        """Dispatch motion event through the window's widget tree.

        Widgets are transparent by default - events pass through widgets that
        haven't registered to handle them. This matches Kivy's touch event
        behavior where unhandled events propagate to widgets behind.

        :param event_type: Motion event type ("begin", "update", "end")
        :param motion_event: MotionEvent to dispatch
        :return: True if any widget accepted the event, False otherwise
        """
        was_accepted = False

        motion_event.push()
        self.window.transform_motion_event_2d(motion_event)

        for widget in self.window.children[:]:
            # Check: registered + collides + handled
            if (
                HoverEventType.HOVER.value in widget.motion_filter
                and widget.collide_point(*motion_event.pos)
                and widget.dispatch("on_motion", event_type, motion_event)
            ):
                was_accepted = True
                break
            # Not registered or didn't handle - continue (transparent for hover)

        motion_event.pop()
        return was_accepted

    def _send_leave_events_to_ungrabbed_widgets(
        self, motion_event, previous_grab_list: List
    ):
        """Send end events to widgets that lost hover between frames.

        Compares previous and current grab lists to find widgets that
        lost hover, then dispatches end events to trigger on_hover_leave.

        :param motion_event: Current motion event
        :param previous_grab_list: Grabbed widgets from previous frame
        """
        # Save current state
        current_grab_state = motion_event.grab_state
        current_time_end = motion_event.time_end
        current_grab_list = motion_event.grab_list[:]

        # Restore previous frame's state
        motion_event.grab_list[:] = previous_grab_list
        motion_event.update_time_end()
        motion_event.grab_state = True

        # Find widgets that lost hover
        for weak_widget_ref in previous_grab_list:
            if weak_widget_ref not in current_grab_list:
                widget = weak_widget_ref()
                if widget:
                    self._dispatch_to_single_widget(
                        HoverMotionType.END, motion_event, widget
                    )

        # Restore current state
        motion_event.grab_list[:] = current_grab_list
        motion_event.grab_state = current_grab_state
        motion_event.time_end = current_time_end

    def _dispatch_to_single_widget(self, event_type: str, motion_event, widget):
        """Dispatch event to specific widget with coordinate transformation.

        :param event_type: Type of event ("begin", "update", "end")
        :param motion_event: :class:`~kivy.input.motionevent.MotionEvent` to dispatch
        :param widget: Target widget
        """
        root_window = widget.get_root_window()

        # Transform to widget space if needed
        needs_transform = root_window and root_window != widget
        if needs_transform:
            motion_event.push()
            try:
                self.window.transform_motion_event_2d(motion_event, widget)
            except AttributeError:
                motion_event.pop()
                return

        # Set widget as grab target
        original_grab_current = motion_event.grab_current
        motion_event.grab_current = widget

        # Dispatch with context handling
        widget._context.push()
        if widget._context.sandbox:
            with widget._context.sandbox:
                widget.dispatch("on_motion", event_type, motion_event)
        else:
            widget.dispatch("on_motion", event_type, motion_event)
        widget._context.pop()

        # Restore grab state
        motion_event.grab_current = original_grab_current

        if needs_transform:
            motion_event.pop()

    def _dispatch_from_clock(self, *args):
        """Dispatch hover events for stationary mouse.

        Re-dispatches existing hover events once when the time since the last
        event exceeds hover_update_interval. This enables hover events
        (enter/update/leave) to fire when content changes under a static cursor.
        """
        times = self._event_times
        time_now = Clock.get_time()
        events_to_update = []
        for me_id, items in self._events.items():
            me, _ = items[0]
            if time_now - times[me.uid] < self.hover_update_interval:
                continue
            events_to_update.append(me)
        for me in events_to_update:
            psx, psy, psz = me.psx, me.psy, me.psz
            dsx, dsy, dsz = me.dsx, me.dsy, me.dsz
            me.psx, me.psy, me.psz = me.sx, me.sy, me.sz
            me.dsx = me.dsy = me.dsz = 0.0
            self.dispatch("update", me)
            me.psx, me.psy, me.psz = psx, psy, psz
            me.dsx, me.dsy, me.dsz = dsx, dsy, dsz


class HoverBehavior:
    """Mixin to add hover detection and event handling to any Kivy widget.

    This mixin enables widgets to respond to mouse hover events with three
    specialized events: :meth:`on_hover_enter`, :meth:`on_hover_update`, and
    :meth:`on_hover_leave`. It also provides a reactive :attr:`hovered` property.

    Hover State Management
    ----------------------
    Tracks active hover events internally. Each hover event gets a unique
    ID (supports multi-touch hover). When a hover enters widget bounds,
    it's tracked. When it leaves, it's removed. The :attr:`hovered` property
    is True when any hover events are active.

    Event Propagation Modes
    ------------------------
    - **"default"**: Standard behavior. Events go to children first. If no child
      accepts, the event is offered to this widget.

    - **"all"**: Forces dispatch to both children AND this widget, regardless
      of whether children accept. Use when parent needs to track hovers even
      while children handle them (e.g., container with hover effects).

    - **"self"**: Skips children entirely. This widget captures all hover events
      within its bounds. Use for widgets that should be "opaque" to hover
      (e.g., popup overlays).

    Static Hover Re-dispatching
    ----------------------------
    By default, hover events are re-dispatched once when the mouse is
    stationary AND the time since the last dispatch exceeds 1/30s. This
    enables proper hover state tracking when content moves under a
    stationary cursor (e.g., scrolling with mousewheel).

    All three hover events (enter/update/leave) are affected:

    - :meth:`on_hover_enter`: Fires when widget scrolls under static cursor
    - :meth:`on_hover_update`: Fires once after interval
    - :meth:`on_hover_leave`: Fires when widget scrolls away from cursor

    Configure globally before creating widgets::

        # Disable re-dispatching entirely
        HoverBehavior.set_hover_update_interval(-1)

        # Re-dispatch once after 0.1s (max 10 updates per second)
        HoverBehavior.set_hover_update_interval(0.1)

        # Default: re-dispatch once after 1/30s (max 30 updates per second)
        HoverBehavior.set_hover_update_interval(1/30)

    Combining with Motion Filters
    ------------------------------
    For most use cases, combine :class:`~kivy.uix.behaviors.hover.HoverBehavior`
    with motion event filters from :mod:`~kivy.uix.behaviors.motion`:

    Example - ScrollView with Collision Filter::

        from kivy.uix.behaviors.motion import MotionCollideBehavior

        class HoverScrollView(MotionCollideBehavior, ScrollView):
            # Filters hover outside stencil bounds
            pass

        class HoverItem(HoverBehavior, MotionCollideBehavior, Label):
            # Only receives hover when visible
            pass

    Example - Blocking Hover Leak-Through::

        from kivy.uix.behaviors.motion import MotionBlockBehavior

        class OpaqueButton(MotionBlockBehavior, Button):
            # Blocks all unregistered motion events
            pass

        layout = FloatLayout()
        layout.add_widget(HoverScrollView())  # Background
        layout.add_widget(OpaqueButton())     # Foreground
        # Hovering button won't trigger ScrollView hover

    Events
    ------
    :meth:`on_hover_enter`
        First collision with widget bounds
    :meth:`on_hover_update`
        Hover moved within bounds
    :meth:`on_hover_leave`
        Hover left widget bounds

    Internal State
    --------------
    For subclassing: ``_hover_ids`` (dict) maps active hover UIDs to positions
    {uid: (x, y)}. Updated by hover events. Empty when not hovered.
    """

    _hover_manager = None

    def _get_hovered(self) -> bool:
        """Compute hovered state based on active hover events.

        :return: True if any hover events are currently active
        """
        return bool(self._hover_ids)

    hovered = AliasProperty(_get_hovered, bind=["_hover_ids"], cache=True)
    """Read-only boolean indicating if widget is currently hovered.

    :attr:`hovered` is an :class:`~kivy.properties.AliasProperty` and defaults
    to False.
    """

    hover_mode = OptionProperty(
        HoverMode.DEFAULT, options=tuple(mode for mode in HoverMode)
    )
    """Controls how hover events propagate through the widget tree.

    Modes:

    - **"default"**: Standard propagation. Children first, then self if not
      accepted. Use this for most widgets.

    - **"all"**: Force dispatch to both children AND self. Use when parent needs
      to track hovers even when children handle them (e.g., container
      with background hover effects).

    - **"self"**: Skip children entirely. Capture all hovers within bounds.
      Use for modal overlays or widgets that should be "opaque" to
      hover events.

    :attr:`hover_mode` is an :class:`~kivy.properties.OptionProperty` and
    defaults to "default".
    """

    _hover_ids = DictProperty()

    def __init_subclass__(cls, **kwargs):
        """Auto-register internal manager when first HoverBehavior is created.

        Ensures the hover system is ready before any hover events occur.
        Uses class-level flag to register only once.
        """
        super().__init_subclass__(**kwargs)

        if HoverBehavior._hover_manager is None:
            from kivy.core.window import Window

            hover_manager = _HoverManager()
            Window.register_event_manager(hover_manager)
            HoverBehavior._hover_manager = hover_manager

            Logger.debug(
                "HoverBehavior: Internal hover manager registered for "
                "window %s",
                Window,
            )

    def __init__(self, **kwargs):
        """Initialize HoverBehavior mixin.

        Registers hover-specific events and subscribes to hover motion events.
        """
        self.register_event_type("on_hover_enter")
        self.register_event_type("on_hover_update")
        self.register_event_type("on_hover_leave")

        # Subscribe to hover motion events
        self.register_for_motion_event(HoverEventType.HOVER.value)

        super().__init__(**kwargs)

    def on_motion(self, event_type: str, motion_event) -> bool:
        """Handle incoming motion events, filtering for hover events.

        Main entry point for motion events. Filters for hover events and
        handles them according to :attr:`hover_mode`. Non-hover events pass to
        parent.

        :param event_type: Type of motion event ("begin", "update", "end")
        :param motion_event: :class:`~kivy.input.motionevent.MotionEvent` instance
        :return: True if event was handled
        """
        # Filter: only process hover events with position
        is_hover_event = (
            motion_event.type_id == HoverEventType.HOVER
            and "pos" in motion_event.profile
        )

        if not is_hover_event:
            return super().on_motion(event_type, motion_event)

        # Handle based on hover_mode
        if self.hover_mode == HoverMode.DEFAULT:
            # Standard: children first, then self
            if super().on_motion(event_type, motion_event):
                return True
            return self._handle_hover_event(event_type, motion_event)

        # Handle HoverMode.ALL and HoverMode.SELF
        original_dispatch_mode = motion_event.dispatch_mode

        if self.hover_mode == HoverMode.SELF:
            # Block children
            motion_event.dispatch_mode = MODE_DONT_DISPATCH

        # Dispatch to children (unless blocked)
        child_accepted = super().on_motion(event_type, motion_event)

        # Always dispatch to self
        self_accepted = self._handle_hover_event(event_type, motion_event)

        motion_event.dispatch_mode = original_dispatch_mode

        return self_accepted or child_accepted

    def _handle_hover_event(self, event_type: str, motion_event) -> bool:
        """Process hover event and dispatch appropriate hover sub-events.

        Implements core hover detection:

        1. Test collision with widget bounds
        2. Grab event if colliding (marks widget as hover owner)
        3. Dispatch enter/update/leave based on state changes
        4. Ungrab event when hover ends

        Grab Mechanism:
            When hover enters bounds, we grab it with motion_event.grab(self).
            This marks the widget as owner. Grab persists across frames until
            explicit ungrab, maintaining hover state as mouse moves.

        :param event_type: Motion event type ("begin", "update", "end")
        :param motion_event: :class:`~kivy.input.motionevent.MotionEvent` instance
        :return: True if event was handled (collided with widget)
        """
        is_colliding = self.collide_point(*motion_event.pos)
        hover_uid = motion_event.uid

        # Handle begin/update (hover active)
        if event_type in (HoverMotionType.UPDATE, HoverMotionType.BEGIN):
            # Already grabbed by us
            if motion_event.grab_current is self:
                return True

            # Disabled widgets block but don't dispatch
            if self.disabled and is_colliding:
                return True

            # Hover within bounds - grab and dispatch
            if is_colliding:
                motion_event.grab(self)

                # First time - dispatch enter
                if hover_uid not in self._hover_ids:
                    self._hover_ids[hover_uid] = motion_event.pos
                    self.dispatch("on_hover_enter", motion_event)

                # Moved within bounds - dispatch update
                elif self._hover_ids[hover_uid] != motion_event.pos:
                    self._hover_ids[hover_uid] = motion_event.pos
                    self.dispatch("on_hover_update", motion_event)

                return True

        # Handle end (hover stopped or left)
        elif event_type == HoverMotionType.END:
            # We own this hover - clean up and dispatch leave
            if motion_event.grab_current is self:
                self._hover_ids.pop(hover_uid, None)
                motion_event.ungrab(self)
                self.dispatch("on_hover_leave", motion_event)
                return True

            # Disabled widget blocking
            if self.disabled and is_colliding:
                return True

        return False

    @classmethod
    def set_hover_update_interval(cls, interval):
        """Configure hover re-dispatching interval globally.

        Controls the minimum time between hover re-dispatches when the mouse
        is stationary. Re-dispatches once when:

        1. Mouse hasn't moved, AND
        2. Time since last dispatch exceeds interval

        This affects all three hover events (enter/update/leave) and is
        essential for scenarios where content moves under a static cursor
        (e.g., scrolling with mousewheel).

        When enabled, the system re-checks which widgets should receive hover
        events, allowing proper enter/leave events as widgets scroll in/out
        of view.

        This configuration applies to all
        :class:`~kivy.uix.behaviors.hover.HoverBehavior` widgets and can be
        called before any widgets are instantiated.

        :param interval: Seconds between re-dispatches. Use negative value to
                        disable re-dispatching entirely

        Example::

            # Disable re-dispatching (no scroll hover updates)
            HoverBehavior.set_hover_update_interval(-1)

            # Re-dispatch once after 0.1s (max 10 updates per second)
            HoverBehavior.set_hover_update_interval(0.1)

            # Default: re-dispatch once after 1/30s (max 30 updates per second)
            HoverBehavior.set_hover_update_interval(1/30)

        .. note::
            When disabled (negative interval), hover events only fire when the
            mouse actually moves. Content scrolling under a static cursor will
            not trigger enter/update/leave events.
        """
        if not isinstance(interval, (float, int)):
            raise ValueError("interval must be a number (seconds)")

        if cls._hover_manager:
            cls._hover_manager.update_hover_interval(float(interval))
        else:
            _HoverManager.hover_update_interval = float(interval)

    @classmethod
    def get_hover_update_interval(cls):
        """Get the current hover re-dispatch interval.

        :return: Current interval in seconds, or negative if disabled

        Example::

            interval = HoverBehavior.get_hover_update_interval()
            if interval < 0:
                print("Hover re-dispatching disabled")
            else:
                print(f"Re-dispatches every {interval:.3f} seconds")
        """
        return _HoverManager.hover_update_interval

    def on_hover_enter(self, motion_event):
        """Called when hover first enters widget bounds.

        Override this method to respond to hover enter events.

        :param motion_event: :class:`~kivy.input.motionevent.MotionEvent`
        """
        pass

    def on_hover_update(self, motion_event):
        """Called when hover moves within widget bounds.

        If the mouse doesn't move AND enough time has passed since the last
        dispatch, this is called once.

        Disable re-dispatching via
        :meth:`set_hover_update_interval(-1) <set_hover_update_interval>` if this
        behavior is not needed.

        :param motion_event: :class:`~kivy.input.motionevent.MotionEvent`
        """
        pass

    def on_hover_leave(self, motion_event):
        """Called when hover exits widget bounds.

        Override this method to respond to hover leave events.

        :param motion_event: :class:`~kivy.input.motionevent.MotionEvent`
        """
        pass
