"""
Button Behavior
===============

The :class:`~kivy.uix.behaviors.button.ButtonBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class provides
:class:`~kivy.uix.button.Button` behavior. You can combine this class with
other widgets, such as an :class:`~kivy.uix.image.Image`, to provide
alternative buttons that preserve Kivy button behavior.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

Example
-------

The following example adds button behavior to an image to make a checkbox that
behaves like a button::

    from kivy.app import App
    from kivy.uix.image import Image
    from kivy.uix.behaviors import ButtonBehavior


    class MyButton(ButtonBehavior, Image):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.source = 'atlas://data/images/defaulttheme/checkbox_off'

        def on_press(self):
            self.source = 'atlas://data/images/defaulttheme/checkbox_on'

        def on_release(self):
            self.source = 'atlas://data/images/defaulttheme/checkbox_off'


    class SampleApp(App):
        def build(self):
            return MyButton()


    SampleApp().run()

See :class:`~kivy.uix.behaviors.ButtonBehavior` for details.
"""

__all__ = ("ButtonBehavior",)

from kivy.properties import BooleanProperty


class ButtonBehavior:
    """
    This `mixin <https://en.wikipedia.org/wiki/Mixin>`_ class provides
    :class:`~kivy.uix.button.Button` behavior. Please see the
    :mod:`button behaviors module <kivy.uix.behaviors.button>` documentation
    for more information.

    The ButtonBehavior mixin handles multi-touch support automatically,
    managing multiple simultaneous touches and their lifecycle. The button
    state transitions based on active touches and user interaction.

    :Events:
        `on_press`
            Fired when the button is pressed (first touch down).

        `on_release`
            Fired when the button is released (i.e., the touch or click that
            pressed the button is released).
            This event is dispatched **only after all active touches**
            registered on the button are released. For example, if the user
            presses the button and then touches it again with another finger,
            the event will wait until **all touches** are released before
            dispatching `on_release`.

            - If `always_release = False`, this event is fired **only** if the
            touch is released within the button bounds.
            - If `always_release = True`, the event is fired **whenever** the
            touch is released, regardless of position.

            .. note::
                This event is not fired after `on_cancel` has been dispatched.

        `on_cancel`
            Fired when a touch moves outside the button bounds during a drag
            (on touch move), but only if `always_release` is False.
            For example, it can be used to provide visual feedback when a button
            action is canceled.

            .. versionadded:: 3.0.0

    Example Usage::

        # Basic press/release handling
        class MyButton(ButtonBehavior, Label):
            def on_press(self):
                print("Button pressed")

            def on_release(self):
                print("Button released")

            def on_cancel(self):
                print("Button action cancelled")

    .. versionchanged:: 3.0.0
        - Replaced `state` OptionProperty with `pressed` BooleanProperty
        - Added `on_cancel` event
        - Improved multi-touch handling
    """

    pressed = BooleanProperty(False)
    """Indicates whether the button is currently pressed.

    The button is pressed only when currently touched/clicked,
    otherwise it is not pressed. This property automatically handles
    multi-touch scenarios, remaining True as long as at least one
    active touch is on the button.

    :attr:`pressed` is a :class:`~kivy.properties.BooleanProperty` and 
    defaults to False.
    """

    always_release = BooleanProperty(False)
    """Determines whether the widget fires an `on_release` event
    if the touch_up occurs outside the widget bounds.

    When False (default):
        - `on_release` only fires if touch ends within button bounds
        - `on_cancel` fires when touch moves outside bounds during drag (touch
            move)
        - Provides standard button behavior with cancellation

    When True:
        - `on_release` always fires regardless of touch position
        - `on_cancel` never fires
        - Useful for drag-and-drop or gesture-based interfaces

    .. versionadded:: 1.9.0

    .. versionchanged:: 1.10.0
        The default value is now False.

    :attr:`always_release` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to `False`.
    """

    def __init__(self, **kwargs):
        self.register_event_type("on_press")
        self.register_event_type("on_release")
        self.register_event_type("on_cancel")
        self._active_touches = set()
        self._cancelled_touches = set()
        super().__init__(**kwargs)

    def _do_press(self):
        """Internal method to set pressed state to True"""
        self.pressed = True

    def _do_release(self, *args):
        """Internal method to set pressed state to False"""
        if not self._active_touches:
            self.pressed = False

    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            return True
        if touch.is_mouse_scrolling:
            return False
        if not self.collide_point(touch.x, touch.y):
            return False
        if self in touch.ud:
            return False

        touch.grab(self)
        touch.ud[self] = True

        # Check if this is the first touch before adding
        is_first = len(self._active_touches) == 0
        self._active_touches.add(touch)

        if is_first:
            self._do_press()
            self.dispatch("on_press")

        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if (
                not self.always_release  # Only cancel if always_release is False
                and not self.collide_point(touch.x, touch.y)
                and touch not in self._cancelled_touches
            ):
                if touch in self._active_touches:
                    self._active_touches.discard(touch)
                    self._cancelled_touches.add(touch)

                    if not self._active_touches:
                        self.dispatch("on_cancel")
                        self._do_release()
            return True

        if super().on_touch_move(touch):
            return True
        return self in touch.ud

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)

        assert self in touch.ud
        touch.ungrab(self)

        self._active_touches.discard(touch)

        is_cancelled = touch in self._cancelled_touches

        if not is_cancelled and (
            self.always_release or self.collide_point(*touch.pos)
        ):
            if not self._active_touches:
                self.dispatch("on_release")
                self._do_release()
        else:
            self._do_release()

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
