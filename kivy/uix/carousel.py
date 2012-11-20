'''
Carousel
========

.. versionadded:: 1.4.0

The :class:`Carousel` widget provides the classic mobile-friendly carousel view
where you can swipe between slides.
You can add any content to the carousel and use it horizontally or verticaly.
The carousel can display pages in loop or not.

Example::

    class Example1(App):

        def build(self):
            carousel = Carousel(direction='right')
            for i in range(10):
                src = "http://placehold.it/480x270.png&text=slide-%d&.png" % i
                image = Factory.AsyncImage(source=src, allow_stretch=True)
                carousel.add_widget(image)
            return carousel

    Example1().run()

.. versionchanged:: 1.5.0

    The carousel now support active children, as
    :class:`~kivy.uix.scrollview.ScrollView`. It will detect a swipe gesture
    according to :data:`Carousel.scroll_timeout` and
    :data:`Carousel.scroll_distance`.
'''

__all__ = ('Carousel', )

from functools import partial
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.animation import Animation
from kivy.uix.stencilview import StencilView
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import BooleanProperty, OptionProperty, AliasProperty, \
                            NumericProperty, ListProperty, ObjectProperty


class Carousel(StencilView):
    '''Carousel class. See module documentation for more information.
    '''

    slides = ListProperty([])
    '''List of slides inside the carousel. The slides are added when a widget is
    added to Carousel using add_widget().

    :data:`slides` is a list of :class:`~kivy.ui.relativelayout.RelativeLayout`
    widgets containing the content added through add_widget.
    '''

    direction = OptionProperty('right',
            options=('right', 'left', 'top', 'bottom'))
    '''Specifies the direction in which the slides are orderd / from
    which the user swipes to go from one to the next slide.
    Can be `right`, `left`, 'top', or `bottom`.  For example, with
    the default value of `right`, the second slide, is to the right
    of the first, and the user would swipe from the right towards the
    left, to get to the second slide.

    :data:`direction` is a :class:`~kivy.properties.OptionProperty`,
    default to 'right'.
    '''

    min_move = NumericProperty(0.2)
    '''Defines the minimal distance from the edge where the movement is
    considered a swipe gesture and the carousel will change his content.
    This is a percentage of the carousel width.
    If the movement doesn't reach this minimal value, then the movement is
    canceled and the content is restored to its preceding position.

    :data:`min_move` is a :class:`~kivy.properties.NumericProperty`, default
    to 0.2
    '''

    anim_move_duration = NumericProperty(0.5)
    '''Defines the duration of the carousel animation between pages.

    :data:`anim_move_duration` is a :class:`~kivy.properties.NumericProperty`,
    default to 0.5
    '''

    anim_cancel_duration = NumericProperty(0.3)
    '''Defines the duration of the animation when a swipe movement is not
    accepted. This is generally when the user doesnt swipe enough.
    See :data:`min_move`.

    :data:`anim_cancel_duration` is a :class:`~kivy.properties.NumericProperty`
    , default to 0.3
    '''

    loop = BooleanProperty(False)
    '''Allow carousel to swipe infinitely. When the user reach the last page,
    he will get the first page when trying to swipe next. Same effect when
    trying to swipe the first page.

    :data:`loop` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''

    def _get_index(self):
        if self.slides:
            return self._index % len(self.slides)
        return float('nan')

    def _set_index(self, value):
        if self.slides:
            self._index = value % len(self.slides)
        else:
            self._index = float('nan')
    index = AliasProperty(_get_index, _set_index, bind=('_index', 'slides'))
    '''Get/Set the current visible slide based on index.

    :data:`index` is a :class:`~kivy.properties.NumericProperty`, default
    to 0 (first item)
    '''

    def _prev_slide(self):
        if len(self.slides) < 2:  # None, or 1 slide
            return None
        if len(self.slides) == 2:
            if self.index == 0:
                return None
            if self.index == 1:
                return self.slides[0]
        if self.loop and self.index == 0:
            return self.slides[-1]
        if self.index > 0:
            return self.slides[self.index - 1]
    previous_slide = AliasProperty(_prev_slide, None, bind=('slides', 'index'))
    '''The previous slide in the Carousel, is None if the current slide is
    the first slide in the carousel.  If :data:`orientation` is 'horizontal',
    the previous slide is to the left. If :data:`orientation` is 'vertical',
    the previous slide towards the bottom.

    :data:`previous_slide` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def _curr_slide(self):
        if len(self.slides):
            return self.slides[self.index]
    current_slide = AliasProperty(_curr_slide, None, bind=('slides', 'index'))
    '''The currently shown slide.
    Slidesare a :class:`~kivy.uix.relativelayout.Relativelayout` which
    contains the widget added to the carousel.

    :data:`current_slide` is a :class:`~kivy.properties.AliasProperty`.
    '''

    def _next_slide(self):
        if len(self.slides) < 2:  # None, or 1 slide
            return None
        if len(self.slides) == 2:
            if self.index == 0:
                return self.slides[1]
            if self.index == 1:
                return None
        if self.loop and self.index == len(self.slides) - 1:
            return self.slides[0]
        if self.index < len(self.slides) - 1:
            return self.slides[self.index + 1]
    next_slide = AliasProperty(_next_slide, None, bind=('slides', 'index'))
    '''The next slide in the Carousel, is None if the current slide is
    the last slide in the carousel.  If :data:`orientation` is 'horizontal',
    the next slide is to the right. If :data:`orientation` is 'vertical',
    the previous slide is towards the top.

    :data:`previous_slide` is a :class:`~kivy.properties.AliasProperty`.
    '''

    scroll_timeout = NumericProperty(200)
    '''Timeout allowed to trigger the :data:`scroll_distance`, in milliseconds.
    If the user has not moved :data:`scroll_distance` within the timeout,
    the scrolling will be disabled, and the touch event will go to the children.

    :data:`scroll_timeout` is a :class:`~kivy.properties.NumericProperty`,
    default to 200 (milliseconds)

    .. versionadded:: 1.5.0
    '''

    scroll_distance = NumericProperty('20dp')
    '''Distance to move before scrolling the :class:`ScrollView`, in pixels. As
    soon as the distance has been traveled, the :class:`ScrollView` will start
    to scroll, and no touch event will go to children.
    It is advisable that you base this value on the dpi of your target device's
    screen.

    :data:`scroll_distance` is a :class:`~kivy.properties.NumericProperty`,
    default to 20dp.

    .. versionadded:: 1.5.0
    '''

    #### private properties, for internal use only ###
    _index = NumericProperty(0)
    _prev = ObjectProperty(None, allownone=True)
    _current = ObjectProperty(None, allownone=True)
    _next = ObjectProperty(None, allownone=True)
    _offset = NumericProperty(0)
    _touch = ObjectProperty(None, allownone=True)

    def _insert_visible_slides(self):
        self._prev = self.previous_slide
        self._current = self.current_slide
        self._next = self.next_slide
        for slide in self.slides:
            super(Carousel, self).remove_widget(slide)
        if self._prev:
            super(Carousel, self).add_widget(self._prev)
        if self._next:
            super(Carousel, self).add_widget(self._next)
        if self._current:
            super(Carousel, self).add_widget(self._current)

    def _position_visible_slides(self):
        if self.direction in ['right', 'left']:
            xoff = self.x + self._offset
            x_prev = {'left': xoff + self.width, 'right': xoff - self.width}
            x_next = {'left': xoff - self.width, 'right': xoff + self.width}
            if self._prev:
                self._prev.pos = (x_prev[self.direction], self.y)
            if self._current:
                self._current.pos = (xoff, self.y)
            if self._next:
                self._next.pos = (x_next[self.direction], self.y)
        if self.direction in ['top', 'bottom']:
            yoff = self.y + self._offset
            y_prev = {'top': yoff - self.height, 'bottom': yoff + self.height}
            y_next = {'top': yoff + self.height, 'bottom': yoff - self.height}
            if self._prev:
                self._prev.pos = (self.x, y_prev[self.direction])
            if self._current:
                self._current.pos = (self.x, yoff)
            if self._next:
                self._next.pos = (self.x, y_next[self.direction])

    def on_size(self, *args):
        for slide in self.slides:
            slide.size = self.size
        self._position_visible_slides()

    def on_index(self, *args):
        self._insert_visible_slides()
        self._position_visible_slides()
        self._offset = 0

    def on_slides(self, *args):
        self.index = self.index % len(self.slides)
        self._insert_visible_slides()
        self._position_visible_slides()

    def on__offset(self, *args):
        self._position_visible_slides()
        #if reached full offset, switche index to next or prev
        if self.direction == 'right':
            if self._offset <= -self.width:
                self.index = self.index + 1
            if self._offset >= self.width:
                self.index = self.index - 1
        if self.direction == 'left':
            if self._offset <= -self.width:
                self.index = self.index - 1
            if self._offset >= self.width:
                self.index = self.index + 1
        if self.direction == 'top':
            if self._offset <= -self.height:
                self.index = self.index + 1
            if self._offset >= self.height:
                self.index = self.index - 1
        if self.direction == 'bottom':
            if self._offset <= -self.height:
                self.index = self.index - 1
            if self._offset >= self.height:
                self.index = self.index + 1

    def _start_animation(self, *args):
        Animation.cancel_all(self)

        # compute target offset for ease back, next or prev
        new_offset = 0
        is_horizontal = self.direction in ['right', 'left']
        extent = self.width if is_horizontal else self.height
        if self._offset < self.min_move * -extent:
            new_offset = -extent
        elif self._offset > self.min_move * extent:
            new_offset = extent

        # if new_offset is 0, it wasnt enough to go next/prev
        dur = self.anim_move_duration
        if new_offset == 0:
            dur = self.anim_cancel_duration

        if not self.loop:  # detect edge cases if not looping
            is_first = (self.index == 0)
            is_last = (self.index == len(self.slides) - 1)
            if self.direction in ['right', 'top']:
                towards_prev = (new_offset > 0)
                towards_next = (new_offset < 0)
            if self.direction in ['left', 'bottom']:
                towards_prev = (new_offset < 0)
                towards_next = (new_offset > 0)
            if (is_first and towards_prev) or (is_last and towards_next):
                new_offset = 0

        anim = Animation(_offset=new_offset, d=dur, t='out_quad')
        anim.start(self)

    def _get_uid(self, prefix='sv'):
        return '{0}.{1}'.format(prefix, self.uid)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            touch.ud[self._get_uid('cavoid')] = True
            return
        if self._touch:
            return super(Carousel, self).on_touch_down(touch)
        Animation.cancel_all(self)
        self._touch = touch
        uid = self._get_uid()
        touch.grab(self)
        touch.ud[uid] = {
            'mode': 'unknown',
            'time': touch.time_start}
        Clock.schedule_once(self._change_touch_mode,
                self.scroll_timeout / 1000.)
        return True

    def on_touch_move(self, touch):
        if self._get_uid('cavoid') in touch.ud:
            return
        if self._touch is not touch:
            super(Carousel, self).on_touch_move(touch)
            return self._get_uid() in touch.ud
        if touch.grab_current is not self:
            return True
        ud = touch.ud[self._get_uid()]
        direction = self.direction
        if ud['mode'] == 'unknown':
            if direction in ('right', 'left'):
                distance = abs(touch.ox - touch.x)
            else:
                distance = abs(touch.oy - touch.y)
            if distance > self.scroll_distance:
                Clock.unschedule(self._change_touch_mode)
                ud['mode'] = 'scroll'
        else:
            if direction in ('right', 'left'):
                self._offset += touch.dx
            if direction in ('top', 'bottom'):
                self._offset += touch.dy
        return True

    def on_touch_up(self, touch):
        if self._get_uid('cavoid') in touch.ud:
            return
        if self in [x() for x in touch.grab_list]:
            touch.ungrab(self)
            self._touch = None
            ud = touch.ud[self._get_uid()]
            if ud['mode'] == 'unknown':
                Clock.unschedule(self._change_touch_mode)
                super(Carousel, self).on_touch_down(touch)
                Clock.schedule_once(partial(self._do_touch_up, touch), .1)
            else:
                self._start_animation()

        else:
            if self._touch is not touch and self.uid not in touch.ud:
                super(Carousel, self).on_touch_up(touch)
        return self._get_uid() in touch.ud

    def _do_touch_up(self, touch, *largs):
        super(Carousel, self).on_touch_up(touch)
        # don't forget about grab event!
        for x in touch.grab_list[:]:
            touch.grab_list.remove(x)
            x = x()
            if not x:
                continue
            touch.grab_current = x
            super(Carousel, self).on_touch_up(touch)
        touch.grab_current = None

    def _change_touch_mode(self, *largs):
        if not self._touch:
            return
        self._start_animation()
        uid = self._get_uid()
        touch = self._touch
        ud = touch.ud[uid]
        if ud['mode'] == 'unknown':
            touch.ungrab(self)
            self._touch = None
            touch.push()
            touch.apply_transform_2d(self.to_widget)
            touch.apply_transform_2d(self.to_parent)
            super(Carousel, self).on_touch_down(touch)
            touch.pop()
            return

    def add_widget(self, widget, index=0):
        slide = RelativeLayout(size=self.size, x=self.x - self.width, y=self.y)
        slide.add_widget(widget)
        super(Carousel, self).add_widget(slide, index)
        if index != 0:
            self.slides.insert(index, slide)
        else:
            self.slides.append(slide)

    def remove_widget(self, widget, *args, **kwargs):
        # XXX be careful, the widget.parent.parent refer to the RelativeLayout
        # added in add_widget(). But it will break if RelativeLayout
        # implementation change.
        if widget.parent.parent in self.slides:
            slide = widget.parent.parent
            self.slides.remove(slide)
            return slide.remove_widget(widget, *args, **kwargs)
        return super(Carousel, self).remove_widget(widget, *args, **kwargs)


if __name__ == '__main__':
    from kivy.app import App

    class Example1(App):

        def build(self):
            carousel = Carousel(direction='right')
            for i in range(10):
                src = "http://placehold.it/480x270.png&text=slide-%d&.png" % i
                image = Factory.AsyncImage(source=src, allow_stretch=True)
                carousel.add_widget(image)
            return carousel

    Example1().run()
