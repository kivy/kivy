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
from kivy.properties import BooleanProperty, OptionProperty, \
                            NumericProperty, ListProperty


class Carousel(StencilView):

    slides = ListProperty([])
    ''' List of slides inside the carousel.  The slides are added when a
    widget is added to Carousel using add_widget().

    :data: `slides` is a list of `~kivy.ui.relativelayout.RelativeLayout`
    widgets containing the content added through add_widget.
    '''

    index = NumericProperty(0)
    '''Get/Set the current visible slide based on index.

    :data:`index` is a :class:`~kivy.properties.NumericProperty`, default
    to 0 (first item)
    '''

    orientation = OptionProperty('horizontal', options=('horizontal', 'vertical'))
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

    :data:`anim_move_duration` is a :class:`~kivy.properties.NumericProperty`, default
    to 0.5
    '''

    anim_cancel_duration = NumericProperty(0.3)
    '''Defines the duration of the animation when a swipe movement is not accepted.
    This is generally when the user doesnt swipe enough. See :data:`min_move`.

    :data:`anim_cancel_duration` is a :class:`~kivy.properties.NumericProperty`, default
    to 0.3
    '''

    loop = BooleanProperty(False)
    '''Allow carousel to swipe infinitely. When the user reach the last page, he will
    get the first page when trying to swipe next. Same effect when trying to swipe the
    first page

    :data:`loop` is a :class:`~kivy.properties.BooleanProperty`,
    default to True.
    '''


    # private, for internal use only
    _offset = NumericProperty(0)

    def __init__(self, *args, **kwargs):
        self._prev = None
        self._current = None
        self._next = None
        super(Carousel, self).__init__(*args, **kwargs)

    def _insert_visible_slides(self):
        self._prev = self.previous_slide
        self._current = self.current_slide
        self._next = self.next_slide
        print self.index, self._prev, self._current, self._next
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
            if self._prev:    self._prev.x    = x_off - self.width
            if self._current: self._current.x = x_off
            if self._next:    self._next.x    = x_off + self.width
        if self.orientation == 'vertical':
            y_off = self.y + self._offset
            if self._prev:    self._prev.y    = y_off - self.height
            if self._current: self._current.y = y_off
            if self._next:    self._next.y    = y_off + self.height

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

    def on_size(self, *args):
        for slide in self.slides:
            slide.size = self.size
        self._position_visible_slides()

    def on_index(self, *args):
        self.index = self.index % len(self.slides)
        self._insert_visible_slides()
        self._position_visible_slides()
        self._offset = 0

    def on_slides(self, *args):
        self.index = self.index % len(self.slides)
        self._insert_visible_slides()
        self._position_visible_slides()

    def on__offset(self, *args):
        self._position_visible_slides()
        #reached full offset, which switches index
        if self._offset <= self.extent * -1:
            self.index = self.index+1
        if self._offset >= self.extent:
            self.index = self.index - 1

    @property
    def extent(self):
        if self.orientation == 'horizontal':
            return self.width
        if self.orientation == 'vertical':
            return self.height

    @property
    def previous_slide(self):
        if len(self.slides) < 2: #None, or 1 slide
            return None
        if len(self.slides) == 2:
            if self.index == 0: return None
            if self.index == 1: return self.slides[0]
        if self.loop and self.index == 0:
            return self.slides[-1]
        if self.index > 0:
            return self.slides[self.index - 1]

    @property
    def current_slide(self):
        if len(self.slides):
            return self.slides[self.index]

    @property
    def next_slide(self):
        if len(self.slides) < 2: #None, or 1 slide
            return None
        if len(self.slides) == 2:
            if self.index == 0: return self.slides[1]
            if self.index == 1: return None
        if self.loop and self.index == len(self.slides)-1:
            return self.slides[0]
        if self.index < len(self.slides)-1:
            return self.slides[self.index + 1]

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        if super(Carousel, self).on_touch_down(touch):
            return True
        else:
            touch.grab(self)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if self.orientation == "horizontal":
                self._offset += touch.dx
            if self.orientation == "vertical":
                self._offset += touch.dy
            return True

        if self.collide_point(*touch.pos):
            return super(Carousel, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            self._end_drag()
            touch.ungrab(self)
            return True

        if self.collide_point(*touch.pos):
            return super(Carousel, self).on_touch_move(touch)

    def _end_drag(self):
        new_offset = 0
        dur = self.anim_move_duration
        if self._offset < self.min_move * self.extent * -1:
            if self.loop or self.index < len(self.slides)-1:
               new_offset = self.extent * -1
        elif self._offset > self.min_move * self.extent:
            if self.loop or self.index > 0:
               new_offset = self.extent
        else:
            dur = self.anim_cancel_duration 
        anim = Animation(_offset=new_offset, d=dur,t='out_quad')
        anim.start(self)


Factory.register('Carousel', Carousel)



if __name__ == '__main__':
    from kivy.app import App

    class Example1(App):
        """ images are not aligned vertically """
        def build(self):
            carousel = Carousel()
            for i in range(2):
                carousel.add_widget(Factory.Label(text="slide %d"%i))
            return carousel

    Example1().run()
