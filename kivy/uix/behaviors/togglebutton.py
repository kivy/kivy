"""
ToggleButton Behavior
=====================

The :class:`~kivy.uix.behaviors.togglebutton.ToggleButtonBehavior`
`mixin <https://en.wikipedia.org/wiki/Mixin>`_ class provides toggle button
behavior for Kivy widgets. You can combine this class with other widgets to add
specialized on/off state management with optional radio button grouping.

For an overview of behaviors, please refer to the :mod:`~kivy.uix.behaviors`
documentation.

Examples
--------

Basic toggle with visual feedback::

    from kivy.app import App
    from kivy.lang import Builder
    from kivy.uix.label import Label
    from kivy.uix.behaviors import ToggleButtonBehavior

    class MyToggle(ToggleButtonBehavior, Label):
        Builder.load_string('''
    <MyToggle>:
        canvas.before:
            Color:
                rgb: self.color
                a: 0.25
            Rectangle:
                size: self.size
                pos: self.pos
        ''')

        def on_active(self, instance, value):
            self.color = [0, 1, 0, 1] if value else [1, 1, 1, 1]

    class SampleApp(App):
        def build(self):
            return MyToggle()

    SampleApp().run()

Radio button group behavior::

    from kivy.lang import Builder
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.behaviors import ToggleButtonBehavior


    class MyToggle(ToggleButtonBehavior, Label):
        Builder.load_string('''
    <MyToggle>:
        canvas.before:
            Color:
                rgb: self.color
                a: 0.25
            Rectangle:
                size: self.size
                pos: self.pos
        ''')

        def on_active(self, instance, value):
            self.color = [0, 1, 0, 1] if value else [1, 1, 1, 1]


    class SampleApp(App):
        def build(self):
            layout = BoxLayout()
            for i in range(3):
                btn = MyToggle(
                    text=f"Option {i + 1}",
                    group="options",
                    allow_no_selection=False,
                )
                layout.add_widget(btn)
            return layout


    SampleApp().run()


Scoped groups for reusable components::

    from kivy.lang import Builder
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.behaviors import ToggleButtonBehavior


    class MyToggle(ToggleButtonBehavior, Label):
        Builder.load_string('''
    <MyToggle>:
        canvas.before:
            Color:
                rgb: self.color
                a: 0.25
            Rectangle:
                size: self.size
                pos: self.pos
        ''')

        def on_active(self, instance, value):
            self.color = [0, 1, 0, 1] if value else [1, 1, 1, 1]


    class ToggleRow(BoxLayout):
        '''Reusable component with scoped group.'''

        def __init__(self, label_prefix="Option", **kwargs):
            super().__init__(**kwargs)
            for i in range(3):
                btn = MyToggle(
                    text=f"{label_prefix}, Col {i + 1}",
                    # group=("options"),  # Global, not scoped

                    # Scoped to this row (ToggleRow instance)
                    group=(self, "options"),

                    allow_no_selection=False,
                    active=i == 0,
                )
                self.add_widget(btn)


    class SampleApp(App):
        def build(self):
            layout = BoxLayout(orientation="vertical")
            # Each row has independent "options" group
            layout.add_widget(ToggleRow(label_prefix="Row 1"))
            layout.add_widget(ToggleRow(label_prefix="Row 2"))
            return layout


    SampleApp().run()


See :class:`~kivy.uix.behaviors.ToggleButtonBehavior` for details.
"""

__all__ = ("ToggleButtonBehavior",)

from collections import defaultdict
from weakref import WeakSet

from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    ObjectProperty,
    OptionProperty,
)
from kivy.uix.behaviors.button import ButtonBehavior


class _GroupAccessor:
    """Descriptor that provides unified group access as both instance and class
    method.

    When accessed from an instance, returns widgets in that instance's group.
    When accessed from the class, returns a callable that accepts a group
    identifier.

    This provides a single, intuitive API for accessing group widgets regardless
    of whether you have a widget instance or just a group identifier.
    """

    def __get__(self, instance, owner):
        if instance is None:
            # Called as class method: ToggleButtonBehavior.get_group(group_id)
            return lambda group: self._get_by_identifier(owner, group)
        else:
            # Called as instance method: my_button.get_group()
            return lambda: self._get_by_instance(instance)

    def _get_by_instance(self, instance):
        """Get widgets from instance's current group."""
        owner, name = instance._current_group_key
        return self._get_widgets_from_group(instance.__class__, owner, name)

    def _get_by_identifier(self, cls, group):
        """Get widgets by group identifier."""
        owner, name = cls._parse_group_static(group)
        return self._get_widgets_from_group(cls, owner, name)

    def _get_widgets_from_group(self, cls, owner, name):
        """Helper to retrieve widgets from group storage."""
        if name is None:
            return []
        return list(cls._toggle_groups.get(owner, {}).get(name, []))

from kivy.uix.widget import Role


class ToggleButtonBehavior(ButtonBehavior):
    """Mixin to add toggle button behavior to any Kivy widget.

    This mixin extends :class:`ButtonBehavior` to provide persistent on/off
    state that survives beyond the press/release interaction. It supports
    grouping multiple toggles together for radio button behavior.

    State Management
    ----------------
    Unlike the transient :attr:`pressed` property from ButtonBehavior (which
    is True only during active touch), the :attr:`active` property maintains
    persistent state:

    - **active=True**: Button is in "on" state (persists after release)
    - **active=False**: Button is in "off" state (default)

    The :attr:`active` property can be set programmatically or toggled by
    user interaction. When :attr:`allow_no_selection` is False, attempts to
    deactivate the last active button in a group will be silently rejected.

    Group Behavior
    --------------
    When buttons share a :attr:`group`, they act like radio buttons:

    - Activating one button automatically deactivates others in the group
    - Only one button per group can be active at a time
    - :attr:`allow_no_selection` controls whether all buttons can be deactivated

    **Without group**: Buttons toggle independently
    **With group**: Buttons behave as mutually exclusive options

    Group Scoping
    ~~~~~~~~~~~~~
    Groups can be either global or scoped to a specific widget owner:

    **Global groups** (string)::

        ToggleButton:
            group: "mygroup"  # Shared across entire application

    **Scoped groups** (tuple)::

        ToggleButton:
            group: (root, "mygroup")  # Scoped to 'root' widget

    Scoped groups allow multiple widget hierarchies to use the same group
    name without interference. This is useful when creating reusable
    components with internal toggle groups.

    Example::

        <MyComponent>:
            # These groups won't conflict with other MyComponent instances
            ToggleButton:
                group: (root, "options")
            ToggleButton:
                group: (root, "options")

    Events
    ------
    Inherits all events from ButtonBehavior:
        - :meth:`on_press`: First touch down
        - :meth:`on_release`: All touches released
        - :meth:`on_cancel`: Touch moved outside bounds

    Additional property events:
        - :meth:`on_active`: When active state changes

    .. versionadded:: 1.8.0

    .. versionchanged:: 3.0.0
        - Replaced ``state`` OptionProperty with ``active`` AliasProperty
        - Added backward-compatible ``state`` alias
        - Improved group management with automatic cleanup
        - Added scoped group support via tuple syntax
        - Replaced ``get_widgets(groupname)`` static method with unified
          ``get_group()`` descriptor that works as both instance and class method
    """

    _toggle_groups = defaultdict(lambda: defaultdict(WeakSet))

    group = ObjectProperty(None, allownone=True)
    """Group of the button. If None, no group will be used (button toggles
    independently).

    Accepts two formats:

    - **Hashable value** (string, int, etc.): Global group shared across entire
      application
    - **Tuple (owner, name)**: Scoped group limited to owner's context

    Global groups (any hashable)::

        group: "mygroup"
        group: 42
        group: MyEnum.OPTION_A

    Scoped groups (tuple of any object + hashable name)::

        group: (root, "mygroup")
        group: (self.parent, "options")
        group: (app.current_screen, "filters")

    **Tuple format**: ``(owner, name)``
        - **owner**: Any object to scope the group to (typically a widget).
          Uses object identity, not equality. Can be weakly referenced.
        - **name**: Hashable identifier for the group (string, int, enum, etc.)

    Only one button per group can be active at a time. When a button in a
    group is activated, all other buttons in that group are automatically
    deactivated.

    Scoped groups allow multiple widget instances to use the same group name
    without interference, making it easier to create reusable components.

    Example of reusable component::

        # Multiple instances won't interfere with each other
        <FilterPanel>:
            ToggleButton:
                group: (root, "size")
                text: "Small"
            ToggleButton:
                group: (root, "size")
                text: "Large"

        # Each FilterPanel instance has independent "size" groups
        FilterPanel:
            id: panel1
        FilterPanel:
            id: panel2

    :attr:`group` is a :class:`~kivy.properties.ObjectProperty` and defaults
    to None.

    .. versionchanged:: 3.0.0
        Added support for tuple format to enable scoped groups.
    """

    allow_no_selection = BooleanProperty(True)
    """Specifies whether widgets in a group allow no selection (all deselected).

    - **True (default)**: Clicking active button deactivates it (all buttons off)
    - **False**: At least one button must remain active (radio button behavior)

    When False, attempts to deactivate the last active button (via touch or
    programmatic ``active = False``) are silently rejected.

    Only applies when :attr:`group` is set.

    .. versionadded:: 1.9.0

    :attr:`allow_no_selection` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to True.
    """

    def _get_active(self):
        """Get current active state."""
        return self._active

    def _set_active(self, value):
        """Set the active state with group validation.

        Used as the setter for :attr:`active`. Delegates all logic to
        :meth:`_change_active_state` to keep programmatic and interactive
        changes consistent.

        :param value: Desired active state.
        :type value: bool
        """
        self._change_active_state(value)

    active = AliasProperty(
        _get_active, _set_active, bind=["_active"], cache=True
    )
    """Persistent toggle state of the button.

    - **True**: Button is in "on" state
    - **False**: Button is in "off" state

    Unlike :attr:`pressed` (which is True only during touch), :attr:`active`
    maintains state after release. Can be set programmatically or toggled by
    user interaction.

    When button is in a group, setting active=True automatically deactivates
    other buttons in that group.

    When :attr:`allow_no_selection` is False, attempts to set active=False
    on the last active button in a group are silently rejected.

    :attr:`active` is an :class:`~kivy.properties.AliasProperty` and defaults
    to False.

    .. versionadded:: 3.0.0
    """

    toggle_on = OptionProperty("release", options=["press", "release"])
    """Specifies which :class:`ButtonBehavior` event triggers the toggle state
    change.

    - **"release" (default)** — The state toggles when the button is released.
    - **"press"** — The state toggles immediately when the button is pressed.

    This property allows adjusting when the toggle action occurs, depending on
    the desired interaction style. It can be changed dynamically at runtime,
    and the new behavior takes effect immediately.

    :attr:`toggle_on` is an :class:`~kivy.properties.OptionProperty` and
    accepts either ``"press"`` or ``"release"``. Defaults to ``"release"``.
    """

    _active = BooleanProperty(False)  # Internal storage for active state

    get_group = _GroupAccessor()
    """Get widgets in a group.

    This descriptor works as both an instance method and a class method,
    providing a unified API for accessing group widgets.

    **As instance method** (no arguments):
        Returns all widgets in the same group as this instance, including
        this instance itself.

        Example::

            # Get all widgets in my_button's group
            widgets = my_button.get_group()
            for w in widgets:
                print(w.text)
            del widgets  # Release immediately

    **As class method** (pass group identifier):
        Returns all widgets in the specified group. Useful when you don't
        have a widget instance but know the group identifier.

        Example::

            # Get widgets by global group name
            widgets = ToggleButtonBehavior.get_group("options")

            # Get widgets by scoped group
            widgets = ToggleButtonBehavior.get_group((panel, "filters"))

            # Useful after removing a widget
            my_group = widget.group
            widget.parent.remove_widget(widget)
            remaining = ToggleButtonBehavior.get_group(my_group)

    .. warning::
        Always release the result immediately! Holding references prevents
        garbage collection::

            widgets = button.get_group()
            # use widgets
            del widgets

    .. note::
        List may contain recently deleted widgets that haven't been
        garbage collected yet.

    :return: List of widget instances in the group (empty list if group
             doesn't exist or has no members)

    .. versionadded:: 3.0.0
        Replaces the old ``get_widgets(groupname)`` static method with a
        unified descriptor that works as both instance and class method.
    """

    def __init__(self, **kwargs):
        """Initialize ToggleButtonBehavior mixin.

        Sets up group tracking and binds property listeners.
        """
        self._current_group_key = (None, None)

        # Bind early so initial 'group' value triggers handler
        self.fbind("group", self._handle_group)
        self._previous_group = None
        if 'accessible_role' not in kwargs:
            kwargs['accessible_role'] = Role.TOGGLE

        # Initialize parent behavior
        super().__init__(**kwargs)

    # override ButtonBehavior._do_press hook
    def _do_press(self):
        if self.toggle_on == "press":
            self._handle_toggle_on()

    # override ButtonBehavior._do_release hook
    def _do_release(self):
        if self.toggle_on == "release":
            self._handle_toggle_on()

    def _change_active_state(self, new_value):
        """Internal helper to update the active state with full validation and
        group management.

        This centralizes the logic shared by :meth:`_set_active` and
        :meth:`_handle_toggle_on`.

        Validation rules:
        - Prevents deactivation if :attr:`allow_no_selection` is False and this
          is the last active button in its group.
        - Updates the internal :attr:`_active` property to reflect the new
          state.
        - When activating, automatically deactivates all sibling buttons in the
          same group (global or scoped).

        :param new_value: The desired new state (True for active, False for
        inactive).
        :type new_value: bool
        """
        owner, name = self._current_group_key

        # Block deactivation if this would leave the group with no active members
        if not new_value and not self.allow_no_selection and name:
            for w in self._toggle_groups[owner][name]:
                if w is not self and w.active:
                    break
            else:
                return  # Cancel deactivation (cannot leave group empty)

        # Apply state change
        self._active = new_value

        # When activating, ensure all other buttons in the same group are
        # deactivated
        if new_value and name is not None:
            self._deactivate_group_siblings()

    def _handle_toggle_on(self, *args):
        """Toggle the button state in response to a press or release.

        - Skips toggling if :attr:`allow_no_selection` is False and the button
          is already active.
        - Otherwise, inverts the :attr:`active` state.
        - State validation and group updates are handled by
          :meth:`_change_active_state`.

        Called by :meth:`_do_press` or :meth:`_do_release` depending on
          :attr:`toggle_on`.
        """
        owner, name = self._current_group_key
        if not self.allow_no_selection and name and self.active:
            return

        self._change_active_state(not self.active)

    def _parse_group(self, group):
        """Parse group into (owner, name) tuple.

        Supports two formats:
        - String: Global group → (None, name)
        - Tuple: Scoped group → (owner, name)

        :param group: Group identifier (string, tuple, or None)
        :return: Tuple of (owner, name) or (None, None) if group is None
        :raises ValueError: If tuple format is invalid
        """
        return self._parse_group_static(group)

    @staticmethod
    def _parse_group_static(group):
        """Static version of _parse_group for class method usage.

        Parse group into (owner, name) tuple without requiring instance context.

        :param group: Group identifier (string, tuple, or None)
        :return: Tuple of (owner, name) or (None, None) if group is None
        :raises ValueError: If tuple format is invalid
        """
        if group is None:
            return None, None

        if isinstance(group, tuple):
            if len(group) != 2:
                raise ValueError(
                    f"Group tuple must have exactly 2 elements (owner, name), "
                    f"got {len(group)}"
                )
            owner, name = group
            if name is None:
                raise ValueError(
                    "Group name (second tuple element) cannot be None"
                )
            return owner, name

        return None, group

    def _validate_group_name(self, name):
        """Validate that group name is hashable.

        :param name: Group name to validate
        :raises ValueError: If name is not hashable
        """
        if name is not None:
            try:
                hash(name)
            except TypeError:
                raise ValueError(
                    f"Group name must be hashable, got {type(name).__name__}"
                )

    def _handle_group(self, instance, new_group):
        """Handle group property changes.

        Manages widget registration in group tracking system:
        1. Parses group into (owner, name) tuple
        2. Removes widget from previous group
        3. Registers widget in new group
        4. Updates internal group reference

        Groups use weak references to prevent memory leaks.

        :param instance: This button instance
        :param new_group: New group value (string, tuple, or None)
        """
        owner, name = self._parse_group(new_group)
        self._validate_group_name(name)

        # Remove from previous group
        old_owner, old_name = self._current_group_key
        if old_name is not None:
            self._toggle_groups[old_owner][old_name].discard(self)

            # Cleanup empty groups
            if not self._toggle_groups[old_owner][old_name]:
                del self._toggle_groups[old_owner][old_name]
                # Cleanup empty owner entries
                if not self._toggle_groups[old_owner]:
                    del self._toggle_groups[old_owner]

        # Register in new group
        if name is not None:
            self._toggle_groups[owner][name].add(self)

        self._current_group_key = (owner, name)

        # Revalidate active state in new group
        if self.active and name is not None:
            self._deactivate_group_siblings()

    def _deactivate_group_siblings(self):
        """Deactivate all other buttons in the same group.

        Only affects buttons in the same scoped group (same owner + name).
        """
        owner, name = self._current_group_key
        if name is None:
            return

        for widget in self._toggle_groups[owner][name]:
            if widget is not self and widget.active:
                widget.active = False

    def on_active(self, instance, value):
        """Event handler called when active state changes.

        Override this method to respond to state changes.

        :param instance: This button instance
        :param value: New active state (True/False)
        """
        pass
