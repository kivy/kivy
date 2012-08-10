'''
Carousel
========

.. versionadded:: 1.4.0

The :class:`Carousel` widget provides the classic mobile-friendly carousel view
where you can swipe between slides.
You can add any content to the carousel and use it horizontally or verticaly.
The carousel can display pages in loop or not.

'''

__all__ = ('Carousel', )

from kivy.factory import Factory
from kivy.animation import Animation
from kivy.uix.stencilview import StencilView
from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import BooleanProperty, OptionProperty, AliasProperty, \
                            NumericProperty, ListProperty, ObjectProperty


class Carousel(StencilView):

    slides = ListProperty([])
    ''' List of slides inside the carousel.  The slides are added when a
    widget is added to Carousel using add_widget().

    :data: `slides` is a list of `~kivy.ui.relativelayout.RelativeLayout`
    widgets containing the content added through add_widget.
    '''

    orientation = OptionProperty('horizontal',
            options=('horizontal', 'vertical'))
    '''Specifies the orientation in which you can scroll the carousel
    Can be `horizontal` or `vertical`.

    :data:`orientation` is a :class:`~kivy.properties.OptionProperty`,
    default to 'horizontal'.
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
        return self._index%len(self.slides)

    def _set_index(self, value):
        self._index = value%len(self.slides)
    index = AliasProperty(_get_index, _set_index, bind=('_index', 'slides'))
    '''Get/Set the current visible slide based on index.

    :data:`index` is a :class:`~kivy.properties.NumericProperty`, default
    to 0 (first item)
    '''

    def _prev_slide(self):
        if len(self.slides) < 2: #None, or 1 slide
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
        if len(self.slides) < 2: #None, or 1 slide
            return None
        if len(self.slides) == 2:
            if self.index == 0:
                return self.slides[1]
            if self.index == 1:
                return None
        if self.loop and self.index == len(self.slides)-1:
            return self.slides[0]
        if self.index < len(self.slides)-1:
            return self.slides[self.index + 1]
    next_slide = AliasProperty(_next_slide, None, bind=('slides', 'index'))
    '''The next slide in the Carousel, is None if the current slide is
    the last slide in the carousel.  If :data:`orientation` is 'horizontal',
    the next slide is to the right. If :data:`orientation` is 'vertical',
    the previous slide is towards teh top.

    :data:`previous_slide` is a :class:`~kivy.properties.AliasProperty`.
    '''

    #### private properties, for internal use only ###
    _index = NumericProperty(0)
    _prev = ObjectProperty(None, allownone=True)
    _current = ObjectProperty(None, allownone=True)
    _next = ObjectProperty(None, allownone=True)
    _offset = NumericProperty(0)
    _drag_touches = ListProperty([])

    def _get_extent(self):
        if self.orientation == 'horizontal':
            return self.width
        if self.orientation == 'vertical':
            return self.height
    _extent = AliasProperty(_get_extent, None, bind=('orientation', 'size'))

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
        if self.orientation == 'horizontal':
            x_off = self.x + self._offset
            if self._prev:
                self._prev.x = x_off - self.width
            if self._current:
                self._current.x = x_off
            if self._next:
                self._next.x = x_off + self.width
        if self.orientation == 'vertical':
            y_off = self.y + self._offset
            if self._prev:
                self._prev.y = y_off - self.height
            if self._current:
                self._current.y = y_off
            if self._next:
                self._next.y = y_off + self.height

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
        if self._offset <= self._extent * -1:
            self.index = self.index+1
        if self._offset >= self._extent:
            self.index = self.index - 1

    def on__drag_touches(self, *args):
        #only when user lets go completly, start animation
        Animation.cancel_all(self)
        if len(self._drag_touches) == 0:
            new_offset = 0
            dur = self.anim_move_duration
            if self._offset < self.min_move * self._extent * -1:
                if self.loop or self.index < len(self.slides)-1:
                    new_offset = self._extent * -1
            elif self._offset > self.min_move * self._extent:
                if self.loop or self.index > 0:
                    new_offset = self._extent
            else:
                dur = self.anim_cancel_duration
            anim = Animation(_offset=new_offset, d=dur, t='out_quad')
            anim.start(self)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        if super(Carousel, self).on_touch_down(touch):
            return True
        else:
            self._drag_touches.append(touch.uid)
            touch.grab(self)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if self._drag_touches.index(touch.uid) > 0:
                return True
            if self.orientation == "horizontal":
                self._offset += touch.dx
            if self.orientation == "vertical":
                self._offset += touch.dy
            return True

        if self.collide_point(*touch.pos):
            return super(Carousel, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self._drag_touches.remove(touch.uid)
            touch.ungrab(self)
            return True

        if self.collide_point(*touch.pos):
            return super(Carousel, self).on_touch_move(touch)

    def add_widget(self, *args, **kwargs):
        slide = RelativeLayout(size=self.size, x=self.x-self.width, y=self.y)
        slide.add_widget(*args, **kwargs)
        super(Carousel, self).add_widget(slide)
        self.slides.append(slide)

    def remove_widget(self, widget, *l, **kwargs):
        if widget.parent.parent in self.slides:
            slide = widget.parent
            self.slides.remove(slide)
            return slide.remove_widget(widget, *l, **kwargs)
        return super(Carousel, self).remove_widget(widget, *l, **kwargs)


if __name__ == '__main__':
    from kivy.app import App

    class Example1(App):

        def build(self):
            carousel = Carousel()
            for i in range(10):
                carousel.add_widget(Factory.Label(text="slide %d"%i))
            return carousel

    Example1().run()
