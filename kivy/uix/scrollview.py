'''
Scroll View
===========

.. versionadded:: 1.0.4

The :class:`ScrollView` widget provides a scrollable/pannable viewport that is
clipped at the ScrollViews bounding box.

Scrolling behavior
------------------

The ScrollView accepts only one child, and controls a viewport/window to it
according to the :data:`scroll_x` and :data:`scroll_y` properties. Touches are
analyzed to determine if the user wants to scroll or control the child - you
cannot do both at the same time. To determine if interaction is a scrolling
gesture, these properties are used:

    - :data:`ScrollView.scroll_distance` a minimum distance to travel, default
      to 20 pixels.
    - :data:`ScrollView.scroll_timeout` a maximum time period, default to 250
      milliseconds.

If a touch travels :data:`~ScrollView.scroll_distance` pixels within the
:data:`~ScrollView.scroll_timeout` period, it is recognized as a scrolling
gesture and translatation (scroll/pan) will begin. If the timeout occurs, the
touch down event is dispatched to the child instead (no translation).

Limiting to X or Y axis
-----------------------

By default, the ScrollView allows scrolling both the X and Y axis. You can
explicitly disable scrolling on one of the axis by setting
:data:`ScrollView.do_scroll_x` or :data:`ScrollView.do_scroll_y` to False.

Managing the content size
-------------------------

The ScrollView manages the position of the child content, not the size. You must
carefully specify the :data:`ScrollView.size_hint` property to get the desired
scroll/pan effect.

By default, size_hint is (1, 1), so the content size will fit your ScrollView
exactly (you will have nothing to scroll). You must deactivate at least one of
the size_hint (x or y) of the child to enable scrolling.

To scroll a :class:`GridLayout` on Y-axis/vertically, set the child's width
identical to that of the ScrollView (size_hint_x=1, default), and set the
size_hint_y property to None ::

    layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
    #Make sure the height is such that there is something to scroll.
    layout.bind(minimum_height=layout.setter('height'))
    for i in range(30):
        btn = Button(text=str(i), size_hint_y=None, height=40)
        layout.add_widget(btn)
    root = ScrollView(size_hint=(None, None), size=(400, 400))
    root.add_widget(layout)

Controlling timeout, distance and trigger
-----------------------------------------

.. versionadded:: 1.0.8

In your configuration file, you can some default values for this widget::

    [widgets]
    scroll_timeout = 250
    scroll_distance = 20
    scroll_friction = 1.

If you want to reduce the default timeout, you can set::

    [widgets]
    scroll_timeout = 150

'''

__all__ = ('ScrollView', )

from functools import partial
from kivy.config import Config
from kivy.clock import Clock
from kivy.uix.stencilview import StencilView
from kivy.properties import NumericProperty, BooleanProperty, AliasProperty


# When we are generating documentation, Config doesn't exist
_scroll_timeout = _scroll_distance = _scroll_friction = 0
if Config:
    _scroll_timeout = Config.getint('widgets', 'scroll_timeout')
    _scroll_distance = Config.getint('widgets', 'scroll_distance')
    _scroll_friction = Config.getfloat('widgets', 'scroll_friction')


class ScrollView(StencilView):
    '''ScrollView class. See module documentation for more information.
    '''

    def __init__(self, **kwargs):
        self._viewport = None
        self._touch = False
        self._tdx = self._tdy = self._ts = self._tsn = 0
        self._scroll_y_mouse = 0
        super(ScrollView, self).__init__(**kwargs)
        self.bind(scroll_x=self.update_from_scroll,
                  scroll_y=self.update_from_scroll,
                  pos=self.update_from_scroll,
                  size=self.update_from_scroll)
        self.update_from_scroll()

    def convert_distance_to_scroll(self, dx, dy):
        '''Convert a distance in pixel to a scroll distance, depending of the
        content size and the scrollview size.

        The result will be a tuple of scroll distance, that can be added to
        :data:`scroll_x` and :data:`scroll_y`
        '''
        if not self._viewport:
            return 0, 0
        vp = self._viewport
        if vp.width > self.width:
            sw = vp.width - self.width
            sx = dx / float(sw)
        else:
            sx = 0
        if vp.height > self.height:
            sh = vp.height - self.height
            sy = dy / float(sh)
        else:
            sy = 1
        return sx, sy

    def update_from_scroll(self, *largs):
        '''Force the reposition of the content, according to current value of
        :data:`scroll_x` and :data:`scroll_y`.

        This method is automatically called when one of the :data:`scroll_x`,
        :data:`scroll_y`, :data:`pos` or :data:`size` properties change, or
        if the size of the content changes.
        '''
        if not self._viewport:
            return
        vp = self._viewport

        if self.do_scroll_x:
            self.scroll_x = min(1, max(0, self.scroll_x))
        if self.do_scroll_y:
            self.scroll_y = min(1, max(0, self.scroll_y))

        # update from size_hint
        if vp.size_hint_x is not None:
            vp.width = vp.size_hint_x * self.width
        if vp.size_hint_y is not None:
            vp.height = vp.size_hint_y * self.height

        if vp.width > self.width:
            sw = vp.width - self.width
            x = self.x - self.scroll_x * sw
        else:
            x = self.x
        if vp.height > self.height:
            sh = vp.height - self.height
            y = self.y - self.scroll_y * sh
        else:
            y = self.top - vp.height
        vp.pos = x, y

    #
    # Private
    #
    def add_widget(self, widget, index=0):
        if self._viewport:
            raise Exception('ScrollView accept only one widget')
        super(ScrollView, self).add_widget(widget, index)
        self._viewport = widget
        widget.bind(size=self.update_from_scroll)
        self.update_from_scroll()

    def remove_widget(self, widget):
        super(ScrollView, self).remove_widget(widget)
        if widget is self._viewport:
            self._viewport = None

    def _get_uid(self):
        return 'sv.%d' % id(self)

    def _change_touch_mode(self, *largs):
        if not self._touch:
            return
        uid = self._get_uid()
        touch = self._touch
        mode = touch.ud[uid]['mode']
        if mode == 'unknown':
            touch.ungrab(self)
            self._touch = None
            # correctly calculate the position of the touch inside the
            # scrollview
            touch.push()
            touch.apply_transform_2d(self.to_widget)
            touch.apply_transform_2d(self.to_parent)
            super(ScrollView, self).on_touch_down(touch)
            touch.pop()
            return

    def _do_touch_up(self, touch, *largs):
        super(ScrollView, self).on_touch_up(touch)
        # don't forget about grab event!
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            super(ScrollView, self).on_touch_up(touch)
        touch.grab_current = None

    def _do_animation(self, touch):
        uid = self._get_uid()
        ud = touch.ud[uid]
        dt = touch.time_end - ud['time']
        if dt > self.scroll_timeout / 1000.:
            self._tdx = self._tdy = self._ts = 0
            return
        dt = ud['dt']
        if dt == 0:
            self._tdx = self._tdy = self._ts = 0
            return
        dx = touch.dx
        dy = touch.dy
        self._sx = ud['sx']
        self._sy = ud['sy']
        self._tdx = dx = dx / dt
        self._tdy = dy = dy / dt
        if abs(dx) < 10 and abs(dy) < 10:
            return
        self._ts = self._tsn = touch.time_update
        Clock.unschedule(self._update_animation)
        Clock.schedule_interval(self._update_animation, 0)

    def _update_animation(self, dt):
        if self._touch is not None or self._ts == 0:
            return False
        self._tsn += dt
        global_dt = self._tsn - self._ts
        divider = 2 ** (global_dt * self.scroll_friction)
        dx = self._tdx / divider
        dy = self._tdy / divider
        test_dx = abs(dx) < 10
        test_dy = abs(dy) < 10
        if (self.do_scroll_x and not self.do_scroll_y and test_dx) or\
           (self.do_scroll_y and not self.do_scroll_x and test_dy) or\
           (self.do_scroll_x and self.do_scroll_y and test_dx and test_dy):
            self._ts = 0
            return False
        dx *= dt
        dy *= dt
        '''
        print 'move by %.3f %.3f | dt=%.3f, divider=%.3f, tdXY=(%.3f, %.3f)' % (
            dx, dy, global_dt, divider, self._tdx, self._tdy)
        '''
        sx, sy = self.convert_distance_to_scroll(dx, dy)
        ssx = self.scroll_x
        ssy = self.scroll_y
        if self.do_scroll_x:
            self.scroll_x -= sx
        if self.do_scroll_y:
            self.scroll_y -= sy
        if ssx == self.scroll_x and ssy == self.scroll_y:
            return False

    def on_touch_down(self, touch):
        if self._touch:
            return super(ScrollView, self).on_touch_down(touch)
        if not self.collide_point(*touch.pos):
            return
        # support scrolling !
        if self._viewport and 'button' in touch.profile and \
                touch.button.startswith('scroll'):
            # distance available to move, if no distance, do nothing
            vp = self._viewport
            if vp.height > self.height:
                # let's say we want to move over 40 pixels each scroll
                d = (vp.height - self.height)
                d = self.scroll_distance / float(d)
                if touch.button == 'scrollup':
                    syd = self.scroll_y - d
                elif touch.button == 'scrolldown':
                    syd = self.scroll_y + d
                self.scroll_y = min(max(syd, 0), 1)
                return True

        self._touch = touch
        uid = self._get_uid()
        touch.grab(self)
        touch.ud[uid] = {
            'mode': 'unknown',
            'sx': self.scroll_x,
            'sy': self.scroll_y,
            'dt': None,
            'time': touch.time_start}
        Clock.schedule_once(self._change_touch_mode, self.scroll_timeout/1000.)
        return True

    def on_touch_move(self, touch):
        if self._touch is not touch:
            super(ScrollView, self).on_touch_move(touch)
            return self._get_uid() in touch.ud
        if touch.grab_current is not self:
            return True
        uid = self._get_uid()
        ud = touch.ud[uid]
        mode = ud['mode']

        # seperate the distance to both X and Y axis.
        # if a distance is reach, but on the inverse axis, stop scroll mode !
        if mode == 'unknown':
            distance = abs(touch.ox - touch.x)
            if distance > self.scroll_distance:
                if not self.do_scroll_x:
                    self._change_touch_mode()
                    return
                mode = 'scroll'

            distance = abs(touch.oy - touch.y)
            if distance > self.scroll_distance:
                if not self.do_scroll_y:
                    self._change_touch_mode()
                    return
                mode = 'scroll'

        if mode == 'scroll':
            ud['mode'] = mode
            dx = touch.ox - touch.x
            dy = touch.oy - touch.y
            sx, sy = self.convert_distance_to_scroll(dx, dy)
            if self.do_scroll_x:
                self.scroll_x = ud['sx'] + sx
            if self.do_scroll_y:
                self.scroll_y = ud['sy'] + sy
            ud['dt'] = touch.time_update - ud['time']
            ud['time'] = touch.time_update

        return True

    def on_touch_up(self, touch):
        # Warning: usually, we are checking if grab_current is ourself first. On
        # this case, we might need to call on_touch_down. If we call it inside
        # the on_touch_up + grab state, any widget that grab the touch will be
        # never ungrabed, cause their on_touch_up will be never called.
        # base.py: the me.grab_list[:] => it's a copy, and we are already
        # iterate on it.
        if self in [x() for x in touch.grab_list]:
            touch.ungrab(self)
            self._touch = None
            uid = self._get_uid()
            mode = touch.ud[uid]['mode']
            if mode == 'unknown':
                # we must do the click at least..
                super(ScrollView, self).on_touch_down(touch)
                Clock.schedule_once(partial(self._do_touch_up, touch), .1)
            elif self.auto_scroll:
                self._do_animation(touch)
        else:
            if self._touch is not touch:
                super(ScrollView, self).on_touch_up(touch)
        return self._get_uid() in touch.ud



    #
    # Properties
    #
    auto_scroll = BooleanProperty(True)
    '''Automatic scrolling is the movement activated after a swipe. When you
    release a touch, it will start to move the list, according to the lastest
    touch movement.
    If you don't want that behavior, just set the auto_scroll to False.

    :data:`auto_scroll` is a :class:`~kivy.properties.BooleanProperty`, default
    to True
    '''

    scroll_friction = NumericProperty(_scroll_friction)
    '''Friction is a factor for reducing the scrolling when the list is not
    moved by a touch. When you do a swipe, the movement speed is calculated, and
    is used to move automatically the list when you touch up. The speed is
    reducing from this equation::

        2 ^ (t * f)
        # t is the time from the touch up
        # f is the friction

    By default, the friction factor is 1, it will reduce the speed by a factor
    or 2 each seconds. If you set the friction to 0, the list speed will never
    stop. If you set to a bigger value, the list movement will stop faster.

    :data:`scroll_friction` is a :class:`~kivy.properties.NumericProperty`,
    default to 1, according to the default value in user configuration.
    '''

    scroll_distance = NumericProperty(_scroll_distance)
    '''Distance to move before scrolling the :class:`ScrollView`, in pixels. As
    soon as the distance have been traveled, the :class:`ScrollView` will start
    to scroll, and no touch event will go to children.

    :data:`scroll_distance` is a :class:`~kivy.properties.NumericProperty`,
    default to 20 (pixels), according to the default value in user
    configuration.
    '''

    scroll_timeout = NumericProperty(_scroll_timeout)
    '''Timeout allowed to trigger the :data:`scroll_distance`, in milliseconds.
    If the timeout is reach, the scrolling will be disabled, and the touch event
    will go to the children.

    :data:`scroll_timeout` is a :class:`~kivy.properties.NumericProperty`,
    default to 250 (milliseconds), according to the default value in user
    configuration.
    '''

    scroll_x = NumericProperty(0.)
    '''X scrolling value, between 0 and 1. If 0, the content's left side will
    touch the left side of the ScrollView. If 1, the content's right side will
    touch the right side.

    This property is controled by :class:`ScrollView` only if
    :data:`do_scroll_x` is True.

    :data:`scroll_x` is a :class:`~kivy.properties.NumericProperty`,
    default to 0.
    '''

    scroll_y = NumericProperty(1.)
    '''Y scrolling value, between 0 and 1. If 0, the content's bottom side will
    touch the bottom side of the ScrollView. If 1, the content's top side will
    touch the top side.

    This property is controled by :class:`ScrollView` only if
    :data:`do_scroll_y` is True.

    :data:`scroll_y` is a :class:`~kivy.properties.NumericProperty`,
    default to 1.
    '''

    do_scroll_x = BooleanProperty(True)
    '''Allow scroll on X axis

    :data:`do_scroll_x` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''

    do_scroll_y = BooleanProperty(True)
    '''Allow scroll on Y axis

    :data:`do_scroll_y` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''

    def _get_do_scroll(self):
        return (self.do_scroll_x, self.do_scroll_y)

    def _set_do_scroll(self, value):
        if type(value) in (list, tuple):
            self.do_scroll_x, self.do_scroll_y = value
        else:
            self.do_scroll_x = self.do_scroll_y = bool(value)
    do_scroll = AliasProperty(_get_do_scroll, _set_do_scroll,
                                bind=('do_scroll_x', 'do_scroll_y'))
    '''Allow scroll on X or Y axis

    :data:`do_scroll` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`do_scroll_x` + :data:`do_scroll_y`)
    '''

