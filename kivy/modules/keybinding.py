'''
Keybinding
==========

Activate this module to map some keys to useful functions

- F12: screenshot

'''

__all__ = ('start', 'stop')

def _on_keyboard_handler(instance, key, scancode, unicode):
    if key == 293: # F12
        instance.screenshot()

def start(win, ctx):
    win.bind(on_keyboard=_on_keyboard_handler)

def stop(win, ctx):
    win.unbind(on_keyboard=_on_keyboard_handler)
