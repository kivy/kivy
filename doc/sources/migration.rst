.. _migration:

Migrating from Kivy 2.x.x to Kivy 3.x.x
========================================

Introduction
------------

Kivy 3.x.x introduces several changes and improvements compared to Kivy 2.x.x. This guide will help you migrate your existing Kivy 2.x.x codebase to Kivy 3.x.x.

Renamed modules
---------------

*Migration from kivy.core.audio to kivy.core.audio_output*


In Kivy 3.x.x, the `kivy.core.audio` module has been renamed as `kivy.core.audio_output`. 

To migrate your code, you need to update the import statements in your codebase. For example, if you have the following import statement in your code:

.. code-block:: python

    from kivy.core.audio import SoundLoader

You need to update it to:

.. code-block:: python

    from kivy.core.audio_output import SoundLoader


Removals
--------

*Removal of `.play` property from `kivy.uix.video.Video` and `kivy.uix.videoplayer.VideoPlayer`*

In Kivy 3.x.x, the `.play` property has been removed from the `kivy.uix.video.Video` and `kivy.uix.videoplayer.VideoPlayer` classes.

To migrate your code, you need to update the references to the `.play` property in your codebase. For example, if you have the following code in your Kivy 2.x.x codebase:

.. code-block:: python

    video = Video(source='video.mp4')

    # Play the video
    video.play = True

    # Stop the video
    video.play = False

You need to update it to:

.. code-block:: python

    video = Video(source='video.mp4')

    # Play the video
    video.state = 'play'

    # Stop the video
    video.state = 'stop'

    # Pause the video
    video.state = 'pause'


*Removal of `padding_x` and `padding_y` Properties from `kivy.uix.textinput.TextInput`*

In Kivy 3.x.x the `padding_x` and `padding_y` properties have been **removed** from the `kivy.uix.textinput.TextInput` class. Instead, padding is now managed through the unified `padding` property.

To update your code, replace instances of `padding_x` and `padding_y` with the `padding` property.

The `padding` property accepts a list of values, allowing for more flexible padding configurations:

- `[horizontal, vertical]` — e.g., `[10, 10]`
- `[padding_left, padding_top, padding_right, padding_bottom]` — e.g., `[10, 5, 10, 5]`

For more details on how to use the `padding` property, please refer to the related documentation.

*Removal of `file_encodings` Property from `kivy.uix.filechooser.FileChooserController`*

In Kivy 3.x.x, the `file_encodings` property has been removed from the `kivy.uix.filechooser.FileChooserController` class.

The `file_encodings` property was deprecated and it was kept for backward compatibility, however it was just ignored and not used internally.

To migrate your code, you just need to remove any references to the `file_encodings` property in your codebase.


==============
ButtonBehavior
==============

*Removal of `state`, `min_state_time`, `last_touch` Properties and `trigger_action()` Method*

In Kivy 3.x.x, the `ButtonBehavior` class has been significantly simplified and improved.
The `state` OptionProperty, `min_state_time` NumericProperty, and `last_touch` ObjectProperty
have been **removed**, along with the `trigger_action()` method. A simpler, read-only `pressed`
BooleanProperty is now used to indicate the button's state.

**Migrating from `state` to `pressed`**

The `state` property that could be `'normal'` or `'down'` has been replaced with a boolean
`pressed` property. Note that `pressed` is **read-only** (an AliasProperty), unlike the old
`state` which could be set directly.

.. code-block:: python

    # Kivy 2.x.x
    if button.state == 'down':
        print("Button is pressed")
    
    button.state = 'down'  # Could set state directly
    
    # Kivy 3.x.x
    if button.pressed:
        print("Button is pressed")
    
    # button.pressed = True  # NOT ALLOWED - read-only property

In KV language:

.. code-block:: kv

    # Kivy 2.x.x
    Button:
        color: (1, 0, 0, 1) if self.state == 'down' else (1, 1, 1, 1)
    
    # Kivy 3.x.x
    Button:
        color: (1, 0, 0, 1) if self.pressed else (1, 1, 1, 1)

**Binding to State Changes**

Use the `on_pressed` property event instead of `on_state`:

.. code-block:: python

    # Kivy 2.x.x
    def on_state(self, instance, value):
        if value == 'down':
            print("Pressed")
        else:
            print("Released")
    
    # Kivy 3.x.x
    def on_pressed(self, instance, is_pressed):
        if is_pressed:
            print("Pressed")
        else:
            print("Released")

**Migrating from `min_state_time`**

The `min_state_time` property, which enforced a minimum duration for the 'down' state,
has been removed. If you need similar behavior, you can implement it manually using
`Clock.create_trigger()`:

.. code-block:: python

    from kivy.clock import Clock
    from kivy.uix.behaviors import ButtonBehavior
    from kivy.uix.label import Label
    
    class DelayedButton(ButtonBehavior, Label):
        MIN_STATE_TIME = 0.5  # seconds
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._release_trigger = Clock.create_trigger(
                self._delayed_action,
                self.MIN_STATE_TIME
            )
            self.bind(pressed=self._pressed_changed)
        
        def _pressed_changed(self, instance, is_pressed):
            if is_pressed:
                self._release_trigger.cancel()
            else:
                self._release_trigger()  # schedule delayed action
        
        def _delayed_action(self, dt):
            # Your delayed logic here
            print("Action executed after minimum time")


**Removal of `trigger_action()` Method**

The `trigger_action()` method has been removed. This method was used to programmatically
simulate button presses, but it violated the principle of UI event simulation and wasn't
properly integrated with the touch system.

.. code-block:: python

    # Kivy 2.x.x
    button.trigger_action(duration=0.1)

If you need to programmatically trigger button actions in Kivy 3.x.x, you have two options:

**Option 1: Dispatch events directly (recommended for simple cases)**

Simply dispatch the `on_press` and `on_release` events without simulating the full touch cycle:

.. code-block:: python

    # Kivy 3.x.x - Direct event dispatch
    button.dispatch('on_press')
    # ... your logic ...
    button.dispatch('on_release')

Note that this approach does NOT update the `pressed` property or trigger internal state
changes, as those are tied to actual touch events.

**Option 2: Simulate touch events (for complete button state simulation)**

If you need the button to fully simulate touch behavior (including updating the `pressed`
property), you must simulate actual touch events:

.. code-block:: python

    from kivy.input.motionevent import MotionEvent
    
    class MyButton(ButtonBehavior, Label):
        def simulate_press(self, duration=0.1):
            """Simulate a complete button press with touch events."""
            # Create a mock touch event
            touch = MotionEvent('mock', 0, {
                'x': self.center_x,
                'y': self.center_y,
                'pos': (self.center_x, self.center_y)
            })
            
            # Simulate touch down
            self.on_touch_down(touch)
            
            # Simulate touch up after duration
            def release_touch(dt):
                self.on_touch_up(touch)
            
            if duration > 0:
                Clock.schedule_once(release_touch, duration)
            else:
                release_touch(0)


Or create a helper method in your custom button class:

.. code-block:: python

    from kivy.clock import Clock
    from kivy.uix.behaviors import ButtonBehavior
    from kivy.uix.label import Label
    
    class MyButton(ButtonBehavior, Label):
        def trigger_action(self, duration=0.1):
            """Simulate button press/release."""
            self._do_press()
            self.dispatch('on_press')
            
            def trigger_release(dt):
                self._do_release()
                self.dispatch('on_release')
            
            if not duration:
                trigger_release(0)
            else:
                Clock.schedule_once(trigger_release, duration)

**Removal of `last_touch` Property**

The `last_touch` ObjectProperty has been **removed**. If you need to track touches,
implement your own tracking:

.. code-block:: python

    # Kivy 2.x.x
    class MyButton(ButtonBehavior, Label):
        def on_press(self):
            print(f"Touch at: {self.last_touch.pos}")
    
    # Kivy 3.x.x
    class MyButton(ButtonBehavior, Label):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.last_touch = None
        
        def on_touch_down(self, touch):
            result = super().on_touch_down(touch)
            if result and self in touch.ud:
                self.last_touch = touch
            return result
        
        def on_press(self):
            if self.last_touch:
                print(f"Touch at: {self.last_touch.pos}")

**Improved Multi-Touch Behavior**

The `on_release` event behavior has changed for multi-touch scenarios:

- **Kivy 2.x.x**: `on_release` fires when **the first touch** is released (even if other touches are still active)
- **Kivy 3.x.x**: `on_release` fires only after **all active touches** are released

.. code-block:: python

    # Example: Multi-touch behavior difference
    class MyButton(ButtonBehavior, Label):
        def on_release(self):
            print("Button released")
    
    # Scenario: User presses button with 3 fingers, then lifts them one by one
    # Kivy 2.x.x: "Button released" prints when the FIRST finger is lifted
    # Kivy 3.x.x: "Button released" prints only when ALL 3 fingers are lifted

If you need the old behavior (release on first touch up), override `on_touch_up`:

.. code-block:: python

    class LegacyButton(ButtonBehavior, Label):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._first_touch_released = False
        
        def on_touch_down(self, touch):
            result = super().on_touch_down(touch)
            if result:
                self._first_touch_released = False
            return result
        
        def on_touch_up(self, touch):
            if touch.grab_current is self and not self._first_touch_released:
                self._first_touch_released = True
                self._do_release()
                self.dispatch('on_release')
            return super().on_touch_up(touch)

**New `on_cancel` Event**

A new event `on_cancel` is now dispatched when a touch moves outside the button bounds
during a drag operation. This only occurs when `always_release=False` (the default).

.. code-block:: python

    class MyButton(ButtonBehavior, Label):
        def on_press(self):
            self.color = (1, 0, 0, 1)  # Red when pressed
        
        def on_release(self):
            self.color = (0, 1, 0, 1)  # Green on successful release
            print("Button action executed")
        
        def on_cancel(self):
            self.color = (1, 1, 1, 1)  # White when cancelled
            print("Button action cancelled")

This event allows you to provide visual feedback when the user drags their finger/pointer
outside the button, indicating the action will not be executed.

**Changed `always_release` Behavior**

The behavior when `always_release=False` (default) has been improved:

**Kivy 2.x.x**: When touch moved outside bounds, `on_release` didn't fire. However, if the
user moved the touch back inside the button bounds before releasing, `on_release` would
fire normally. This could cause unexpected side effects.

**Kivy 3.x.x**: When touch moves outside bounds during drag:
- `on_cancel` event fires immediately (NEW)
- Touch is marked as cancelled permanently
- `on_release` will NOT fire, even if touch moves back inside before release
- Provides explicit feedback about cancellation
- Now, canceled `on_release` are explicitly canceled `on_release`(`on_cancel`).

.. code-block:: python

    # Example: Standard button behavior (always_release=False)
    class StandardButton(ButtonBehavior, Label):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.always_release = False  # Default, but explicit here
        
        def on_press(self):
            print("Action started")
            self.text = "Release here to confirm"
        
        def on_release(self):
            print("Action confirmed!")
            self.text = "Confirmed"
        
        def on_cancel(self):
            print("Action cancelled")
            self.text = "Cancelled - press again"

When `always_release=True`, the behavior remains the same - `on_release` always fires
and `on_cancel` never fires:

.. code-block:: python

    # Example: Always release (drag-and-drop style)
    class DragButton(ButtonBehavior, Label):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.always_release = True  # Release fires anywhere
        
        def on_release(self):
            print("Released - on_cancel never fires")

**Internal Hooks for Subclassing**

The methods `_do_press()`, `_do_release()`, and `_do_cancel()` are now documented as
internal hooks for subclasses (like `ToggleButtonBehavior`). These are called before
the corresponding public events are dispatched.

.. note::
    Avoid using these methods, they are for internal state management in subclasses. Application code
    should use the `on_press`, `on_release`, and `on_cancel` events instead.

.. code-block:: python

    class CustomButton(ButtonBehavior, Label):
        def _do_press(self):
            # Internal state changes before event dispatch (for internal use only)
            super()._do_press()
            self._internal_state = "pressing"
        
        def on_press(self):
            # Public event handler for application logic
            print("Button pressed - use this for your logic")

**Summary of Breaking Changes**

+-------------------------+---------------------------+----------------------------------------+
| Removed/Changed         | Kivy 2.x.x                | Kivy 3.x.x                             |
+=========================+===========================+========================================+
| `state` property        | `'normal'` or `'down'`    | Removed - use `pressed` (read-only)    |
+-------------------------+---------------------------+----------------------------------------+
| `min_state_time`        | NumericProperty (0.035)   | Removed - implement manually           |
+-------------------------+---------------------------+----------------------------------------+
| `last_touch`            | ObjectProperty            | Removed - track manually               |
+-------------------------+---------------------------+----------------------------------------+
| `trigger_action()`      | Method available          | Removed - dispatch events manually     |
+-------------------------+---------------------------+----------------------------------------+
| `on_release` behavior   | Fires on first touch up   | Fires after all touches released       |
+-------------------------+---------------------------+----------------------------------------+
| `on_cancel` event       | Not available             | **New** - fires on drag outside bounds |
+-------------------------+---------------------------+----------------------------------------+
| `always_release=False`  | Silent non-release        | Explicit `on_cancel` event             |
+-------------------------+---------------------------+----------------------------------------+
| Internal hooks          | Undocumented              | Documented `_do_*()` methods           |
+-------------------------+---------------------------+----------------------------------------+

====================
ToggleButtonBehavior
====================

*Replacement of `state` with `active` and Major API Improvements*

In Kivy 3.x.x, `ToggleButtonBehavior` has undergone significant improvements and changes.
The most notable change is replacing the `state` OptionProperty with an `active` boolean property (`AliasProperty`),
along with new features like scoped groups and the `toggle_on` property.

**Migrating from `state` to `active`**

The `state` property (`'normal'` or `'down'`) has been replaced with a boolean `active` property:

.. code-block:: python

    # Kivy 2.x.x
    if toggle.state == 'down':
        print("Toggle is active")
        toggle.state = 'normal'  # Deactivate
    
    # Kivy 3.x.x
    if toggle.active:
        print("Toggle is active")
        toggle.active = False  # Deactivate

In KV language:

.. code-block:: kv

    # Kivy 2.x.x
    ToggleButton:
        text: "ON" if self.state == 'down' else "OFF"
        color: (0, 1, 0, 1) if self.state == 'down' else (1, 1, 1, 1)
    
    # Kivy 3.x.x
    ToggleButton:
        text: "ON" if self.active else "OFF"
        color: (0, 1, 0, 1) if self.active else (1, 1, 1, 1)

**New `on_active` Event**

Replace `on_state` bindings with `on_active`:

.. code-block:: python

    # Kivy 2.x.x
    class MyToggle(ToggleButtonBehavior, Label):
        def on_state(self, instance, value):
            if value == 'down':
                print("Activated")
                self.background_color = (0, 1, 0, 1)
            else:
                print("Deactivated")
                self.background_color = (1, 1, 1, 1)
    
    # Kivy 3.x.x
    class MyToggle(ToggleButtonBehavior, Label):
        def on_active(self, instance, value):
            if value:
                print("Activated")
                self.color = (0, 1, 0, 1)
            else:
                print("Deactivated")
                self.color = (1, 1, 1, 1)

In KV language, bind to property changes:

.. code-block:: kv

    # Kivy 2.x.x
    <MyToggle@ToggleButton>:
        on_state: app.handle_toggle(self, self.state)
    
    # Kivy 3.x.x
    <MyToggle@ToggleButton>:
        on_active: app.handle_toggle(self, self.active)

**New `toggle_on` Property**

A new `toggle_on` property controls when the toggle state changes - either on press
or on release (default):

.. code-block:: python

    # Kivy 3.x.x - Toggle immediately on press
    ToggleButton:
        toggle_on: 'press'
    
    # Kivy 3.x.x - Toggle on release (default)
    ToggleButton:
        toggle_on: 'release'

This is useful when you want instant visual feedback:

.. code-block:: python

    from kivy.uix.behaviors import ToggleButtonBehavior
    from kivy.uix.label import Label
    
    class InstantToggle(ToggleButtonBehavior, Label):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.toggle_on = 'press'  # Toggle immediately
        
        def on_active(self, instance, value):
            self.text = "ON" if value else "OFF"

**Scoped Groups (New Tuple Syntax)**

Groups can now be scoped to specific widget owners using tuple syntax. This prevents
conflicts when creating reusable components:

.. code-block:: python

    # Kivy 2.x.x - Only global groups (string)
    ToggleButton:
        group: 'options'  # Global across entire application
    
    # Kivy 3.x.x - Global groups (still supported)
    ToggleButton:
        group: 'options'
    
    # Kivy 3.x.x - Scoped groups (NEW)
    ToggleButton:
        group: (root, 'options')  # Scoped to 'root' widget

**Scoped Group Format**: ``(owner, name)``

- **owner**: Any object to scope the group to (typically a widget)
- **name**: Hashable identifier (string, int, enum, etc.)

Example of reusable component with scoped groups:

.. code-block:: python

    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.togglebutton import ToggleButton
    
    class FilterPanel(BoxLayout):
        """Reusable panel with independent toggle groups."""
        
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            
            # Each FilterPanel instance has its own "size" group
            for size in ["Small", "Medium", "Large"]:
                btn = ToggleButton(
                    text=size,
                    group=(self, "size"),  # Scoped to this FilterPanel instance
                    allow_no_selection=False
                )
                self.add_widget(btn)
    
    # Multiple panels won't interfere with each other
    panel1 = FilterPanel()  # Has independent "size" group
    panel2 = FilterPanel()  # Has independent "size" group

In KV language:

.. code-block:: kv

    <FilterPanel@BoxLayout>:
        ToggleButton:
            text: "Small"
            group: (root, "size")  # Scoped to FilterPanel instance
        ToggleButton:
            text: "Medium"
            group: (root, "size")
        ToggleButton:
            text: "Large"
            group: (root, "size")
    
    # Each instance has independent groups
    BoxLayout:
        FilterPanel:  # Independent "size" group
        FilterPanel:  # Independent "size" group

**When to Use Scoped vs Global Groups**

Use **global groups** (string) when:
- You want all toggles across the app to share the same group
- Building simple single-instance interfaces

Use **scoped groups** (tuple) when:
- Creating reusable components with internal toggle groups
- Multiple instances of the same component shouldn't interfere
- Building complex layouts with nested toggle groups

**Method Changes: `get_widgets()` → `get_group()`**

The static method `get_widgets(groupname)` has been replaced with an instance method
`get_group()`:

.. code-block:: python

    # Kivy 2.x.x - Static method
    widgets = ToggleButtonBehavior.get_widgets('mygroup')
    for widget in widgets:
        print(widget.text)
    del widgets  # Always delete to prevent memory leaks
    
    # Kivy 3.x.x - Instance method
    widgets = my_toggle_button.get_group()
    for widget in widgets:
        print(widget.text)
    del widgets  # Still recommended to delete to prevent memory leaks

The new `get_group()` method:
- Returns widgets in the same group as the calling instance
- Works with both global and scoped groups automatically
- Includes the calling widget in the returned list

.. code-block:: python

    # Example usage
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.togglebutton import ToggleButton
    
    class MyApp(App):
        def build(self):
            layout = BoxLayout()
            
            btn1 = ToggleButton(text="Option 1", group="options")
            btn2 = ToggleButton(text="Option 2", group="options")
            btn3 = ToggleButton(text="Option 3", group="options")
            
            layout.add_widget(btn1)
            layout.add_widget(btn2)
            layout.add_widget(btn3)
            
            # Get all widgets in btn1's group
            group_widgets = btn1.get_group()
            print(f"Group has {len(group_widgets)} widgets")  # Prints: 3
            del group_widgets
            
            return layout

**Removal of `_clear_groups()` and `_release_group()`**

The static method `_clear_groups()` and instance method `_release_group()` have been
removed. Group management is now handled automatically through weak references.

.. code-block:: python

    # Kivy 2.x.x - Manual group management
    class MyToggle(ToggleButtonBehavior, Label):
        def custom_release(self):
            self._release_group(self)
            self.state = 'normal'
    
    # Kivy 3.x.x - Automatic group management
    class MyToggle(ToggleButtonBehavior, Label):
        def custom_release(self):
            self.active = False  # Automatically manages group

**Improved Group Cleanup**

Group management now uses `WeakSet` for automatic cleanup when widgets are deleted.
You no longer need to manually clean up groups:

.. code-block:: python

    # Kivy 2.x.x - Potential memory leaks if not careful
    toggle = ToggleButton(group='mygroup')
    del toggle  # Weak reference might linger
    
    # Kivy 3.x.x - Automatic cleanup
    toggle = ToggleButton(group='mygroup')
    del toggle  # Automatically removed from group via WeakSet


**Summary of Breaking Changes**

+---------------------------+---------------------------+----------------------------------------+
| Removed/Changed           | Kivy 2.x.x                | Kivy 3.x.x                             |
+===========================+===========================+========================================+
| `state` property          | `'normal'` or `'down'`    | Replaced with `active` (bool)          |
+---------------------------+---------------------------+----------------------------------------+
| `on_state` event          | Fired on state change     | Replaced with `on_active`              |
+---------------------------+---------------------------+----------------------------------------+
| `toggle_on` property      | Not available             | **New** - 'press' or 'release'         |
+---------------------------+---------------------------+----------------------------------------+
| Group syntax              | String only               | String or (owner, name) tuple          |
+---------------------------+---------------------------+----------------------------------------+
| `get_widgets(group)`      | Static method             | Replaced with `get_group()` instance   |
+---------------------------+---------------------------+----------------------------------------+
| `_clear_groups()`         | Static method             | Removed - automatic cleanup            |
+---------------------------+---------------------------+----------------------------------------+
| `_release_group()`        | Instance method           | Removed - automatic via `active`       |
+---------------------------+---------------------------+----------------------------------------+
| Group management          | Manual weak references    | Automatic with `WeakSet`               |
+---------------------------+---------------------------+----------------------------------------+
```