'''
Touchring module
================

Show ring around every touch on the table. You can use this module for checking
if you don't have any calibration trouble with touches.
'''

import os
from kivy import kivy_data_dir
from kivy.core.image import Image
from kivy.graphics import Color, Rectangle

if not 'KIVY_DOC' in os.environ:
    ring_fn = os.path.join(kivy_data_dir, 'images', 'ring.png')
    ring_img = Image(ring_fn)


def _touch_down(win, touch):
    ud = touch.userdata
    touch.scale_for_screen(win.width, win.height)
    with win.canvas.after:
        ud['tr.color'] = Color(1, 1, 1, .7)
        iw, ih = ring_img.size
        ud['tr.rect'] = Rectangle(
            pos=(
                touch.x - (ring_img.width / 2. * 0.3),
                touch.y - (ring_img.height / 2. * 0.3)),
            size=(iw * 0.3, ih * 0.3),
            texture=ring_img.texture)


def _touch_move(win, touch):
    ud = touch.userdata
    ud['tr.rect'].pos = (
        touch.x - (ring_img.width / 2. * 0.3),
        touch.y - (ring_img.height / 2. * 0.3))


def _touch_up(win, touch):
    ud = touch.userdata
    win.canvas.after.remove(ud['tr.color'])
    win.canvas.after.remove(ud['tr.rect'])


def start(win, ctx):
    win.bind(on_touch_down=_touch_down,
             on_touch_move=_touch_move,
             on_touch_up=_touch_up)


def stop(win, ctx):
    win.unbind(on_touch_down=_touch_down,
             on_touch_move=_touch_move,
             on_touch_up=_touch_up)
