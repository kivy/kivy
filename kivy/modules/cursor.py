'''
Touchring
=========

Shows rings around every touch on the surface / screen. You can use this module
to check that you don't have any calibration issues with touches.

Configuration
-------------

:Parameters:
    `image`: str, defaults to '<kivy>/data/images/ring.png'
        Filename of the image to use.
    `scale`: float, defaults to 1.
        Scale of the image.
    `alpha`: float, defaults to 1.
        Opacity of the image.
    `show_cursor`: boolean, defaults to False
        .. versionadded:: 1.8.0
    `cursor_texture`: str, defaults to
        'data/images/cursor.png' Image used to
        represent the cursor if displayed
        .. versionadded:: 1.8.0
    `cursor_size`: tuple, defaults to (40, 40)
        Apparent size of the mouse cursor, if displayed, (None,None) value
        will keep its real size.
        .. versionadded:: 1.8.0
    `cursor_offset`: tuple, defaults to (None, None)
        Offset of the texture image. The default value will align the
        top-left corner of the image to the mouse pos.
        .. versionadded:: 1.8.0

Example
-------

In your configuration (`~/.kivy/config.ini`), you can add something like
this::

    [modules]
    touchring = image=mypointer.png,scale=.3,alpha=.7

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
    print "move"
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
