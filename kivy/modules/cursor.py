'''
Cursor
=========

Displays an artistic cursor texture pointing at the position of the mouse cursor. This is practical for use with the egl_rpi window that is drawn right into the framebuffer and has no cursor by default.

Configuration
-------------

:Parameters:
    `cursor_size`: tuple, defaults to (40, 40)
        Apparent size of the mouse cursor, if displayed, (None,None) value
        will keep its real size.
        .. versionadded:: 1.9.0
    `cursor_offset`: tuple, defaults to (None, None)
        Offset of the texture image. The default value will align the
        top-left corner of the image to the mouse pos.
        .. versionadded:: 1.9.0

Example
-------

In your configuration (`~/.kivy/config.ini`), you can add something like
this::

    [modules]
    cursor = cursor_size=(20,20),cursor_offset=(0,0)
'''

__all__ = ('start', 'stop')

from kivy.core.image import Image
from kivy.graphics import Color, Rectangle
from kivy import kivy_data_dir
from os.path import join

cursor_texture = None
cursor_offset = (0, 0)
cursor_size = (20, 20)



def _mouse_move(win, pos, *args):
    if hasattr(win, '_cursor'):
        c = win._cursor
    else:
        with win.canvas.after:            
            Color(1, 1, 1, 1, mode='rgba')
            win._cursor = c = Rectangle(texture=cursor_texture,
                                        size=cursor_size)

    c.pos = pos[0] + cursor_offset[0], pos[1] -cursor_size[1] + cursor_offset[1]


def start(win, ctx):
    # XXX use ctx !
    global cursor_size, cursor_texture, cursor_offset

    cursor_texture = Image(join(kivy_data_dir, 'images', 'cursor.png')).texture
    cursor_size = ctx.config.get('cursor_size', cursor_size)
    if isinstance(cursor_size, str):
        cursor_size = [int(x) for x in cursor_size.split('x')]

    cursor_offset = ctx.config.get('cursor_offset', (0, 0))
    if isinstance(cursor_offset, str):
        cursor_offset = [int(x) for x in cursor_offset.split('x')]

    win.bind(mouse_pos=_mouse_move)


def stop(win, ctx):
    win.unbind(mouse_pos=_mouse_move)
