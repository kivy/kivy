"""
Button Behavior
===============

The :class:`~kivy.uix.behaviors.button.ButtonBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class provides button behavior
for Kivy widgets. You can combine this class with other widgets to add
specialized press/release/cancel events and reactive pressed state tracking.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

Examples
--------

Basic button with visual feedback::

    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.behaviors import ButtonBehavior

    class MyButton(ButtonBehavior, Label):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.text = "Press me!"

        def on_pressed(self, instance, is_pressed):
            # Visual feedback: red when pressed, white otherwise
            self.color = [1, 0, 0, 1] if is_pressed else [1, 1, 1, 1]

        def on_press(self):
            print("Button pressed")

        def on_release(self):
            print("Button released")

    class SampleApp(App):
        def build(self):
            return MyButton()

    SampleApp().run()

Handling button cancellation::

    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.behaviors import ButtonBehavior

    class MyButton(ButtonBehavior, Label):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.text = 'Press me!'
            self.always_release = False  # Enable cancellation

        def on_press(self):
            self.text = 'Pressed - drag outside to cancel'

        def on_release(self):
            self.text = 'Released!'

        def on_cancel(self):
            self.text = 'Action cancelled!'

    class SampleApp(App):
        def build(self):
            return MyButton()

    SampleApp().run()


See :class:`~kivy.uix.behaviors.ButtonBehavior` for details.
"""

__all__ = ("ButtonBehavior",)

from kivy.properties import BooleanProperty, AliasProperty, ObjectProperty

from kivy.core.accessibility import Role


class ButtonBehavior:
    """Mixin to add button behavior to any Kivy widget.

    This mixin enables widgets to respond to press/release interactions with
    automatic multi-touch support. It provides three specialized events:
    :meth:`on_press`, :meth:`on_release`, and :meth:`on_cancel`, along with
    a reactive :attr:`pressed` property.

    Button State Management
    -----------------------
    Tracks active touches internally using a set-based approach. Each touch
    gets a unique ID (supports multi-touch). When first touch enters widget
    bounds, button becomes pressed. When ALL touches are released or cancelled,
    button returns to unpressed state. The :attr:`pressed` property is True
    when any touches are active.

    Multi-Touch Behavior
    --------------------
    The button automatically handles multiple simultaneous touches:

    - **First touch down**: Triggers :meth:`on_press`, sets :attr:`pressed` to True
    - **Additional touches**: Tracked but don't trigger :meth:`on_press` again
    - **Touch release**: Only triggers :meth:`on_release` after ALL touches released
    - **Touch cancel**: Removes touch from tracking, updates :attr:`pressed` state

    Release Modes
    -------------
    Controlled by :attr:`always_release` property:

    - **False (default)**: Standard button behavior. :meth:`on_release` only fires
      if touch ends within button bounds. :meth:`on_cancel` fires when touch
      moves outside bounds during drag (touch move).

    - **True**: Always fires :meth:`on_release` regardless of touch position.
      :meth:`on_cancel` never fires. Useful for drag-and-drop or gesture-based
      interfaces.

    Events
    ------
    :meth:`on_press`
        First touch down on button
    :meth:`on_release`
        All touches released (respects :attr:`always_release` mode)
    :meth:`on_cancel`
        Touch moved outside bounds during drag (only when :attr:`always_release`
         is False)


    .. versionchanged:: 3.0.0
        - Replaced ``state`` OptionProperty with ``pressed`` BooleanProperty
        - Made ``pressed`` read-only via AliasProperty
        - Added :meth:`on_cancel` event
        - Improved multi-touch handling with explicit touch sets
    """

    always_release = BooleanProperty(False)
    """Determines whether the widget fires :meth:`on_release` when touch ends
    outside widget bounds.

    When False (default):
        - :meth:`on_release` only fires if touch ends within button bounds
        - :meth:`on_cancel` fires when touch moves outside bounds during drag
        - Provides standard button behavior with cancellation feedback

    When True:
        - :meth:`on_release` always fires regardless of final touch position
        - :meth:`on_cancel` never fires
        - Useful for drag-and-drop or gesture-based interfaces where release
          position is irrelevant

    :attr:`always_release` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to False.

    .. versionadded:: 1.9.0

    .. versionchanged:: 1.10.0
        The default value changed from True to False.
    """

    def _get_pressed(self):
        """Compute pressed state based on active touches.

        :return: True if any touches are currently active
        """
        return bool(self._active_touches)

    pressed = AliasProperty(_get_pressed, bind=["_active_touches"], cache=True)
    """Read-only boolean indicating if button is currently pressed.

    The button is pressed only when currently touched/clicked. This property
    automatically handles multi-touch scenarios, remaining True as long as at
    least one active touch is on the button.

    Updates automatically as touches are added/removed from ``_active_touches``.

    :attr:`pressed` is an :class:`~kivy.properties.AliasProperty` and defaults
    to False.

    .. versionchanged:: 3.0.0
        Changed from editable BooleanProperty to read-only AliasProperty
    """

    _active_touches = ObjectProperty()

    def __init__(self, **kwargs):
        """Initialize ButtonBehavior mixin.

        Registers button-specific events and initializes touch tracking sets.
        """
        self.register_event_type("on_press")
        self.register_event_type("on_release")
        self.register_event_type("on_cancel")

        # Track touches: active vs cancelled
        self._active_touches = set()
        self._cancelled_touches = set()

    # NOTE: Internal hooks for subclassing
    # ====================================
    # These methods are called internally before dispatching the corresponding
    # public events. They allow subclasses to implement internal state changes
    # (e.g., ToggleButtonBehavior updating its state) separately from
    # user-facing event handlers, maintaining a clean separation between
    # internal logic and external event dispatch.
    # Do NOT call these directly or bind to them - use
    # on_press/on_release/on_cancel events instead.
        if 'min_state_time' not in kwargs:
            self.min_state_time = float(Config.get('graphics',
                                                   'min_state_time'))
        if 'accessible_role' not in kwargs:
            kwargs['accessible_role'] = Role.BUTTON
        super(ButtonBehavior, self).__init__(**kwargs)
        self.__state_event = None
        self.__touch_time = None
        self.fbind('state', self.cancel_event)

    def _do_press(self):
        """Internal hook for subclasses. Called before on_press event dispatch.

        .. note::
            It's not recommended to override this unless subclassing for
            internal state management.
            Use :meth:`on_press` event for application logic instead.
        """
        pass

    def _do_release(self):
        """Internal hook for subclasses. Called before on_release event dispatch.

        .. note::
            It's not recommended to override this unless subclassing for
            internal state management.
            Use :meth:`on_release` event for application logic instead.
        """
        pass

    def _do_cancel(self):
        """Internal hook for subclasses. Called before on_cancel event dispatch.

        .. note::
            It's not recommended to override this unless subclassing for
            internal state management.
            Use :meth:`on_cancel` event for application logic instead.
        """
        pass

    def _add_active_touch(self, touch):
        """Add touch to active tracking and trigger property update.

        :param touch: Touch to add to active set
        """
        self._active_touches = self._active_touches | {touch}

    def _remove_active_touch(self, touch):
        """Remove touch from active tracking and trigger property update.

        :param touch: Touch to remove from active set
        """
        self._active_touches = self._active_touches - {touch}

    def on_touch_down(self, touch):
        """Handle touch down events.

        Implements core press detection:

        1. Test collision with widget bounds
        2. Grab touch if colliding (marks widget as touch owner)
        3. Add to active touches tracking
        4. Dispatch :meth:`on_press` on first touch

        :param touch: :class:`~kivy.input.motionevent.MotionEvent` instance
        :return: True if event was handled (collided with widget)
        """
        # Let parent handle first
        if super().on_touch_down(touch):
            return True

        # Ignore scroll events
        if touch.is_mouse_scrolling:
            return False

        # Only handle touches within bounds
        if not self.collide_point(touch.x, touch.y):
            return False

        # Prevent double-handling
        if self in touch.ud:
            return False

        # Grab touch to track its lifecycle
        touch.grab(self)
        touch.ud[self] = True

        # Check if this is the first touch before adding
        is_first_touch = len(self._active_touches) == 0
        self._add_active_touch(touch)

        # Only dispatch press event on first touch
        if is_first_touch:
            self._do_press()
            self.dispatch("on_press")

        return True

    def on_touch_move(self, touch):
        """Handle touch move events.

        Detects when touch moves outside button bounds during drag and
        triggers cancellation if :attr:`always_release` is False.

        Cancellation flow:
        1. Touch owned by this widget moves outside bounds
        2. Remove from active touches, add to cancelled touches
        3. Dispatch :meth:`on_cancel` if this was the last active touch

        :param touch: :class:`~kivy.input.motionevent.MotionEvent` instance
        :return: True if event was handled
        """
        # We own this touch
        if touch.grab_current is self:
            # Cancel if moved outside and cancellation is enabled
            if (
                not self.always_release
                and not self.collide_point(touch.x, touch.y)
                and touch not in self._cancelled_touches
            ):
                # Move from active to cancelled
                if touch in self._active_touches:
                    self._remove_active_touch(touch)
                    self._cancelled_touches.add(touch)

                    # Dispatch cancel event if this was the last active touch
                    if not self._active_touches:
                        self._do_cancel()
                        self.dispatch("on_cancel")

            return True

        # Let parent handle
        if super().on_touch_move(touch):
            return True

        # We touched this widget before
        return self in touch.ud

    def on_touch_up(self, touch) -> bool:
        """Handle touch up events.

        Implements release detection:

        1. Verify we own this touch
        2. Ungrab touch to release ownership
        3. Remove from active/cancelled tracking
        4. Dispatch :meth:`on_release` if appropriate:
           - Touch wasn't cancelled, AND
           - (Touch ended within bounds OR :attr:`always_release` is True), AND
           - This was the last active touch

        :param touch: :class:`~kivy.input.motionevent.MotionEvent` instance
        :return: True if event was handled
        """
        # Not our touch
        if touch.grab_current is not self:
            return super().on_touch_up(touch)

        # Sanity check
        assert self in touch.ud

        # Release ownership
        touch.ungrab(self)

        # Remove from active tracking
        self._remove_active_touch(touch)

        # Check if this touch was cancelled
        is_cancelled = touch in self._cancelled_touches

        # Dispatch release if not cancelled and conditions met
        if not is_cancelled and (
            self.always_release or self.collide_point(*touch.pos)
        ):
            # Only dispatch release after ALL touches are released
            if not self._active_touches:
                self._do_release()
                self.dispatch("on_release")

        # Cleanup cancelled touch tracking
        self._cancelled_touches.discard(touch)

        return True

    def on_press(self):
        """Event handler called when the button is pressed.

        This event is fired when the first touch down occurs on the button.
        In multi-touch scenarios, only the first touch triggers this event.
        """
        pass

    def on_release(self):
        """Event handler called when the button is released.

        This event is fired when the last active touch is released, and only if:
        - The touch is released within button bounds, OR
        - The `always_release` property is True
        """
        pass

    def on_cancel(self):
        """Event handler called when touch leaves button bounds during drag.

        This event is only fired when `always_release` is False and a touch
        moves outside the button's bounds during a drag operation. It provides
        an opportunity to give visual feedback that the button action has been
        cancelled.

        Use this to restore the button's original appearance or cancel any
        pending actions that would have occurred on release.

        .. versionadded:: 3.0.0
        """
        pass
