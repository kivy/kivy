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

The default value for thoses settings can be changed in the configuration file::

    [widgets]
    scroll_timeout = 250
    scroll_distance = 20

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
carefully specify the `size_hint` of your content to get the desired
scroll/pan effect.

By default, size_hint is (1, 1), so the content size will fit your ScrollView
exactly (you will have nothing to scroll). You must deactivate at least one of
the size_hint instructions (x or y) of the child to enable scrolling.

To scroll a :class:`GridLayout` on Y-axis/vertically, set the child's width
identical to that of the ScrollView (size_hint_x=1, default), and set the
size_hint_y property to None::

    layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
    # Make sure the height is such that there is something to scroll.
    layout.bind(minimum_height=layout.setter('height'))
    for i in range(30):
        btn = Button(text=str(i), size_hint_y=None, height=40)
        layout.add_widget(btn)
    root = ScrollView(size_hint=(None, None), size=(400, 400))
    root.add_widget(layout)


Effects
-------

.. versionadded:: 1.7.0

An effect is a subclass of :class:`~kivy.effects.scroll.ScrollEffect` that will
compute informations during the dragging, and apply transformation to the
:class:`ScrollView`. Depending of the effect, more computing can be done for
calculating over-scroll, bouncing, etc.

All the effects are located in the :mod:`kivy.effects`.


'''

__all__ = ('ScrollView', )

from functools import partial
from kivy.animation import Animation
from kivy.config import Config
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.metrics import sp
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.properties import NumericProperty, BooleanProperty, AliasProperty, \
    ObjectProperty, ListProperty


# When we are generating documentation, Config doesn't exist
_scroll_timeout = _scroll_distance = 0
_desktop = False
if Config:
    _scroll_timeout = Config.getint('widgets', 'scroll_timeout')
    _scroll_distance = sp(Config.getint('widgets', 'scroll_distance'))
    _desktop = Config.getboolean('kivy', 'desktop')


class ScrollView(Widget):
    '''ScrollView class. See module documentation for more information.

    .. versionchanged:: 1.7.0

        `auto_scroll`, `scroll_friction`, `scroll_moves`, `scroll_stoptime' has
        been deprecated, use :data:`effect_cls` instead.
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

    scroll_proportionate = BooleanProperty(_desktop)
    '''Whether the scrolling is proportionate as is typical in desktop
    environments.

    .. versionadded:: 1.8.0

    :data:`scroll_proportionate` is a :class:`~kivy.properties.BooleanProperty`,
    default to True if executed on a desktop (i.e. desktop is True in the kivy
    config file). When True, a downward/rightward drag with the mouse will
    scroll down/righ. When False, it behaves like a touch device where a drag
    up/left scroll down/right. Also, when True, a drag of the bar from one end
    to the other will scroll through the full content
    (top/right to bottom/left).
    '''

    scroll_on_bar_only = BooleanProperty(_desktop)
    '''Whether scrolling can be initiated only from on top of the scrollbar as
    is typical in desktop environments.

    .. versionadded:: 1.8.0

    :data:`scroll_on_bar` is a :class:`~kivy.properties.BooleanProperty`,
    default to True if executed on a desktop (i.e. desktop is True in the kivy
    config file). When True, scrolling will only occur if the scroll started
    from on top of the scroll bar. In addition, if True, scrolling will only
    occur in the direction of the scroll bar that was clicked. E.g. if a scroll
    is started on the y bar, only y scrolling will occur for that touch session.
    '''

    def _get_vbar(self):
        # must return (y, height) in %
        # calculate the viewport size / scrollview size %
        if self._viewport is None:
            return 0, 1.
        vh = self._viewport.height
        h = self.view_height
        if vh < h or vh == 0:
            return 0, 1.
        ph = max(0.01, h / float(vh))
        sy = min(1.0, max(0.0, self.scroll_y))
        py = (1. - ph) * sy
        return (py, ph)

    vbar = AliasProperty(_get_vbar, None, bind=(
        'scroll_y', '_viewport', 'viewport_size'))
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
        w = self.view_width
        if vw < w or vw == 0:
            return 0, 1.
        pw = max(0.01, w / float(vw))
        sx = min(1.0, max(0.0, self.scroll_x))
        px = (1. - pw) * sx
        return (px, pw)

    hbar = AliasProperty(_get_hbar, None, bind=(
        'scroll_x', '_viewport', 'viewport_size'))
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

    bar_width = NumericProperty('16dp' if _desktop else '2dp')
    '''Width of the horizontal / vertical scroll bar. The width is interpreted
    as a height for the horizontal bar.

    .. versionadded:: 1.2.0

    :data:`bar_width` is a :class:`~kivy.properties.NumericProperty`, defaults
    to 16dp if executed on a desktop (i.e. desktop is True in the kivy
    config file), otherwise to 2dp.

    .. versionchanged:: 1.8.0
        Default value changed from 2dp to 16dp when executed on a desktop
        (i.e. desktop is True in the kivy config file).
    '''

    bar_margin = NumericProperty(0)
    '''Margin between the bottom / right side of the scrollview when drawing
    the horizontal / vertical scroll bar.

    .. versionadded:: 1.2.0

    :data:`bar_margin` is a :class:`~kivy.properties.NumericProperty`, default
    to 0
    '''

    bar_perm = BooleanProperty(_desktop)
    '''Whether the scrolling bar is permanently displayed.

    .. versionadded:: 1.8.0

    :data:`bar_perm` is a :class:`~kivy.properties.BooleanProperty`,
    default to True if executed on a desktop (i.e. desktop is True in the kivy
    config file). When True, the scroll bar is permanently displayed and the
    viewing area is therefore reduced by the scroll bar width. Also, a touch
    initiated over a scroll bar will never time out.
    '''

    effect_cls = ObjectProperty(DampedScrollEffect, allownone=True)
    '''Class effect to instanciate for X and Y axis.

    .. versionadded:: 1.7.0

    :data:`effect_cls` is a :class:`~kivy.properties.ObjectProperty`, default to
    :class:`DampedScrollEffect`.
    '''

    effect_x = ObjectProperty(None, allownone=True)
    '''Effect to apply for the X axis. If None is set, an instance of
    :data:`effect_cls` will be created.

    .. versionadded:: 1.7.0

    :data:`effect_x` is a :class:`~kivy.properties.ObjectProperty`, default to
    None
    '''

    effect_y = ObjectProperty(None, allownone=True)
    '''Effect to apply for the Y axis. If None is set, an instance of
    :data:`effect_cls` will be created.

    .. versionadded:: 1.7.0

    :data:`effect_y` is a :class:`~kivy.properties.ObjectProperty`, default to
    None, read-only.
    '''

    view_width = NumericProperty(0)
    '''The width of the observable content. Read Only. Typically, this is the
    same as self.width. However, if the y bar is permanently displayed, and
    there's y content to scroll, and the y bar is enabled; the effective view
    will be smaller than self.width by :data:`bar_width`.
    :data:`view_width` will reflect the effective width.

    .. versionadded:: 1.8.0

    :data:`view_width` is a :class:`~kivy.properties.NumericProperty`, default
    to 0
    '''

    view_height = NumericProperty(0)
    '''The height of the observable content. Read Only. Typically, this is the
    same as self.height. However, if the x bar is permanently displayed, and
    there's x content to scroll, and the x bar is enabled; the effective view
    will be smaller than self.height by :data:`bar_width`.
    :data:`view_height` will reflect the effective height.

    .. versionadded:: 1.8.0

    :data:`view_height` is a :class:`~kivy.properties.NumericProperty`, default
    to 0
    '''

    view_y = NumericProperty(0)
    '''The amount by which the content is displaced in the y direction relative
    to self.y. Read Only. Typically, this is the same as self.y. However, if
    the x bar is permanently displayed, and there's x content to scroll, and
    the x bar is enabled; the content will be displaced by :data:`bar_width`.
    :data:`view_y` will reflect the effective y relative to self.y.

    .. versionadded:: 1.8.0

    :data:`view_y` is a :class:`~kivy.properties.NumericProperty`, default
    to 0
    '''

    viewport_size = ListProperty([0, 0])
    '''(internal) Size of the internal viewport. This is the size of your only
    child in the scrollview.
    '''

    # private, for internal use only

    _viewport = ObjectProperty(None, allownone=True)
    bar_alpha = NumericProperty(1.)

    def _set_viewport_size(self, instance, value):
        self.viewport_size = value

    def on__viewport(self, instance, value):
        if value:
            value.bind(size=self._set_viewport_size)
            self.viewport_size = value.size

    def __init__(self, **kwargs):
        self._touch = None
        self._trigger_update_from_scroll = Clock.create_trigger(
            self.update_from_scroll, -1)
        super(ScrollView, self).__init__(**kwargs)
        if self.effect_x is None and self.effect_cls is not None:
            self.effect_x = self.effect_cls(target_widget=self._viewport)
        if self.effect_y is None and self.effect_cls is not None:
            self.effect_y = self.effect_cls(target_widget=self._viewport)
        self.bind(
            view_width=self._update_effect_x_bounds,
            view_height=self._update_effect_y_bounds,
            view_y=self._update_effect_y_bounds,
            viewport_size=self._update_effect_bounds,
            _viewport=self._update_effect_widget,
            scroll_x=self._trigger_update_from_scroll,
            scroll_y=self._trigger_update_from_scroll,
            pos=self._trigger_update_from_scroll,
            size=self._trigger_update_from_scroll)

        self._update_effect_widget()
        self._update_effect_x_bounds()
        self._update_effect_y_bounds()

    def on_effect_x(self, instance, value):
        if value:
            value.bind(scroll=self._update_effect_x)
            value.target_widget = self._viewport

    def on_effect_y(self, instance, value):
        if value:
            value.bind(scroll=self._update_effect_y)
            value.target_widget = self._viewport

    def on_effect_cls(self, instance, cls):
        self.effect_x = self.effect_cls(target_widget=self._viewport)
        self.effect_x.bind(scroll=self._update_effect_x)
        self.effect_y = self.effect_cls(target_widget=self._viewport)
        self.effect_y.bind(scroll=self._update_effect_y)

    def _update_effect_widget(self, *args):
        if self.effect_x:
            self.effect_x.target_widget = self._viewport
        if self.effect_y:
            self.effect_y.target_widget = self._viewport

    def _update_effect_x_bounds(self, *args):
        if not self._viewport or not self.effect_x:
            return
        if self.scroll_proportionate:
            self.effect_x.min = 0
            self.effect_x.max = self.viewport_size[0] - self.view_width
            self.effect_x.value = self.effect_x.max * self.scroll_x
        else:
            self.effect_x.min = -(self.viewport_size[0] - self.view_width)
            self.effect_x.max = 0
            self.effect_x.value = self.effect_x.min * self.scroll_x

    def _update_effect_y_bounds(self, *args):
        if not self._viewport or not self.effect_y:
            return
        if self.scroll_proportionate:
            self.effect_y.min = 0
            self.effect_y.max = self.viewport_size[1] - self.view_height
            self.effect_y.value = self.effect_y.max * self.scroll_y
        else:
            self.effect_y.min = -(self.viewport_size[1] - self.view_height)
            self.effect_y.max = 0
            self.effect_y.value = self.effect_y.min * self.scroll_y

    def _update_effect_bounds(self, *args):
        if not self._viewport:
            return
        if self.effect_x:
            self._update_effect_x_bounds()
        if self.effect_y:
            self._update_effect_y_bounds()

    def _update_effect_x(self, *args):
        vp = self._viewport
        if not vp or not self.effect_x:
            return
        sw = vp.width - self.view_width
        if sw < 1:
            return
        sx = self.effect_x.scroll / float(sw)
        if not self.scroll_proportionate:
            sx *= -1
        self.scroll_x = sx
        self._trigger_update_from_scroll()

    def _update_effect_y(self, *args):
        vp = self._viewport
        if not vp or not self.effect_y:
            return
        sh = vp.height - self.view_height
        if sh < 1:
            return
        sy = self.effect_y.scroll / float(sh)
        if not self.scroll_proportionate:
            sy *= -1
        self.scroll_y = sy
        self._trigger_update_from_scroll()

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            touch.ud[self._get_uid('svavoid')] = True
            return
        if self.disabled:
            return True
        outside_bar = (touch.pos[0] <= self.view_width + self.x and
                       touch.pos[1] >= self.view_y + self.y)
        if (self._touch or (not (self.do_scroll_x or self.do_scroll_y)) or
            (self.scroll_on_bar_only and outside_bar and
             'button' in touch.profile and
             not touch.button.startswith('scroll'))):
            return super(ScrollView, self).on_touch_down(touch)

        # handle mouse scrolling, only if the viewport size is bigger than the
        # scrollview size, and if the user allowed to do it
        vp = self._viewport
        if vp and 'button' in touch.profile and \
            touch.button.startswith('scroll'):
            btn = touch.button
            m = self.scroll_distance
            prop = self.scroll_proportionate

            if (self.do_scroll_x and vp.width >
                self.view_width and btn in ('scrollleft', 'scrollright')):
                width = self.view_width
                if prop:
                    dx = m / float(width - width * self.hbar[1])
                else:
                    dx = m / float(width)
                if btn == 'scrollleft':
                    dx *= -1
                self.scroll_x = min(max(self.scroll_x + dx, 0.), 1.)
                self._trigger_update_from_scroll()
                touch.ud[self._get_uid('svavoid')] = True
                return True
            elif (self.do_scroll_y and vp.height >
                self.view_height and btn in ('scrolldown', 'scrollup')):
                height = self.view_height
                if prop:
                    dy = m / float(height - height * self.vbar[1])
                    if btn == 'scrollup':
                        dy *= -1
                else:
                    dy = m / float(height)
                    if btn == 'scrolldown':
                        dy *= -1
                self.scroll_y = min(max(self.scroll_y + dy, 0.), 1.)
                self._trigger_update_from_scroll()
                touch.ud[self._get_uid('svavoid')] = True
                return True

        # no mouse scrolling, so the user is going to drag the scrollview with
        # this touch.
        self._touch = touch
        uid = self._get_uid()
        touch.grab(self)
        scroll_on_bar_only = self.scroll_on_bar_only
        x_scrolling = (touch.pos[1] < self.view_y + self.y or
                       not scroll_on_bar_only)
        y_scrolling = (touch.pos[0] > self.view_width + self.x or
                       not scroll_on_bar_only)
        prop = self.scroll_proportionate  # if True, no effect
        touch.ud[uid] = {
            'mode': 'unknown',
            'dx': 0,
            'dy': 0,
            'user_stopped': False,
            'time': touch.time_start,
            'y_scrolling': y_scrolling,  # whether the y is allowed to scroll
            'x_scrolling': x_scrolling}  # whether the x is allowed to scroll
        if self.do_scroll_x and self.effect_x and x_scrolling and not prop:
            self.effect_x.start(touch.x)
        if self.do_scroll_y and self.effect_y and y_scrolling and not prop:
            self.effect_y.start(touch.y)
        if outside_bar:
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
        x_scrolling = ud['x_scrolling']
        y_scrolling = ud['y_scrolling']
        prop = self.scroll_proportionate

        # check if the minimum distance has been travelled
        if mode == 'unknown' or mode == 'scroll':
            if self.do_scroll_x and self.effect_x and x_scrolling:
                width = self.view_width
                if prop and width:
                    dx = touch.dx / float(width - width * self.hbar[1])
                    self.scroll_x = min(max(self.scroll_x + dx, 0.), 1.)
                    self._trigger_update_from_scroll()
                else:
                    self.effect_x.update(touch.x)
            if self.do_scroll_y and self.effect_y and y_scrolling:
                height = self.view_height
                if prop and height:
                    dy = touch.dy / float(height - height * self.vbar[1])
                    self.scroll_y = min(max(self.scroll_y + dy, 0.), 1.)
                    self._trigger_update_from_scroll()
                else:
                    self.effect_y.update(touch.y)

        if mode == 'unknown':
            ud['dx'] += abs(touch.dx)
            ud['dy'] += abs(touch.dy)
            if ud['dx'] > self.scroll_distance:
                if not self.do_scroll_x:
                    self._change_touch_mode()
                    return
                mode = 'scroll'

            if ud['dy'] > self.scroll_distance:
                if not self.do_scroll_y:
                    self._change_touch_mode()
                    return
                mode = 'scroll'
            ud['mode'] = mode

        if mode == 'scroll':
            ud['dt'] = touch.time_update - ud['time']
            ud['time'] = touch.time_update
            ud['user_stopped'] = True

        return True

    def on_touch_up(self, touch):
        if self._get_uid('svavoid') in touch.ud:
            return

        if self in [x() for x in touch.grab_list]:
            touch.ungrab(self)
            self._touch = None
            uid = self._get_uid()
            ud = touch.ud[uid]
            x_scrolling = ud['x_scrolling']
            y_scrolling = ud['y_scrolling']
            prop = self.scroll_proportionate
            if self.do_scroll_x and self.effect_x and x_scrolling and not prop:
                self.effect_x.stop(touch.x)
            if self.do_scroll_y and self.effect_y and y_scrolling and not prop:
                self.effect_y.stop(touch.y)
            if ud['mode'] == 'unknown':
                # we must do the click at least..
                # only send the click if it was not a click to stop
                # autoscrolling
                if not ud['user_stopped']:
                    super(ScrollView, self).on_touch_down(touch)
                Clock.schedule_once(partial(self._do_touch_up, touch), .1)
        else:
            if self._touch is not touch and self.uid not in touch.ud:
                super(ScrollView, self).on_touch_up(touch)

        # if we do mouse scrolling, always accept it
        if 'button' in touch.profile and touch.button.startswith('scroll'):
            return True

        return self._get_uid() in touch.ud

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

        # update from size_hint
        width = self.view_width
        height = self.view_height
        if vp.size_hint_x is not None:
            vp.width = vp.size_hint_x * width
        if vp.size_hint_y is not None:
            vp.height = vp.size_hint_y * height

        if vp.width > width:
            sw = vp.width - width
            x = self.x - self.scroll_x * sw
        else:
            x = self.x
        if vp.height > height:
            sh = vp.height - height
            y = self.y - self.scroll_y * sh + self.view_y
        else:
            y = self.top - vp.height
        vp.pos = x, y

        # new in 1.2.0, show bar when scrolling happen
        # and slowly remove them when no scroll is happening.
        self.bar_alpha = 1.
        Animation.stop_all(self, 'bar_alpha')
        Clock.unschedule(self._start_decrease_alpha)
        if not self.bar_perm:
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
        widget.bind(size=self._trigger_update_from_scroll)
        self._trigger_update_from_scroll()

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
        if ud['mode'] != 'unknown' or ud['user_stopped']:
            return
        x_scrolling = ud['x_scrolling']
        y_scrolling = ud['y_scrolling']
        if self.do_scroll_x and self.effect_x and x_scrolling:
            self.effect_x.cancel()
        if self.do_scroll_y and self.effect_y and y_scrolling:
            self.effect_y.cancel()
        # XXX the next line was in the condition. But this stop
        # the possibily to "drag" an object out of the scrollview in the
        # non-used direction: if you have an horizontal scrollview, a
        # vertical gesture will not "stop" the scroll view to look for an
        # horizontal gesture, until the timeout is done.
        # and touch.dx + touch.dy == 0:
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


if __name__ == '__main__':
    from kivy.app import App

    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.button import Button

    class ScrollViewApp(App):

        def build(self):
            layout1 = GridLayout(cols=4, spacing=10, size_hint=(None, None))
            layout1.bind(minimum_height=layout1.setter('height'),
                        minimum_width=layout1.setter('width'))
            for i in range(40):
                btn = Button(text=str(i), size_hint=(None, None),
                             size=(200, 100))
                layout1.add_widget(btn)
            scrollview1 = ScrollView(bar_width='2dp', bar_perm=False,
                                     scroll_proportionate=False,
                                     scroll_on_bar_only=False)
            scrollview1.add_widget(layout1)

            layout2 = GridLayout(cols=4, spacing=10, size_hint=(None, None))
            layout2.bind(minimum_height=layout2.setter('height'),
                        minimum_width=layout2.setter('width'))
            for i in range(40):
                btn = Button(text=str(i), size_hint=(None, None),
                             size=(200, 100))
                layout2.add_widget(btn)
            scrollview2 = ScrollView(bar_width='16dp', bar_perm=True,
                                     scroll_proportionate=True,
                                     scroll_on_bar_only=True)
            scrollview2.add_widget(layout2)

            root = GridLayout(cols=2)
            root.add_widget(scrollview1)
            root.add_widget(scrollview2)
            return root

    ScrollViewApp().run()
