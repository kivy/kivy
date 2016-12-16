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

pointer_image = None
pointer_scale = 1.0
pointer_alpha = 0.7


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


def start(win, ctx):
    # XXX use ctx !
    global pointer_image, pointer_scale, pointer_alpha

    pointer_fn = ctx.config.get('image',
                                'atlas://data/images/defaulttheme/ring')
    pointer_scale = float(ctx.config.get('scale', 1.0))
    pointer_alpha = float(ctx.config.get('alpha', 1.0))
    pointer_image = Image(pointer_fn)

    win.bind(on_touch_down=_touch_down,
             on_touch_move=_touch_move,
             on_touch_up=_touch_up)


def stop(win, ctx):
    win.unbind(on_touch_down=_touch_down,
               on_touch_move=_touch_move,
               on_touch_up=_touch_up)
