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
    `cursor_image`: str, defaults to
        'atlas://data/images/defaulttheme/slider_cursor' Image used to
        represent the cursor if displayed

        .. versionadded:: 1.8.0
    `cursor_size`: tuple, defaults to (None, None)
        Apparent size of the mouse cursor, if displayed, default value
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
from kivy.logger import Logger

pointer_image = None
pointer_scale = 1.0
pointer_alpha = 0.7
cursor_image = ''
cursor_offset = (0, 0)
cursor_size = (None, None)


def _touch_down(win, touch):
    ud = touch.ud
    touch.scale_for_screen(win.width, win.height)
    with win.canvas.after:
        ud['tr.color'] = Color(1, 1, 1, pointer_alpha)
        iw, ih = pointer_image.size
        ud['tr.rect'] = Rectangle(
            pos=(
                touch.x - (pointer_image.width / 2. * pointer_scale),
                touch.y - (pointer_image.height / 2. * pointer_scale)),
            size=(iw * pointer_scale, ih * pointer_scale),
            texture=pointer_image.texture)

    if not ud.get('tr.grab', False):
        ud['tr.grab'] = True
        touch.grab(win)


def _touch_move(win, touch):
    ud = touch.ud
    ud['tr.rect'].pos = (
        touch.x - (pointer_image.width / 2. * pointer_scale),
        touch.y - (pointer_image.height / 2. * pointer_scale))


def _touch_up(win, touch):
    if touch.grab_current is win:
        ud = touch.ud
        win.canvas.after.remove(ud['tr.color'])
        win.canvas.after.remove(ud['tr.rect'])

        if ud.get('tr.grab') is True:
            touch.ungrab(win)
            ud['tr.grab'] = False


def _mouse_move(win, pos, *args):
    global cursor_size
    if hasattr(win, '_cursor'):
        c = win._cursor
    else:
        with win.canvas.after:
            img = Image(cursor_image)
            Color(1, 1, 1, 1, mode='rgba')
            size = (
                cursor_size[0] or img.texture.size[0],
                cursor_size[1] or img.texture.size[1]
            )
            print(size)
            win._cursor = c = Rectangle(texture=img.texture,
                                        size=size)

    c.pos = pos[0] + cursor_offset[0], pos[1] - c.size[1] + cursor_offset[1]


def start(win, ctx):
    # XXX use ctx !
    global pointer_image, pointer_scale, pointer_alpha, cursor_size,\
        cursor_image, cursor_offset
    pointer_fn = ctx.config.get('image',
                                'atlas://data/images/defaulttheme/ring')
    pointer_scale = float(ctx.config.get('scale', 1.0))
    pointer_alpha = float(ctx.config.get('alpha', 1.0))
    pointer_image = Image(pointer_fn)
    cursor_image = ctx.config.get(
        'cursor_image',
        'atlas://data/images/defaulttheme/slider_cursor')
    cursor_size = ctx.config.get('cursor_size', (None, None))
    if isinstance(cursor_size, str):
        cursor_size = [int(x) for x in cursor_size.split('x')]

    cursor_offset = ctx.config.get('cursor_offset', (0, 0))
    if isinstance(cursor_offset, str):
        cursor_offset = [int(x) for x in cursor_offset.split('x')]

    win.bind(on_touch_down=_touch_down,
             on_touch_move=_touch_move,
             on_touch_up=_touch_up)

    if ctx.config.get('show_cursor', False):
        Logger.info('Base: Adding binding for mouse move')
        win.bind(mouse_pos=_mouse_move)


def stop(win, ctx):
    win.unbind(on_touch_down=_touch_down,
               on_touch_move=_touch_move,
               on_touch_up=_touch_up,
               on_mouse_pos=_mouse_move)
