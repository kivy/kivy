'''Keybinding
==========

This module forces the mapping of some keys to functions:

* F11: Rotate the Window through 0, 90, 180 and 270 degrees
* Shift + F11: Switches between portrait and landscape on desktops
* F12: Take a screenshot

Note: this does't work if the application requests the keyboard beforehand.

Usage
-----

For normal module usage, please see the :mod:`~kivy.modules` documentation.

The Keybinding module, however, can also be imported and used just
like a normal python module. This has the added advantage of being
able to activate and deactivate the module programmatically::

    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.modules import keybinding
    from kivy.core.window import Window

    class Demo(App):

        def build(self):
            button = Button(text="Hello")
            keybinding.start(Window, button)
            return button

    Demo().run()

To remove the Keybinding, you can do the following::

    Keybinding.stop(Window, button)

'''

from kivy.utils import platform

__all__ = ('start', 'stop')


def _on_keyboard_handler(instance, key, scancode, codepoint, modifiers):
    if key == 293 and modifiers == []:  # F12
        instance.screenshot()
    elif key == 292 and modifiers == []:  # F11
        instance.rotation += 90
    elif key == 292 and modifiers == ['shift']:  # Shift + F11
        if platform in ('win', 'linux', 'macosx'):
            instance.rotation = 0
            w, h = instance.size
            w, h = h, w
            instance.size = (w, h)


def start(win, ctx):
    win.bind(on_keyboard=_on_keyboard_handler)


def stop(win, ctx):
    win.unbind(on_keyboard=_on_keyboard_handler)
