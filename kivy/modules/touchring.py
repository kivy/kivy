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
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, NumericProperty


class TouchRingWidget(Widget):
    '''This widget will not be added to the widget tree. Only using for touch
    handler'''
    window = ObjectProperty()
    pointer_image = ObjectProperty()
    pointer_alpha = NumericProperty()
    pointer_scale = NumericProperty()

    def on_touch_down_window(self, window, touch):
        ud = touch.ud
        pointer_image = self.pointer_image
        pointer_scale = self.pointer_scale
        with window.canvas.after:
            ud['tr.color'] = Color(1, 1, 1, self.pointer_alpha)
            iw, ih = pointer_image.size
            ud['tr.rect'] = Rectangle(
                pos=(
                    touch.x - (pointer_image.width / 2. * pointer_scale),
                    touch.y - (pointer_image.height / 2. * pointer_scale)),
                size=(iw * pointer_scale, ih * pointer_scale),
                texture=pointer_image.texture)

        if not ud.get('tr.grab', False):
            ud['tr.grab'] = True
            touch.grab(self)

    def on_touch_move_window(self, window, touch):
        if not touch.ud.get('tr.rect', False):
            self.on_touch_down_window(window, touch)

    def on_touch_move(self, touch):
        assert touch.grab_current is self
        pointer_image = self.pointer_image
        pointer_scale = self.pointer_scale
        touch.ud['tr.rect'].pos = (
            touch.x - (pointer_image.width / 2. * pointer_scale),
            touch.y - (pointer_image.height / 2. * pointer_scale))

    def on_touch_up(self, touch):
        assert touch.grab_current is self
        ud = touch.ud
        remove = self.window.canvas.after.remove
        remove(ud['tr.color'])
        remove(ud['tr.rect'])

        if ud.get('tr.grab') is True:
            touch.ungrab(self)
            ud['tr.grab'] = False


def start(win, ctx):
    config_get = ctx.config.get
    widget = TouchRingWidget(
        window=win,
        pointer_scale=float(config_get('scale', 1.0)),
        pointer_alpha=float(config_get('alpha', 1.0)),
        pointer_image=Image(config_get('image',
                                       'atlas://data/images/defaulttheme/ring')),
    )
    win.bind(on_touch_down=widget.on_touch_down_window,
             on_touch_move=widget.on_touch_move_window)
    ctx.widget = widget


def stop(win, ctx):
    widget = ctx.widget
    win.unbind(on_touch_down=widget.on_touch_down_window,
               on_touch_move=widget.on_touch_move_window)
