'''
Scroll View
===========

.. versionadded:: 1.0.4

The :class:`ScrollView` widget provides a scrollable/pannable viewport that is
clipped at the scrollview's bounding box.

Scrolling Behavior
------------------

ScrollView accepts only one child, and applies a viewport/window to it
according to the :data:`scroll_x` and :data:`scroll_y` properties. Touches are
analyzed to determine if the user wants to scroll or control the child in some
other manner - you cannot do both at the same time. To determine if interaction
is a scrolling gesture, these properties are used:

    - :data:`ScrollView.scroll_distance` a minimum distance to travel, default
      to 20 pixels.
    - :data:`ScrollView.scroll_timeout` a maximum time period, default to 250
      milliseconds.

If a touch travels :data:`~ScrollView.scroll_distance` pixels within the
:data:`~ScrollView.scroll_timeout` period, it is recognized as a scrolling
gesture and translatation (scroll/pan) will begin. If the timeout occurs, the
touch down event is dispatched to the child instead (no translation).

.. versionadded:: 1.1.1

    Scrollview now animates scrolling in Y when a mousewheel is used.

Limiting to X or Y Axis
-----------------------

By default, ScrollView allows scrolling in both the X and Y axes. You can
explicitly disable scrolling on an axis by setting
:data:`ScrollView.do_scroll_x` or :data:`ScrollView.do_scroll_y` to False.

Managing the Content Size
-------------------------

ScrollView manages the position of the child content, not the size. You must
carefully specify the :data:`ScrollView.size_hint` property to get the desired
scroll/pan effect.

By default, size_hint is (1, 1), so the content size will fit your ScrollView
exactly (you will have nothing to scroll). You must deactivate at least one of
the size_hint instructions (x or y) of the child to enable scrolling.

To scroll a :class:`GridLayout` on Y-axis/vertically, set the child's width
identical to that of the ScrollView (size_hint_x=1, default), and set the
size_hint_y property to None::

    layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
    #Make sure the height is such that there is something to scroll.
    layout.bind(minimum_height=layout.setter('height'))
    for i in range(30):
        btn = Button(text=str(i), size_hint_y=None, height=40)
        layout.add_widget(btn)
    root = ScrollView(size_hint=(None, None), size=(400, 400))
    root.add_widget(layout)

Controlling Timeout, Distance and Trigger
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

from copy import copy
from functools import partial
from kivy.animation import Animation
from kivy.config import Config
from kivy.clock import Clock
from kivy.uix.stencilview import StencilView
from kivy.properties import NumericProperty, BooleanProperty, AliasProperty, \
    ObjectProperty, ListProperty


# When we are generating documentation, Config doesn't exist
_scroll_moves = _scroll_timeout = _scroll_stoptime = \
        _scroll_distance = _scroll_friction = 0
if Config:
    _scroll_timeout = Config.getint('widgets', 'scroll_timeout')
    _scroll_stoptime = Config.getint('widgets', 'scroll_stoptime')
    _scroll_distance = Config.getint('widgets', 'scroll_distance')
    _scroll_moves = Config.getint('widgets', 'scroll_moves')
    _scroll_friction = Config.getfloat('widgets', 'scroll_friction')


class FixedList(list):
    '''A list. In addition, you can specify the maximum length.
    This will save memory.
    '''
    def __init__(self, maxlength=0, *args, **kwargs):
        super(FixedList, self).__init__(*args, **kwargs)
        self.maxlength = maxlength

    def append(self, x):
        super(FixedList, self).append(x)
        self._cut()

    def extend(self, L):
        super(FixedList, self).append(L)
        self._cut()

    def _cut(self):
        while len(self) > self.maxlength:
            self.pop(0)


class ScrollView(StencilView):
    '''ScrollView class. See module documentation for more information.
    '''

    def __init__(self, **kwargs):
        self._touch = False
        self._tdx = self._tdy = self._ts = self._tsn = 0
        self._scroll_y_mouse = 1
        self._scroll_x_mouse = 1
        super(ScrollView, self).__init__(**kwargs)
        self.bind(scroll_x=self.update_from_scroll,
                  scroll_y=self.update_from_scroll,
                  pos=self.update_from_scroll,
                  size=self.update_from_scroll)
        self.update_from_scroll()

    def convert_distance_to_scroll(self, dx, dy):
        '''Convert a distance in pixels to a scroll distance, depending on the
        content size and the scrollview size.

        The result will be a tuple of scroll distance that can be added to
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

        # new in 1.2.0, show bar when scrolling happen
        # and slowly remove them when no scroll is happening.
        self.bar_alpha = 1.
        Animation.stop_all(self, 'bar_alpha')
        Clock.unschedule(self._start_decrease_alpha)
        Clock.schedule_once(self._start_decrease_alpha, .5)

    def _start_decrease_alpha(self, *l):
        self.bar_alpha = 1.
        Animation(bar_alpha=0., d=.5, t='out_quart').start(self)

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

    def _get_uid(self, prefix='sv'):
        return '{0}.{1}'.format(prefix, self.uid)

    def _change_touch_mode(self, *largs):
        if not self._touch:
            return
        uid = self._get_uid()
        touch = self._touch
        ud = touch.ud[uid]
        if ud['mode'] == 'unknown' and \
                not ud['user_stopped'] and \
                touch.dx + touch.dy == 0:
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

    def _do_animation(self, touch, *largs):
        uid = self._get_uid()
        ud = touch.ud[uid]
        dt = touch.time_end - ud['time']
        avgdx = sum([move.dx for move in ud['moves']]) / len(ud['moves'])
        avgdy = sum([move.dy for move in ud['moves']]) / len(ud['moves'])
        if ud['same'] > self.scroll_stoptime / 1000.:
            return
        dt = ud['dt']
        if dt == 0:
            self._tdx = self._tdy = self._ts = 0
            return
        dx = avgdx
        dy = avgdy
        self._sx = ud['sx']
        self._sy = ud['sy']
        self._tdx = dx = dx / dt
        self._tdy = dy = dy / dt
        self._ts = self._tsn = touch.time_update

        Clock.unschedule(self._update_animation)
        Clock.schedule_interval(self._update_animation, 0)

    def _update_animation(self, dt):
        if self._touch is not None or self._ts == 0:
            touch = self._touch
            uid = self._get_uid()
            ud = touch.ud[uid]
            # scrolling stopped by user input
            ud['user_stopped'] = True
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
            # scrolling stopped by friction
            return False
        dx *= dt
        dy *= dt
        sx, sy = self.convert_distance_to_scroll(dx, dy)
        ssx = self.scroll_x
        ssy = self.scroll_y
        if self.do_scroll_x:
            self.scroll_x -= sx
        if self.do_scroll_y:
            self.scroll_y -= sy
        self._scroll_x_mouse = self.scroll_x
        self._scroll_y_mouse = self.scroll_y
        if ssx == self.scroll_x and ssy == self.scroll_y:
            # scrolling stopped by end of box
            return False

    def _update_delta(self, dt):
        touch = self._touch
        if not touch:
            return False
        uid = self._get_uid()
        ud = touch.ud[uid]
        if touch.dx + touch.dy != 0:
            ud['same'] += dt
        else:
            ud['same'] = 0

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            touch.ud[self._get_uid('svavoid')] = True
            return
        if self._touch:
            return super(ScrollView, self).on_touch_down(touch)
        # support scrolling !
        if self._viewport and 'button' in touch.profile and \
                touch.button.startswith('scroll'):
            # distance available to move, if no distance, do nothing
            vp = self._viewport
            if vp.height > self.height:
                # let's say we want to move over 40 pixels each scroll
                d = (vp.height - self.height)
                syd = None
                if d != 0:
                    d = self.scroll_distance / float(d)
                if touch.button == 'scrollup':
                    syd = self._scroll_y_mouse - d
                elif touch.button == 'scrolldown':
                    syd = self._scroll_y_mouse + d

                if syd is not None:
                    self._scroll_y_mouse = scroll_y = min(max(syd, 0), 1)
                    Animation.stop_all(self, 'scroll_y')
                    Animation(scroll_y=scroll_y, d=.3,
                              t='out_quart').start(self)
                    Clock.unschedule(self._update_animation)
                    return True

            if vp.width > self.width:
                # let's say we want to move over 40 pixels each scroll
                d = (vp.width - self.width)
                if d != 0:
                    d = self.scroll_distance / float(d)
                if touch.button == 'scrollright':
                    sxd = self._scroll_x_mouse - d
                elif touch.button == 'scrollleft':
                    sxd = self._scroll_x_mouse + d
                self._scroll_x_mouse = scroll_x = min(max(sxd, 0), 1)
                Animation.stop_all(self, 'scroll_x')
                Animation(scroll_x=scroll_x, d=.3, t='out_quart').start(self)
                Clock.unschedule(self._update_animation)
                return True

        self._touch = touch
        uid = self._get_uid()
        touch.grab(self)
        touch.ud[uid] = {
            'mode': 'unknown',
            'sx': self.scroll_x,
            'sy': self.scroll_y,
            'dt': None,
            'time': touch.time_start,
            'user_stopped': False,
            'same': 0,
            'moves': FixedList(self.scroll_moves)}

        Clock.schedule_interval(self._update_delta, 0)
        Clock.schedule_once(self._change_touch_mode,
                            self.scroll_timeout / 1000.)
        return True

    def on_touch_move(self, touch):
        if self._get_uid('svavoid') in touch.ud:
            return
        if self._touch is not touch:
            super(ScrollView, self).on_touch_move(touch)
            return self._get_uid() in touch.ud
        if touch.grab_current is not self:
            return True
        uid = self._get_uid()
        ud = touch.ud[uid]
        mode = ud['mode']
        ud['moves'].append(copy(touch))

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
            ud['user_stopped'] = True

        return True

    def on_touch_up(self, touch):
        # Warning: usually, we are checking if grab_current is ourself first. On
        # this case, we might need to call on_touch_down. If we call it inside
        # the on_touch_up + grab state, any widget that grab the touch will be
        # never ungrabed, cause their on_touch_up will be never called.
        # base.py: the me.grab_list[:] => it's a copy, and we are already
        # iterate on it.
        Clock.unschedule(self._update_delta)
        if self._get_uid('svavoid') in touch.ud:
            return

        if 'button' in touch.profile and not touch.button.startswith('scroll'):
            self._scroll_y_mouse = self.scroll_y
            self._scroll_x_mouse = self.scroll_x

        if self in [x() for x in touch.grab_list]:
            touch.ungrab(self)
            self._touch = None
            uid = self._get_uid()
            ud = touch.ud[uid]
            if ud['mode'] == 'unknown':
                # we must do the click at least..
                # only send the click if it was not a click to stop
                # autoscrolling
                if not ud['user_stopped']:
                    super(ScrollView, self).on_touch_down(touch)
                Clock.schedule_once(partial(self._do_touch_up, touch), .1)
            elif self.auto_scroll:
                self._do_animation(touch)
        else:
            if self._touch is not touch and self.uid not in touch.ud:
                super(ScrollView, self).on_touch_up(touch)

        # if we do mouse scrolling, always accept it
        if 'button' in touch.profile and touch.button.startswith('scroll'):
            return True

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
    moved by a touch. When you do a swipe, the movement speed is calculated,
    and is used to move the list automatically when touch up happens. The speed
    is reducing from this equation::

        2 ^ (t * f)
        # t is the time from the touch up
        # f is the friction

    By default, the friction factor is 1. It will reduce the speed by a factor
    of 2 each second. If you set the friction to 0, the list speed will never
    stop. If you set to a bigger value, the list movement will stop faster.

    :data:`scroll_friction` is a :class:`~kivy.properties.NumericProperty`,
    default to 1, according to the default value in user configuration.
    '''

    scroll_moves = NumericProperty(_scroll_moves)
    '''The speed of automatic scrolling is based on previous touch moves. This
    is to prevent accidental slowing down by the user at the end of the swipe
    to slow down the automatic scrolling.
    The moves property specifies the amount of previous scrollmoves that
    should be taken into consideration when calculating the automatic scrolling
    speed.

    :data:`scroll_moves` is a :class:`~kivy.properties.NumericProperty`,
    default to 5.

    .. versionadded:: 1.5.0
    '''

    scroll_stoptime = NumericProperty(_scroll_stoptime)
    '''Time after which user input not moving will disable autoscroll for that
    move. If the user has not moved within the stoptime, autoscroll will not
    start.
    This is to prevent autoscroll to trigger while the user has slowed down
    on purpose to prevent this.

    :data:`scroll_stoptime` is a :class:`~kivy.properties.NumericProperty`,
    default to 300 (milliseconds)

    .. versionadded:: 1.5.0
    '''

    scroll_distance = NumericProperty(_scroll_distance)
    '''Distance to move before scrolling the :class:`ScrollView`, in pixels. As
    soon as the distance has been traveled, the :class:`ScrollView` will start
    to scroll, and no touch event will go to children.
    It is advisable that you base this value on the dpi of your target device's
    screen.

    :data:`scroll_distance` is a :class:`~kivy.properties.NumericProperty`,
    default to 20 (pixels), according to the default value in user
    configuration.
    '''

    scroll_timeout = NumericProperty(_scroll_timeout)
    '''Timeout allowed to trigger the :data:`scroll_distance`, in milliseconds.
    If the user has not moved :data:`scroll_distance` within the timeout,
    the scrolling will be disabled, and the touch event will go to the children.

    :data:`scroll_timeout` is a :class:`~kivy.properties.NumericProperty`,
    default to 55 (milliseconds), according to the default value in user
    configuration.

    .. versionchanged:: 1.5.0
        Default value changed from 250 to 55.
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
    '''Allow scroll on X axis.

    :data:`do_scroll_x` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''

    do_scroll_y = BooleanProperty(True)
    '''Allow scroll on Y axis.

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
    '''Allow scroll on X or Y axis.

    :data:`do_scroll` is a :class:`~kivy.properties.AliasProperty` of
    (:data:`do_scroll_x` + :data:`do_scroll_y`)
    '''

    def _get_vbar(self):
        # must return (y, height) in %
        # calculate the viewport size / scrollview size %
        if self._viewport is None:
            return 0, 1.
        vh = self._viewport.height
        h = self.height
        if vh < h or vh == 0:
            return 0, 1.
        ph = max(0.01, h / float(vh))
        py = (1. - ph) * self.scroll_y
        return (py, ph)

    vbar = AliasProperty(_get_vbar, None, bind=(
        'scroll_y', '_viewport', '_viewport_size'))
    '''Return a tuple of (position, size) of the vertical scrolling bar.

    .. versionadded:: 1.2.0

    The position and size are normalized between 0-1, and represent a
    percentage of the current scrollview height. This property is used
    internally for drawing the little vertical bar when you're scrolling.

    :data:`vbar` is a :class:`~kivy.properties.AliasProperty`, readonly.
    '''

    def _get_hbar(self):
        # must return (x, width) in %
        # calculate the viewport size / scrollview size %
        if self._viewport is None:
            return 0, 1.
        vw = self._viewport.width
        w = self.width
        if vw < w or vw == 0:
            return 0, 1.
        pw = max(0.01, w / float(vw))
        px = (1. - pw) * self.scroll_x
        return (px, pw)

    hbar = AliasProperty(_get_hbar, None, bind=(
        'scroll_x', '_viewport', '_viewport_size'))
    '''Return a tuple of (position, size) of the horizontal scrolling bar.

    .. versionadded:: 1.2.0

    The position and size are normalized between 0-1, and represent a
    percentage of the current scrollview height. This property is used
    internally for drawing the little horizontal bar when you're scrolling.

    :data:`vbar` is a :class:`~kivy.properties.AliasProperty`, readonly.
    '''

    bar_color = ListProperty([.7, .7, .7, .9])
    '''Color of horizontal / vertical scroll bar, in RGBA format.

    .. versionadded:: 1.2.0

    :data:`bar_color` is a :class:`~kivy.properties.ListProperty`, default to
    [.7, .7, .7, .9].
    '''

    bar_width = NumericProperty('2dp')
    '''Width of the horizontal / vertical scroll bar. The width is interpreted
    as a height for the horizontal bar.

    .. versionadded:: 1.2.0

    :data:`bar_width` is a :class:`~kivy.properties.NumericProperty`, default
    to 2
    '''

    bar_margin = NumericProperty(0)
    '''Margin between the bottom / right side of the scrollview when drawing
    the horizontal / vertical scroll bar.

    .. versionadded:: 1.2.0

    :data:`bar_margin` is a :class:`~kivy.properties.NumericProperty`, default
    to 0
    '''

    # private, for internal use only

    _viewport = ObjectProperty(None, allownone=True)
    _viewport_size = ListProperty([0, 0])
    bar_alpha = NumericProperty(1.)

    def _set_viewport_size(self, instance, value):
        self._viewport_size = value

    def on__viewport(self, instance, value):
        if value:
            value.bind(size=self._set_viewport_size)
            self._viewport_size = value.size
