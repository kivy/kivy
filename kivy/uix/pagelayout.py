"""
PageLayout
==========

The :class:`PageLayout` class allow to create a simple multiple page
layout, in a way that allows easy flipping of one page to another using
borders.

:class:`PageLayout` doesn't honor size_hint or pos_hint in any way currently.

.. versionadded:: 1.7.1

example::

    PageLayout:
        BoxLayout:
            canvas:
                Color:
                    rgba: 216/255., 195/255., 88/255., 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            orientation: 'vertical'
            Label:
                size_hint_y: None
                height: 1.5 * self.texture_size[1]
                text: 'page 1'

            Button:
                text: 'test'
                on_press: print "test"

        BoxLayout:
            orientation: 'vertical'
            canvas:
                Color:
                    rgba: 109/255., 8/255., 57/255., 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            Label:
                text: 'page 2'

            AsyncImage:
                source: 'http://kivy.org/logos/kivy-logo-black-64.png'

        GridLayout:
            canvas:
                Color:
                    rgba: 37/255., 39/255., 30/255., 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            cols: 2
            Label:
                text: 'page 3'
            AsyncImage:
                source: 'http://kivy.org/slides/kivyandroid-thumb.jpg'
            Button:
                text: 'test'
                on_press: print "test last page"
            AsyncImage:
                source: 'http://kivy.org/slides/kivypictures-thumb.jpg'
            Widget
            AsyncImage:
                source: 'http://kivy.org/slides/particlepanda-thumb.jpg'
"""

__all__ = ('PageLayout', )

from kivy.uix.layout import Layout
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.animation import Animation


class PageLayout(Layout):
    ''' PageLayout class. See module documentation for more information
    '''

    '''currently displayed page.

    :data:`page` is a :class:`~kivy.properties.NumericProperty`, default to 0.
    '''
    page = NumericProperty(0)

    '''width of the border used around current page to display previous/next
    page when needed.

    :data:`border` is a :class:`~kivy.properties.NumericProperty`, default to 0.
    '''
    border = NumericProperty(dp(50))

    def __init__(self, **kwargs):
        super(PageLayout, self).__init__(**kwargs)

        self.bind(
            border=self._trigger_layout,
            page=self._trigger_layout,
            parent=self._trigger_layout,
            children=self._trigger_layout,
            size=self._trigger_layout,
            pos=self._trigger_layout
            )

    def do_layout(self, *largs):
        for i, c in enumerate(reversed(self.children)):
            y = self.y
            height = self.height
            if i in (0, len(self.children) -1):
                width = self.width - self.border
            else:
                width = self.width - 2 * self.border

            if i == 0:
                x = self.x

            elif i < self.page:
                x = self.x

            elif i == self.page:
                x = self.x + self.border

            elif i == self.page + 1:
                x = self.right - self.border

            else:
                x = self.right

            c.height = height
            c.width = width

            Animation(
                x=x,
                y=y,
                d=.5, t='in_quad').start(c)

    def on_touch_down(self, touch):
        if self.y < touch.y < self.top:
            if self.page > 0 and self.x < touch.x < (self.x + self.border):
                touch.ud['page'] = 'previous'
                touch.grab(self)
                return True

            elif self.page < len(self.children) - 1 and self.right > touch.x > (self.right - self.border):
                touch.ud['page'] = 'next'
                touch.grab(self)
                return True

        return self.children[-self.page - 1].on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current == self:
            if touch.ud['page'] == 'previous':
                self.children[-self.page - 1].x = max(
                        min(
                            self.x + self.border + (touch.x - touch.ox),
                            self.right - self.border
                            ),
                        self.x + self.border
                        )


                if self.page > 1:
                    self.children[-self.page].x = min(
                            self.x + self.border * (touch.sx - touch.osx),
                            self.x + self.border
                            )

                if self.page < len(self.children) - 1:
                    self.children[-self.page + 1].x = min(
                            self.right - self.border * (1 - (touch.sx - touch.osx)),
                            self.right
                            )

            elif touch.ud['page'] == 'next':
                self.children[-self.page + 1].x = min(
                        max(
                            self.right - self.border + (touch.x - touch.ox),
                            self.x + self.border
                            ),
                        self.right - self.border
                        )

                if self.page >= 1:
                    self.children[-self.page - 1].x = max(
                            self.x + self.border * (1 - (touch.osx - touch.sx)),
                            self.x
                            )

                if self.page < len(self.children) - 2:
                    self.children[-self.page].x = max(
                            self.right + self.border * (touch.sx - touch.osx),
                            self.right - self.border
                            )

        return self.children[-self.page - 1].on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            if touch.ud['page'] == 'previous' and abs(touch.sx - touch.osx) > .5:
                self.page -= 1
            elif touch.ud['page'] == 'next' and abs(touch.sx - touch.osx) > .5:
                self.page += 1
            else:
                # hack to trigger a relayout
                self.page += 1
                self.page -= 1

            touch.ungrab(self)
        return self.children[-self.page + 1].on_touch_up(touch)
