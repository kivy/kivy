"""
PageLayout
==========

.. image:: images/pagelayout.gif
    :align: right

The :class:`PageLayout` class is used to create a simple multi-page
layout, in a way that allows easy flipping from one page to another using
borders.

:class:`PageLayout` does not currently honor the
:attr:`~kivy.uix.widget.Widget.size_hint`,
:attr:`~kivy.uix.widget.Widget.size_hint_min`,
:attr:`~kivy.uix.widget.Widget.size_hint_max`, or
:attr:`~kivy.uix.widget.Widget.pos_hint` properties.

.. versionadded:: 1.8.0

Example:

.. code-block:: kv

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
from kivy.properties import NumericProperty, DictProperty
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
    defaults to 50dp.
    '''

    swipe_threshold = NumericProperty(.5)
    '''The threshold used to trigger swipes as ratio of the widget
    size.

    :data:`swipe_threshold` is a :class:`~kivy.properties.NumericProperty`
    and defaults to .5.
    '''

    anim_kwargs = DictProperty({'d': .5, 't': 'in_quad'})
    '''The animation kwargs used to construct the animation

    :data:`anim_kwargs` is a :class:`~kivy.properties.DictProperty`
    and defaults to {'d': .5, 't': 'in_quad'}.

    .. versionadded:: 1.11.0
    '''

    def __init__(self, **kwargs):
        super(PageLayout, self).__init__(**kwargs)

        trigger = self._trigger_layout
        fbind = self.fbind
        fbind('border', trigger)
        fbind('page', trigger)
        fbind('parent', trigger)
        fbind('children', trigger)
        fbind('size', trigger)
        fbind('pos', trigger)

    def do_layout(self, *largs):
        l_children = len(self.children) - 1
        h = self.height
        x_parent, y_parent = self.pos
        p = self.page
        border = self.border
        half_border = border / 2.
        right = self.right
        width = self.width - border
        for i, c in enumerate(reversed(self.children)):

            if i < p:
                x = x_parent
            elif i == p:
                if not p:  # it's first page
                    x = x_parent
                elif p != l_children:  # not first, but there are post pages
                    x = x_parent + half_border
                else:  # not first and there are no post pages
                    x = x_parent + border
            elif i == p + 1:
                if not p:  # second page - no left margin
                    x = right - border
                else:  # there's already a left margin
                    x = right - half_border
            else:
                x = right

            c.height = h
            c.width = width

            Animation(
                x=x,
                y=y_parent,
                **self.anim_kwargs).start(c)

    def on_touch_down(self, touch):
        if (
            self.disabled or
            not self.collide_point(*touch.pos) or
            not self.children
        ):
            return

        page = self.children[-self.page - 1]
        if self.x <= touch.x < page.x:
            touch.ud['page'] = 'previous'
            touch.grab(self)
            return True
        elif page.right <= touch.x < self.right:
            touch.ud['page'] = 'next'
            touch.grab(self)
            return True
        return page.on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current != self:
            return

        p = self.page
        border = self.border
        half_border = border / 2.
        page = self.children[-p - 1]
        if touch.ud['page'] == 'previous':
            # move next page up to right edge
            if p < len(self.children) - 1:
                self.children[-p - 2].x = min(
                    self.right - self.border * (1 - (touch.sx - touch.osx)),
                    self.right)

            # move current page until edge hits the right border
            if p >= 1:
                b_right = half_border if p > 1 else border
                b_left = half_border if p < len(self.children) - 1 else border
                self.children[-p - 1].x = max(min(
                    self.x + b_left + (touch.x - touch.ox),
                    self.right - b_right),
                    self.x + b_left)

            # move previous page left edge up to left border
            if p > 1:
                self.children[-p].x = min(
                    self.x + half_border * (touch.sx - touch.osx),
                    self.x + half_border)

        elif touch.ud['page'] == 'next':
            # move current page up to left edge
            if p >= 1:
                self.children[-p - 1].x = max(
                    self.x + half_border * (1 - (touch.osx - touch.sx)),
                    self.x)

            # move next page until its edge hit the left border
            if p < len(self.children) - 1:
                b_right = half_border if p >= 1 else border
                b_left = half_border if p < len(self.children) - 2 else border
                self.children[-p - 2].x = min(max(
                    self.right - b_right + (touch.x - touch.ox),
                    self.x + b_left),
                    self.right - b_right)

            # move second next page up to right border
            if p < len(self.children) - 2:
                self.children[-p - 3].x = max(
                    self.right + half_border * (touch.sx - touch.osx),
                    self.right - half_border)

        return page.on_touch_move(touch)

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

        if len(self.children) > 1:
            return self.children[-self.page + 1].on_touch_up(touch)


if __name__ == '__main__':
    from kivy.base import runTouchApp
    from kivy.uix.button import Button

    pl = PageLayout()
    for i in range(1, 4):
        b = Button(text='page%s' % i)
        pl.add_widget(b)

    runTouchApp(pl)
