"""
PageLayout
==========

The :class:`PageLayout` class is used to create a simple multi-page
layout, in a way that allows easy flipping from one page to another using
borders.

:class:`PageLayout` does not currently honor
:attr:`~kivy.uix.widget.Widget.size_hint` or
:attr:`~kivy.uix.widget.Widget.pos_hint` properties.

.. versionadded:: 1.8.0

example::

    PageLayout:
        Button:
            text: 'page1'

        Button:
            text: 'page2'

        Button:
            text: 'page3'
"""

__all__ = ('PageLayout', )

from kivy.uix.layout import Layout
from kivy.properties import NumericProperty
from kivy.animation import Animation


class PageLayout(Layout):
    '''PageLayout class. See module documentation for more information.
    '''

    page = NumericProperty(0)
    '''The currently displayed page.

    :data:`page` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0.
    '''

    border = NumericProperty('50dp')
    '''The width of the border used around the current page used to display
    the previous/next page when needed.

    :data:`border` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 0.
    '''

    swipe_threshold = NumericProperty(.5)
    '''The thresold used to trigger swipes as percentage of the widget
    size.

    :data:`swipe_threshold` is a :class:`~kivy.properties.NumericProperty`
    and defaults to .5.
    '''

    def __init__(self, **kwargs):
        super(PageLayout, self).__init__(**kwargs)

        self.bind(
            border=self._trigger_layout,
            page=self._trigger_layout,
            parent=self._trigger_layout,
            children=self._trigger_layout,
            size=self._trigger_layout,
            pos=self._trigger_layout)

    def do_layout(self, *largs):
        l_children = len(self.children)
        for i, c in enumerate(reversed(self.children)):
            if i < l_children:
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

            c.height = self.height
            c.width = width

            Animation(
                x=x,
                y=self.y,
                d=.5, t='in_quad').start(c)

    def on_touch_down(self, touch):
        if self.y < touch.y < self.top:
            if self.page > 0 and self.x < touch.x < (self.x + self.border):
                touch.ud['page'] = 'previous'
                touch.grab(self)
                return True

            elif (
                self.page < len(self.children) - 1 and
                self.right > touch.x > (self.right - self.border)
            ):
                touch.ud['page'] = 'next'
                touch.grab(self)
                return True

        return self.children[-self.page - 1].on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current == self:
            if touch.ud['page'] == 'previous':
                self.children[-self.page - 1].x = max(min(
                    self.x + self.border + (touch.x - touch.ox),
                    self.right - self.border),
                    self.x + self.border)

                if self.page > 1:
                    self.children[-self.page].x = min(
                        self.x + self.border * (touch.sx - touch.osx),
                        self.x + self.border)

                if self.page < len(self.children) - 1:
                    self.children[-self.page + 1].x = min(
                        self.right - self.border * (1 - (touch.sx - touch.osx)),
                        self.right)

            elif touch.ud['page'] == 'next':
                self.children[-self.page + 1].x = min(max(
                    self.right - self.border + (touch.x - touch.ox),
                    self.x + self.border),
                    self.right - self.border)

                if self.page >= 1:
                    self.children[-self.page - 1].x = max(
                        self.x + self.border * (1 - (touch.osx - touch.sx)),
                        self.x)

                if self.page < len(self.children) - 2:
                    self.children[-self.page].x = max(
                        self.right + self.border * (touch.sx - touch.osx),
                        self.right - self.border)

        return self.children[-self.page - 1].on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current == self:
            if (
                touch.ud['page'] == 'previous' and
                abs(touch.x - touch.ox) / self.width > self.swipe_threshold
            ):
                self.page -= 1
            elif (
                touch.ud['page'] == 'next' and
                abs(touch.x - touch.ox) / self.width > self.swipe_threshold
            ):
                self.page += 1
            else:
                self._trigger_layout()

            touch.ungrab(self)
        return self.children[-self.page + 1].on_touch_up(touch)


if __name__ == '__main__':
    from kivy.base import runTouchApp
    from kivy.uix.button import Button

    pl = PageLayout()
    for i in range(1, 4):
        b = Button(text='page%s' % i)
        pl.add_widget(b)

    runTouchApp(pl)
