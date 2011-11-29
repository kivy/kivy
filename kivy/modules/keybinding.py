'''
Keybinding
==========

This module force the mapping of some keys to functions:

* F11: Rotate the Window from 0, 90, 180, 270
* F12: Take a screenshot

'''

__all__ = ('start', 'stop')


def _on_keyboard_handler(instance, key, scancode, unicode, modifier):
    if key == 293: # F12
        instance.screenshot()
    elif key == 292: # F11
        instance.rotation += 90


def start(win, ctx):
    win.bind(on_keyboard=_on_keyboard_handler)


def stop(win, ctx):
    win.unbind(on_keyboard=_on_keyboard_handler)
