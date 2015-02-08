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

Example::

    PageLayout:
        Button:
            text: 'page1'
        Button:
            text: 'page2'
        Button:
            text: 'page3'

Transitions from one page to the next are made by swiping in from the border
areas on the right or left hand side. If you wish to display multiple widgets
in a page, we suggest you use a containing layout. Ideally, each page should
consist of a single :mod:`~kivy.uix.layout` widget that contains the remaining
widgets on that page.
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
    '''The width of the border around the current page used to display
    the previous/next page swipe areas when needed.

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
        l_children = len(self.children) - 1
        h = self.height
        x_parent, y_parent = self.pos
        p = self.page
        border = self.border
        right = self.right
        for i, c in enumerate(reversed(self.children)):
            if not i or i == l_children:
                width = self.width - border
            else:
                width = self.width - 2 * border

            if i < p:
                x = x_parent
            elif i == p:
                if not p:
                    x = x_parent
                else:
                    x = x_parent + border
            elif i == p + 1:
                x = right - border
            else:
                x = right

            c.height = h
            c.width = width

            Animation(
                x=x,
                y=y_parent,
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
                # move next page upto right edge
                if self.page < len(self.children) - 1:
                    self.children[-self.page - 2].x = min(
                        self.right - self.border * (1 - (touch.sx - touch.osx)),
                        self.right)

                # move current page until edge hits the right border
                if self.page >= 1:
                    self.children[-self.page - 1].x = max(min(
                        self.x + self.border + (touch.x - touch.ox),
                        self.right - self.border),
                        self.x + self.border)

                # move previous page left edge upto left border
                if self.page > 1:
                    self.children[-self.page].x = min(
                        self.x + self.border * (touch.sx - touch.osx),
                        self.x + self.border)

            elif touch.ud['page'] == 'next':
                # move current page upto left edge
                if self.page >= 1:
                    self.children[-self.page - 1].x = max(
                        self.x + self.border * (1 - (touch.osx - touch.sx)),
                        self.x)

                # move next page until its edge hit the left border
                if self.page < len(self.children) - 1:
                    self.children[-self.page - 2].x = min(max(
                        self.right - self.border + (touch.x - touch.ox),
                        self.x + self.border),
                        self.right - self.border)

                # move second next page upto right border
                if self.page < len(self.children) - 2:
                    self.children[-self.page - 3].x = max(
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
