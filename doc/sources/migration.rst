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

*Removal of `state` and `min_state_time` Properties from `kivy.uix.behaviors.button.ButtonBehavior`*

In Kivy 3.x.x, the `state` OptionProperty and `min_state_time` NumericProperty have been
**removed** from the `kivy.uix.behaviors.button.ButtonBehavior` class. Instead, a simpler `pressed`
BooleanProperty is now used to indicate the button's state.

**Migrating from `state` to `pressed`**

To update your code, replace references to the `state` property with the `pressed` property:

.. code-block:: python

    # Kivy 2.x.x
    if button.state == 'down':
        print("Button is pressed")
    
    # Kivy 3.x.x
    if button.pressed:
        print("Button is pressed")

In KV language:

.. code-block::

    # Kivy 2.x.x
    Button:
        color: (1, 0, 0, 1) if self.state == 'down' else (1, 1, 1, 1)
    
    # Kivy 3.x.x
    Button:
        color: (1, 0, 0, 1) if self.pressed else (1, 1, 1, 1)

**Migrating from `min_state_time`**

The `min_state_time` property, which enforced a minimum duration for the 'down' state,
has been removed. If you need similar behavior, you can implement it manually using `Clock.create_trigger()`:

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
            print("Action executed after minimum time (MIN_STATE_TIME)")


**Removal of `trigger_action()` Method**

The `trigger_action()` method has also been removed. If you need to programmatically
simulate button presses, you can dispatch the events directly:

.. code-block:: python

    # Kivy 2.x.x
    button.trigger_action(duration=0.1)
    
    # Kivy 3.x.x
    button.pressed = True
    button.dispatch('on_press')
    button.pressed = False
    button.dispatch('on_release')

Or create a helper method in your custom button class:

.. code-block:: python

    class MyButton(ButtonBehavior, Label):

        def trigger_action(self, duration=0.1):
            def trigger_release(dt):
                self._do_release()
                self.dispatch('on_release')

            self._do_press()
            self.dispatch('on_press')

            if not duration:
                trigger_release(0)
            else:
                Clock.schedule_once(trigger_release, duration)


**Removal of `last_touch` Property**

The `last_touch` ObjectProperty has been **removed**. If you need to track touches, implement your own tracking:

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


**Improved Multi-Touch Behavior**

The `on_release` event behavior has changed for multi-touch scenarios:

- **Kivy 2.x.x**: `on_release` fires when the **first touch** is released (even if other touches are still active)
- **Kivy 3.x.x**: `on_release` fires only after **all active touches** are released

.. code-block:: python

    # Example: Multi-touch behavior difference
    class MyButton(ButtonBehavior, Label):
        def on_release(self):
            print("Button released")
    
    # Scenario: User presses button with 3 fingers
    # Kivy 2.x.x: "Button released" prints when ANY finger is lifted
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
                self.dispatch('on_release')
            return super().on_touch_up(touch)


**Summary of Breaking Changes**

+-------------------------+---------------------------+----------------------------------------+
| Removed/Changed         | Kivy 2.x.x                | Kivy 3.x.x                             |
+=========================+===========================+========================================+
| `state` property        | `'normal'` or `'down'`    | Removed - use `pressed` (bool)         |
+-------------------------+---------------------------+----------------------------------------+
| `min_state_time`        | NumericProperty (0.035)   | Removed - implement manually           |
+-------------------------+---------------------------+----------------------------------------+
| `last_touch`            | ObjectProperty            | Removed - track manually               |
+-------------------------+---------------------------+----------------------------------------+
| `trigger_action()`      | Method available          | Removed - dispatch events manually     |
+-------------------------+---------------------------+----------------------------------------+
| `on_release` behavior   | Fires per touch           | Fires after all touches released       |
+-------------------------+---------------------------+----------------------------------------+
| `on_cancel` event       | Not available             | **New** - fires on drag outside bounds |
+-------------------------+---------------------------+----------------------------------------+
