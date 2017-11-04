'''
ScrollView
==========

.. versionadded:: 1.0.4

The :class:`ScrollView` widget provides a scrollable/pannable viewport that is
clipped at the scrollview's bounding box.


Scrolling Behavior
------------------

The ScrollView accepts only one child and applies a viewport/window to
it according to the :attr:`~ScrollView.scroll_x` and
:attr:`~ScrollView.scroll_y` properties. Touches are analyzed to
determine if the user wants to scroll or control the child in some
other manner: you cannot do both at the same time. To determine if
interaction is a scrolling gesture, these properties are used:

    - :attr:`~ScrollView.scroll_distance`: the minimum distance to travel,
      defaults to 20 pixels.
    - :attr:`~ScrollView.scroll_timeout`: the maximum time period, defaults
      to 55 milliseconds.

If a touch travels :attr:`~ScrollView.scroll_distance` pixels within the
:attr:`~ScrollView.scroll_timeout` period, it is recognized as a scrolling
gesture and translation (scroll/pan) will begin. If the timeout occurs, the
touch down event is dispatched to the child instead (no translation).

The default value for those settings can be changed in the configuration file::

    [widgets]
    scroll_timeout = 250
    scroll_distance = 20

.. versionadded:: 1.1.1

    ScrollView now animates scrolling in Y when a mousewheel is used.


Limiting to the X or Y Axis
---------------------------

By default, the ScrollView allows scrolling along both the X and Y axes. You
can explicitly disable scrolling on an axis by setting the
:attr:`~ScrollView.do_scroll_x` or :attr:`~ScrollView.do_scroll_y` properties
to False.


Managing the Content Size and Position
--------------------------------------

The ScrollView manages the position of its children similarly to a
:class:`~kivy.uix.relativelayout.RelativeLayout` but does not use the
:attr:`~kivy.uix.widget.Widget.size_hint`. You must
carefully specify the :attr:`~kivy.uix.widget.Widget.size` of your content to
get the desired scroll/pan effect.

By default, the :attr:`~kivy.uix.widget.Widget.size_hint` is (1, 1), so the
content size will fit your ScrollView
exactly (you will have nothing to scroll). You must deactivate at least one of
the size_hint instructions (x or y) of the child to enable scrolling.
Setting :attr:`~kivy.uix.widget.Widget.size_hint_min` to not be None will
also enable scrolling for that dimension when the :class:`ScrollView` is
smaller than the minimum size.

To scroll a :class:`~kivy.uix.gridlayout.GridLayout` on it's Y-axis/vertically,
set the child's width  to that of the ScrollView (size_hint_x=1), and set
the size_hint_y property to None::

    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.button import Button
    from kivy.uix.scrollview import ScrollView
    from kivy.core.window import Window
    from kivy.app import runTouchApp

    layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
    # Make sure the height is such that there is something to scroll.
    layout.bind(minimum_height=layout.setter('height'))
    for i in range(100):
        btn = Button(text=str(i), size_hint_y=None, height=40)
        layout.add_widget(btn)
    root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
    root.add_widget(layout)

    runTouchApp(root)

Overscroll Effects
------------------

.. versionadded:: 1.7.0

When scrolling would exceed the bounds of the :class:`ScrollView`, it
uses a :class:`~kivy.effects.scroll.ScrollEffect` to handle the
overscroll. These effects can perform actions like bouncing back,
changing opacity, or simply preventing scrolling beyond the normal
boundaries. Note that complex effects may perform many computations,
which can be slow on weaker hardware.

You can change what effect is being used by setting
:attr:`~ScrollView.effect_cls` to any effect class. Current options
include:

    - :class:`~kivy.effects.scroll.ScrollEffect`: Does not allow
      scrolling beyond the :class:`ScrollView` boundaries.
    - :class:`~kivy.effects.dampedscroll.DampedScrollEffect`: The
      current default. Allows the user to scroll beyond the normal
      boundaries, but has the content spring back once the
      touch/click is released.
    - :class:`~kivy.effects.opacityscroll.OpacityScrollEffect`: Similar
      to the :class:`~kivy.effect.dampedscroll.DampedScrollEffect`, but
      also reduces opacity during overscroll.

You can also create your own scroll effect by subclassing one of these,
then pass it as the :attr:`~ScrollView.effect_cls` in the same way.

Alternatively, you can set :attr:`~ScrollView.effect_x` and/or
:attr:`~ScrollView.effect_y` to an *instance* of the effect you want to
use. This will override the default effect set in
:attr:`~ScrollView.effect_cls`.

All the effects are located in the :mod:`kivy.effects`.

'''

__all__ = ('ScrollView', )

from functools import partial
from kivy.animation import Animation
from kivy.compat import string_types
from kivy.config import Config
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.uix.stencilview import StencilView
from kivy.metrics import sp, dp
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.properties import NumericProperty, BooleanProperty, AliasProperty, \
    ObjectProperty, ListProperty, ReferenceListProperty, OptionProperty
from kivy.uix.behaviors import FocusBehavior


# When we are generating documentation, Config doesn't exist
_scroll_timeout = _scroll_distance = 0
if Config:
    _scroll_timeout = Config.getint('widgets', 'scroll_timeout')
    _scroll_distance = '{}sp'.format(Config.getint('widgets',
                                                   'scroll_distance'))


class ScrollView(StencilView):
    '''ScrollView class. See module documentation for more information.

    :Events:
        `on_scroll_start`
            Generic event fired when scrolling starts from touch.
        `on_scroll_move`
            Generic event fired when scrolling move from touch.
        `on_scroll_stop`
            Generic event fired when scrolling stops from touch.

    .. versionchanged:: 1.9.0
        `on_scroll_start`, `on_scroll_move` and `on_scroll_stop` events are
        now dispatched when scrolling to handle nested ScrollViews.

    .. versionchanged:: 1.7.0
        `auto_scroll`, `scroll_friction`, `scroll_moves`, `scroll_stoptime' has
        been deprecated, use :attr:`effect_cls` instead.
    '''

    scroll_distance = NumericProperty(_scroll_distance)
    '''Distance to move before scrolling the :class:`ScrollView`, in pixels. As
    soon as the distance has been traveled, the :class:`ScrollView` will start
    to scroll, and no touch event will go to children.
    It is advisable that you base this value on the dpi of your target device's
    screen.

    :attr:`scroll_distance` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 20 (pixels), according to the default value in user
    configuration.
    '''

    scroll_wheel_distance = NumericProperty('20sp')
    '''Distance to move when scrolling with a mouse wheel.
    It is advisable that you base this value on the dpi of your target device's
    screen.

    .. versionadded:: 1.8.0

    :attr:`scroll_wheel_distance` is a
    :class:`~kivy.properties.NumericProperty` , defaults to 20 pixels.
    '''

    scroll_timeout = NumericProperty(_scroll_timeout)
    '''Timeout allowed to trigger the :attr:`scroll_distance`, in milliseconds.
    If the user has not moved :attr:`scroll_distance` within the timeout,
    the scrolling will be disabled, and the touch event will go to the
    children.

    :attr:`scroll_timeout` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 55 (milliseconds) according to the default value in user
    configuration.

    .. versionchanged:: 1.5.0
        Default value changed from 250 to 55.
    '''

    scroll_x = NumericProperty(0.)
    '''X scrolling value, between 0 and 1. If 0, the content's left side will
    touch the left side of the ScrollView. If 1, the content's right side will
    touch the right side.

    This property is controled by :class:`ScrollView` only if
    :attr:`do_scroll_x` is True.

    :attr:`scroll_x` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    scroll_y = NumericProperty(1.)
    '''Y scrolling value, between 0 and 1. If 0, the content's bottom side will
    touch the bottom side of the ScrollView. If 1, the content's top side will
    touch the top side.

    This property is controled by :class:`ScrollView` only if
    :attr:`do_scroll_y` is True.

    :attr:`scroll_y` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.
    '''

    do_scroll_x = BooleanProperty(True)
    '''Allow scroll on X axis.

    :attr:`do_scroll_x` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
    '''

    do_scroll_y = BooleanProperty(True)
    '''Allow scroll on Y axis.

    :attr:`do_scroll_y` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to True.
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

    :attr:`do_scroll` is a :class:`~kivy.properties.AliasProperty` of
    (:attr:`do_scroll_x` + :attr:`do_scroll_y`)
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

    :attr:`vbar` is a :class:`~kivy.properties.AliasProperty`, readonly.
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

    :attr:`vbar` is a :class:`~kivy.properties.AliasProperty`, readonly.
    '''

    bar_color = ListProperty([.7, .7, .7, .9])
    '''Color of horizontal / vertical scroll bar, in RGBA format.

    .. versionadded:: 1.2.0

    :attr:`bar_color` is a :class:`~kivy.properties.ListProperty` and defaults
    to [.7, .7, .7, .9].
    '''

    bar_inactive_color = ListProperty([.7, .7, .7, .2])
    '''Color of horizontal / vertical scroll bar (in RGBA format), when no
    scroll is happening.

    .. versionadded:: 1.9.0

    :attr:`bar_inactive_color` is a
    :class:`~kivy.properties.ListProperty` and defaults to [.7, .7, .7, .2].
    '''

    bar_width = NumericProperty('2dp')
    '''Width of the horizontal / vertical scroll bar. The width is interpreted
    as a height for the horizontal bar.

    .. versionadded:: 1.2.0

    :attr:`bar_width` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 2.
    '''

    bar_pos_x = OptionProperty('bottom', options=('top', 'bottom'))
    '''Which side of the ScrollView the horizontal scroll bar should go
    on. Possible values are 'top' and 'bottom'.

    .. versionadded:: 1.8.0

    :attr:`bar_pos_x` is an :class:`~kivy.properties.OptionProperty`,
    defaults to 'bottom'.

    '''

    bar_pos_y = OptionProperty('right', options=('left', 'right'))
    '''Which side of the ScrollView the vertical scroll bar should go
    on. Possible values are 'left' and 'right'.

    .. versionadded:: 1.8.0

    :attr:`bar_pos_y` is an :class:`~kivy.properties.OptionProperty` and
    defaults to 'right'.

    '''

    bar_pos = ReferenceListProperty(bar_pos_x, bar_pos_y)
    '''Which side of the scroll view to place each of the bars on.

    :attr:`bar_pos` is a :class:`~kivy.properties.ReferenceListProperty` of
    (:attr:`bar_pos_x`, :attr:`bar_pos_y`)
    '''

    bar_margin = NumericProperty(0)
    '''Margin between the bottom / right side of the scrollview when drawing
    the horizontal / vertical scroll bar.

    .. versionadded:: 1.2.0

    :attr:`bar_margin` is a :class:`~kivy.properties.NumericProperty`, default
    to 0
    '''

    effect_cls = ObjectProperty(DampedScrollEffect, allownone=True)
    '''Class effect to instantiate for X and Y axis.

    .. versionadded:: 1.7.0

    :attr:`effect_cls` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to :class:`DampedScrollEffect`.

    .. versionchanged:: 1.8.0
        If you set a string, the :class:`~kivy.factory.Factory` will be used to
        resolve the class.

    '''

    effect_x = ObjectProperty(None, allownone=True)
    '''Effect to apply for the X axis. If None is set, an instance of
    :attr:`effect_cls` will be created.

    .. versionadded:: 1.7.0

    :attr:`effect_x` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None.
    '''

    effect_y = ObjectProperty(None, allownone=True)
    '''Effect to apply for the Y axis. If None is set, an instance of
    :attr:`effect_cls` will be created.

    .. versionadded:: 1.7.0

    :attr:`effect_y` is an :class:`~kivy.properties.ObjectProperty` and
    defaults to None, read-only.
    '''

    viewport_size = ListProperty([0, 0])
    '''(internal) Size of the internal viewport. This is the size of your only
    child in the scrollview.
    '''

    scroll_type = OptionProperty(['content'], options=(['content'], ['bars'],
                                 ['bars', 'content'], ['content', 'bars']))
    '''Sets the type of scrolling to use for the content of the scrollview.
    Available options are: ['content'], ['bars'], ['bars', 'content'].

    +---------------------+------------------------------------------------+
    | ['content']         | Content is scrolled by dragging or swiping the |
    |                     | content directly.                              |
    +---------------------+------------------------------------------------+
    | ['bars']            | Content is scrolled by dragging or swiping the |
    |                     | scoll bars.                                    |
    +---------------------+------------------------------------------------+
    | ['bars', 'content'] | Content is scrolled by either of the above     |
    |                     | methods.                                       |
    +---------------------+------------------------------------------------+

    .. versionadded:: 1.8.0

    :attr:`scroll_type` is an :class:`~kivy.properties.OptionProperty` and
    defaults to ['content'].
    '''

    # private, for internal use only

    _viewport = ObjectProperty(None, allownone=True)
    _bar_color = ListProperty([0, 0, 0, 0])
    _effect_x_start_width = None
    _effect_y_start_height = None
    _update_effect_bounds_ev = None
    _bind_inactive_bar_color_ev = None

    def _set_viewport_size(self, instance, value):
        self.viewport_size = value

    def on__viewport(self, instance, value):
        if value:
            value.bind(size=self._set_viewport_size)
            self.viewport_size = value.size

    __events__ = ('on_scroll_start', 'on_scroll_move', 'on_scroll_stop')

    def __init__(self, **kwargs):
        self._touch = None
        self._trigger_update_from_scroll = Clock.create_trigger(
            self.update_from_scroll, -1)
        # create a specific canvas for the viewport
        from kivy.graphics import PushMatrix, Translate, PopMatrix, Canvas
        self.canvas_viewport = Canvas()
        self.canvas = Canvas()
        with self.canvas_viewport.before:
            PushMatrix()
            self.g_translate = Translate(0, 0)
        with self.canvas_viewport.after:
            PopMatrix()

        super(ScrollView, self).__init__(**kwargs)

        self.register_event_type('on_scroll_start')
        self.register_event_type('on_scroll_move')
        self.register_event_type('on_scroll_stop')

        # now add the viewport canvas to our canvas
        self.canvas.add(self.canvas_viewport)

        effect_cls = self.effect_cls
        if isinstance(effect_cls, string_types):
            effect_cls = Factory.get(effect_cls)
        if self.effect_x is None and effect_cls is not None:
            self.effect_x = effect_cls(target_widget=self._viewport)
        if self.effect_y is None and effect_cls is not None:
            self.effect_y = effect_cls(target_widget=self._viewport)

        trigger_update_from_scroll = self._trigger_update_from_scroll
        update_effect_widget = self._update_effect_widget
        update_effect_x_bounds = self._update_effect_x_bounds
        update_effect_y_bounds = self._update_effect_y_bounds
        fbind = self.fbind
        fbind('width', update_effect_x_bounds)
        fbind('height', update_effect_y_bounds)
        fbind('viewport_size', self._update_effect_bounds)
        fbind('_viewport', update_effect_widget)
        fbind('scroll_x', trigger_update_from_scroll)
        fbind('scroll_y', trigger_update_from_scroll)
        fbind('pos', trigger_update_from_scroll)
        fbind('size', trigger_update_from_scroll)
        fbind('scroll_y', self._update_effect_bounds)
        fbind('scroll_x', self._update_effect_bounds)

        update_effect_widget()
        update_effect_x_bounds()
        update_effect_y_bounds()

    def on_effect_x(self, instance, value):
        if value:
            value.bind(scroll=self._update_effect_x)
            value.target_widget = self._viewport

    def on_effect_y(self, instance, value):
        if value:
            value.bind(scroll=self._update_effect_y)
            value.target_widget = self._viewport

    def on_effect_cls(self, instance, cls):
        if isinstance(cls, string_types):
            cls = Factory.get(cls)
        self.effect_x = cls(target_widget=self._viewport)
        self.effect_x.bind(scroll=self._update_effect_x)
        self.effect_y = cls(target_widget=self._viewport)
        self.effect_y.bind(scroll=self._update_effect_y)

    def _update_effect_widget(self, *args):
        if self.effect_x:
            self.effect_x.target_widget = self._viewport
        if self.effect_y:
            self.effect_y.target_widget = self._viewport

    def _update_effect_x_bounds(self, *args):
        if not self._viewport or not self.effect_x:
            return
        self.effect_x.min = -(self.viewport_size[0] - self.width)
        self.effect_x.max = 0
        self.effect_x.value = self.effect_x.min * self.scroll_x

    def _update_effect_y_bounds(self, *args):
        if not self._viewport or not self.effect_y:
            return
        self.effect_y.min = -(self.viewport_size[1] - self.height)
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

        if self.effect_x.is_manual:
            sw = vp.width - self._effect_x_start_width
        else:
            sw = vp.width - self.width
        if sw < 1:
            return
        sx = self.effect_x.scroll / float(sw)
        self.scroll_x = -sx
        self._trigger_update_from_scroll()

    def _update_effect_y(self, *args):
        vp = self._viewport
        if not vp or not self.effect_y:
            return
        if self.effect_y.is_manual:
            sh = vp.height - self._effect_y_start_height
        else:
            sh = vp.height - self.height
        if sh < 1:
            return
        sy = self.effect_y.scroll / float(sh)
        self.scroll_y = -sy
        self._trigger_update_from_scroll()

    def to_local(self, x, y, **k):
        tx, ty = self.g_translate.xy
        return x - tx, y - ty

    def to_parent(self, x, y, **k):
        tx, ty = self.g_translate.xy
        return x + tx, y + ty

    def _apply_transform(self, m, pos=None):
        tx, ty = self.g_translate.xy
        m.translate(tx, ty, 0)
        return super(ScrollView, self)._apply_transform(m, (0, 0))

    def simulate_touch_down(self, touch):
        # at this point the touch is in parent coords
        touch.push()
        touch.apply_transform_2d(self.to_local)
        ret = super(ScrollView, self).on_touch_down(touch)
        touch.pop()
        return ret

    def on_touch_down(self, touch):
        if self.dispatch('on_scroll_start', touch):
            self._touch = touch
            touch.grab(self)
            return True

    def _touch_in_handle(self, pos, size, touch):
        x, y = pos
        width, height = size
        return x <= touch.x <= x + width and y <= touch.y <= y + height

    def on_scroll_start(self, touch, check_children=True):
        if check_children:
            touch.push()
            touch.apply_transform_2d(self.to_local)
            if self.dispatch_children('on_scroll_start', touch):
                touch.pop()
                return True
            touch.pop()

        if not self.collide_point(*touch.pos):
            touch.ud[self._get_uid('svavoid')] = True
            return
        if self.disabled:
            return True
        if self._touch or (not (self.do_scroll_x or self.do_scroll_y)):
            return self.simulate_touch_down(touch)

        # handle mouse scrolling, only if the viewport size is bigger than the
        # scrollview size, and if the user allowed to do it
        vp = self._viewport
        if not vp:
            return True
        scroll_type = self.scroll_type
        ud = touch.ud
        scroll_bar = 'bars' in scroll_type

        # check if touch is in bar_x(horizontal) or bar_y(vertical)
        width_scrollable = vp.width > self.width
        height_scrollable = vp.height > self.height

        d = {'bottom': touch.y - self.y - self.bar_margin,
             'top': self.top - touch.y - self.bar_margin,
             'left': touch.x - self.x - self.bar_margin,
             'right': self.right - touch.x - self.bar_margin}

        ud['in_bar_x'] = (scroll_bar and width_scrollable and
                             (0 <= d[self.bar_pos_x] <= self.bar_width))
        ud['in_bar_y'] = (scroll_bar and height_scrollable and
                             (0 <= d[self.bar_pos_y] <= self.bar_width))

        if vp and 'button' in touch.profile and \
                touch.button.startswith('scroll'):
            btn = touch.button
            m = self.scroll_wheel_distance
            e = None

            if ((btn == 'scrolldown' and self.scroll_y >= 1) or
                (btn == 'scrollup' and self.scroll_y <= 0) or
                (btn == 'scrollleft' and self.scroll_x >= 1) or
                    (btn == 'scrollright' and self.scroll_x <= 0)):
                return False

            if (self.effect_x and self.do_scroll_y and height_scrollable and
                    btn in ('scrolldown', 'scrollup')):
                e = self.effect_x if ud['in_bar_x'] else self.effect_y

            elif (self.effect_y and self.do_scroll_x and width_scrollable and
                    btn in ('scrollleft', 'scrollright')):
                e = self.effect_y if ud['in_bar_y'] else self.effect_x

            if e:
                if btn in ('scrolldown', 'scrollleft'):
                    e.value = max(e.value - m, e.min)
                    e.velocity = 0
                elif btn in ('scrollup', 'scrollright'):
                    e.value = min(e.value + m, e.max)
                    e.velocity = 0
                touch.ud[self._get_uid('svavoid')] = True
                e.trigger_velocity_update()
            return True

        in_bar = ud['in_bar_x'] or ud['in_bar_y']
        if scroll_type == ['bars'] and not in_bar:
            return self.simulate_touch_down(touch)

        if in_bar:
            if (ud['in_bar_y'] and not
                    self._touch_in_handle(
                        self._handle_y_pos, self._handle_y_size, touch)):
                self.scroll_y = (touch.y - self.y) / self.height
            elif (ud['in_bar_x'] and not
                    self._touch_in_handle(
                        self._handle_x_pos, self._handle_x_size, touch)):
                self.scroll_x = (touch.x - self.x) / self.width

        # no mouse scrolling, so the user is going to drag the scrollview with
        # this touch.
        self._touch = touch
        uid = self._get_uid()

        ud[uid] = {
            'mode': 'unknown',
            'dx': 0,
            'dy': 0,
            'user_stopped': in_bar,
            'frames': Clock.frames,
            'time': touch.time_start}

        if self.do_scroll_x and self.effect_x and not ud['in_bar_x']:
            self._effect_x_start_width = self.width
            self.effect_x.start(touch.x)
            self._scroll_x_mouse = self.scroll_x
        if self.do_scroll_y and self.effect_y and not ud['in_bar_y']:
            self._effect_y_start_height = self.height
            self.effect_y.start(touch.y)
            self._scroll_y_mouse = self.scroll_y

        if not in_bar:
            Clock.schedule_once(self._change_touch_mode,
                                self.scroll_timeout / 1000.)
        return True

    def on_touch_move(self, touch):
        if self._touch is not touch:
            # don't pass on touch to children if outside the sv
            if self.collide_point(*touch.pos):
                # touch is in parent
                touch.push()
                touch.apply_transform_2d(self.to_local)
                super(ScrollView, self).on_touch_move(touch)
                touch.pop()
            return self._get_uid() in touch.ud
        if touch.grab_current is not self:
            return True

        if touch.ud.get(self._get_uid()) is None:
            # don't pass on touch to children if outside the sv
            if self.collide_point(*touch.pos):
                return super(ScrollView, self).on_touch_move(touch)
            return False

        touch.ud['sv.handled'] = {'x': False, 'y': False}
        if self.dispatch('on_scroll_move', touch):
            return True

    def on_scroll_move(self, touch):
        if self._get_uid('svavoid') in touch.ud:
            return False

        touch.push()
        touch.apply_transform_2d(self.to_local)
        if self.dispatch_children('on_scroll_move', touch):
            touch.pop()
            return True
        touch.pop()

        rv = True

        # By default this touch can be used to defocus currently focused
        # widget, like any touch outside of ScrollView.
        touch.ud['sv.can_defocus'] = True

        uid = self._get_uid()
        if uid not in touch.ud:
            self._touch = False
            return self.on_scroll_start(touch, False)
        ud = touch.ud[uid]

        # check if the minimum distance has been travelled
        if ud['mode'] == 'unknown':
            if not self.do_scroll_x and not self.do_scroll_y:
                # touch is in parent, but _change expects window coords
                touch.push()
                touch.apply_transform_2d(self.to_local)
                touch.apply_transform_2d(self.to_window)
                self._change_touch_mode()
                touch.pop()
                return
            ud['dx'] += abs(touch.dx)
            ud['dy'] += abs(touch.dy)
            if ((ud['dx'] > self.scroll_distance and self.do_scroll_x) or
                    (ud['dy'] > self.scroll_distance and self.do_scroll_y)):
                ud['mode'] = 'scroll'

        if ud['mode'] == 'scroll':
            if not touch.ud['sv.handled']['x'] and self.do_scroll_x \
                    and self.effect_x:
                width = self.width
                if touch.ud.get('in_bar_x', False):
                    dx = touch.dx / float(width - width * self.hbar[1])
                    self.scroll_x = min(max(self.scroll_x + dx, 0.), 1.)
                    self._trigger_update_from_scroll()
                else:
                    if self.scroll_type != ['bars']:
                        self.effect_x.update(touch.x)
                if self.scroll_x < 0 or self.scroll_x > 1:
                    rv = False
                else:
                    touch.ud['sv.handled']['x'] = True
                # Touch resulted in scroll should not defocus focused widget
                touch.ud['sv.can_defocus'] = False
            if not touch.ud['sv.handled']['y'] and self.do_scroll_y \
                    and self.effect_y:
                height = self.height
                if touch.ud.get('in_bar_y', False):
                    dy = touch.dy / float(height - height * self.vbar[1])
                    self.scroll_y = min(max(self.scroll_y + dy, 0.), 1.)
                    self._trigger_update_from_scroll()
                else:
                    if self.scroll_type != ['bars']:
                        self.effect_y.update(touch.y)
                if self.scroll_y < 0 or self.scroll_y > 1:
                    rv = False
                else:
                    touch.ud['sv.handled']['y'] = True
                # Touch resulted in scroll should not defocus focused widget
                touch.ud['sv.can_defocus'] = False
            ud['dt'] = touch.time_update - ud['time']
            ud['time'] = touch.time_update
            ud['user_stopped'] = True
        return rv

    def on_touch_up(self, touch):
        uid = self._get_uid('svavoid')
        if self._touch is not touch and uid not in touch.ud:
            # don't pass on touch to children if outside the sv
            if self.collide_point(*touch.pos):
                # touch is in parents
                touch.push()
                touch.apply_transform_2d(self.to_local)
                if super(ScrollView, self).on_touch_up(touch):
                    touch.pop()
                    return True
                touch.pop()
            return False

        if self.dispatch('on_scroll_stop', touch):
            touch.ungrab(self)
            if not touch.ud.get('sv.can_defocus', True):
                # Focused widget should stay focused
                FocusBehavior.ignored_touch.append(touch)
            return True

    def on_scroll_stop(self, touch, check_children=True):
        self._touch = None

        if check_children:
            touch.push()
            touch.apply_transform_2d(self.to_local)
            if self.dispatch_children('on_scroll_stop', touch):
                touch.pop()
                return True
            touch.pop()

        if self._get_uid('svavoid') in touch.ud:
            return
        if self._get_uid() not in touch.ud:
            return False

        self._touch = None
        uid = self._get_uid()
        ud = touch.ud[uid]
        if self.do_scroll_x and self.effect_x:
            if not touch.ud.get('in_bar_x', False) and\
                    self.scroll_type != ['bars']:
                self.effect_x.stop(touch.x)
        if self.do_scroll_y and self.effect_y and\
                self.scroll_type != ['bars']:
            if not touch.ud.get('in_bar_y', False):
                self.effect_y.stop(touch.y)
        if ud['mode'] == 'unknown':
            # we must do the click at least..
            # only send the click if it was not a click to stop
            # autoscrolling
            if not ud['user_stopped']:
                self.simulate_touch_down(touch)
            Clock.schedule_once(partial(self._do_touch_up, touch), .2)

        ev = self._update_effect_bounds_ev
        if ev is None:
            ev = self._update_effect_bounds_ev = Clock.create_trigger(
                self._update_effect_bounds)
        ev()

        # if we do mouse scrolling, always accept it
        if 'button' in touch.profile and touch.button.startswith('scroll'):
            return True

        return self._get_uid() in touch.ud

    def scroll_to(self, widget, padding=10, animate=True):
        '''Scrolls the viewport to ensure that the given widget is visible,
        optionally with padding and animation. If animate is True (the
        default), then the default animation parameters will be used.
        Otherwise, it should be a dict containing arguments to pass to
        :class:`~kivy.animation.Animation` constructor.

        .. versionadded:: 1.9.1
        '''
        if not self.parent:
            return

        # if _viewport is layout and has pending operation, reschedule
        if hasattr(self._viewport, 'do_layout'):
            if self._viewport._trigger_layout.is_triggered:
                Clock.schedule_once(
                     lambda *dt: self.scroll_to(widget, padding, animate))
                return

        if isinstance(padding, (int, float)):
            padding = (padding, padding)

        pos = self.parent.to_widget(*widget.to_window(*widget.pos))
        cor = self.parent.to_widget(*widget.to_window(widget.right,
                                                      widget.top))

        dx = dy = 0

        if pos[1] < self.y:
            dy = self.y - pos[1] + dp(padding[1])
        elif cor[1] > self.top:
            dy = self.top - cor[1] - dp(padding[1])

        if pos[0] < self.x:
            dx = self.x - pos[0] + dp(padding[0])
        elif cor[0] > self.right:
            dx = self.right - cor[0] - dp(padding[0])

        dsx, dsy = self.convert_distance_to_scroll(dx, dy)
        sxp = min(1, max(0, self.scroll_x - dsx))
        syp = min(1, max(0, self.scroll_y - dsy))

        if animate:
            if animate is True:
                animate = {'d': 0.2, 't': 'out_quad'}
            Animation.stop_all(self, 'scroll_x', 'scroll_y')
            Animation(scroll_x=sxp, scroll_y=syp, **animate).start(self)
        else:
            self.scroll_x = sxp
            self.scroll_y = syp

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
        :attr:`scroll_x` and :attr:`scroll_y`.

        This method is automatically called when one of the :attr:`scroll_x`,
        :attr:`scroll_y`, :attr:`pos` or :attr:`size` properties change, or
        if the size of the content changes.
        '''
        if not self._viewport:
            return
        vp = self._viewport

        # update from size_hint
        if vp.size_hint_x is not None:
            w = vp.size_hint_x * self.width
            if vp.size_hint_min_x is not None:
                w = max(w, vp.size_hint_min_x)
            if vp.size_hint_max_x is not None:
                w = min(w, vp.size_hint_max_x)
            vp.width = w
        if vp.size_hint_y is not None:
            h = vp.size_hint_y * self.height
            if vp.size_hint_min_y is not None:
                h = max(h, vp.size_hint_min_y)
            if vp.size_hint_max_y is not None:
                h = min(h, vp.size_hint_max_y)
            vp.height = h

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

        # from 1.8.0, we now use a matrix by default, instead of moving the
        # widget position behind. We set it here, but it will be a no-op most
        # of the time.
        vp.pos = 0, 0
        self.g_translate.xy = x, y

        # New in 1.2.0, show bar when scrolling happens and (changed in 1.9.0)
        # fade to bar_inactive_color when no scroll is happening.
        ev = self._bind_inactive_bar_color_ev
        if ev is None:
            ev = self._bind_inactive_bar_color_ev = Clock.create_trigger(
                self._bind_inactive_bar_color, .5)
        self.funbind('bar_inactive_color', self._change_bar_color)
        Animation.stop_all(self, '_bar_color')
        self.fbind('bar_color', self._change_bar_color)
        self._bar_color = self.bar_color
        ev()

    def _bind_inactive_bar_color(self, *l):
        self.funbind('bar_color', self._change_bar_color)
        self.fbind('bar_inactive_color', self._change_bar_color)
        Animation(
            _bar_color=self.bar_inactive_color,
            d=.5, t='out_quart').start(self)

    def _change_bar_color(self, inst, value):
        self._bar_color = value

    #
    # Private
    #
    def add_widget(self, widget, index=0):
        if self._viewport:
            raise Exception('ScrollView accept only one widget')
        canvas = self.canvas
        self.canvas = self.canvas_viewport
        super(ScrollView, self).add_widget(widget, index)
        self.canvas = canvas
        self._viewport = widget
        widget.bind(size=self._trigger_update_from_scroll,
                    size_hint_min=self._trigger_update_from_scroll)
        self._trigger_update_from_scroll()

    def remove_widget(self, widget):
        canvas = self.canvas
        self.canvas = self.canvas_viewport
        super(ScrollView, self).remove_widget(widget)
        self.canvas = canvas
        if widget is self._viewport:
            self._viewport = None

    def _get_uid(self, prefix='sv'):
        return '{0}.{1}'.format(prefix, self.uid)

    def _change_touch_mode(self, *largs):
        if not self._touch:
            return
        uid = self._get_uid()
        touch = self._touch
        if uid not in touch.ud:
            self._touch = False
            return
        ud = touch.ud[uid]
        if ud['mode'] != 'unknown' or ud['user_stopped']:
            return
        diff_frames = Clock.frames - ud['frames']

        # in order to be able to scroll on very slow devices, let at least 3
        # frames displayed to accumulate some velocity. And then, change the
        # touch mode. Otherwise, we might never be able to compute velocity,
        # and no way to scroll it. See #1464 and #1499
        if diff_frames < 3:
            Clock.schedule_once(self._change_touch_mode, 0)
            return

        if self.do_scroll_x and self.effect_x:
            self.effect_x.cancel()
        if self.do_scroll_y and self.effect_y:
            self.effect_y.cancel()
        # XXX the next line was in the condition. But this stop
        # the possibility to "drag" an object out of the scrollview in the
        # non-used direction: if you have an horizontal scrollview, a
        # vertical gesture will not "stop" the scroll view to look for an
        # horizontal gesture, until the timeout is done.
        # and touch.dx + touch.dy == 0:
        touch.ungrab(self)
        self._touch = None
        # touch is in window coords
        touch.push()
        touch.apply_transform_2d(self.to_widget)
        touch.apply_transform_2d(self.to_parent)
        self.simulate_touch_down(touch)
        touch.pop()
        return

    def _do_touch_up(self, touch, *largs):
        # touch is in window coords
        touch.push()
        touch.apply_transform_2d(self.to_widget)
        super(ScrollView, self).on_touch_up(touch)
        touch.pop()
        # don't forget about grab event!
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            # touch is in window coords
            touch.push()
            touch.apply_transform_2d(self.to_widget)
            super(ScrollView, self).on_touch_up(touch)
            touch.pop()
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
            scrollview1 = ScrollView(bar_width='2dp')
            scrollview1.add_widget(layout1)

            layout2 = GridLayout(cols=4, spacing=10, size_hint=(None, None))
            layout2.bind(minimum_height=layout2.setter('height'),
                         minimum_width=layout2.setter('width'))
            for i in range(40):
                btn = Button(text=str(i), size_hint=(None, None),
                             size=(200, 100))
                layout2.add_widget(btn)
            scrollview2 = ScrollView(scroll_type=['bars'],
                                     bar_width='9dp',
                                     scroll_wheel_distance=100)
            scrollview2.add_widget(layout2)

            root = GridLayout(cols=2)
            root.add_widget(scrollview1)
            root.add_widget(scrollview2)
            return root

    ScrollViewApp().run()
