'''
Keybinding
==========

This module force the mapping of some keys to functions:

* F11: Rotate the Window from 0, 90, 180, 270
* Shift + F11: Switches between portrait and landscape on PC
* F12: Take a screenshot

Note: this don't work if the application requires keyboard before.

'''

from kivy.utils import platform

__all__ = ('start', 'stop')


def _on_keyboard_handler(instance, key, scancode, codepoint, modifiers):
    if key == 293 and modifiers == []:  # F12
        instance.screenshot()
    elif key == 292 and modifiers == []:  # F11
        instance.rotation += 90
    elif key == 292 and modifiers == ['shift']:  # Shift + F11
        if platform() in ('win', 'linux', 'macosx'):
            instance.rotation = 0
            w, h = instance.size
            w, h = h, w
            instance.size = (w, h)


def start(win, ctx):
    win.bind(on_keyboard=_on_keyboard_handler)


def stop(win, ctx):
    win.unbind(on_keyboard=_on_keyboard_handler)
