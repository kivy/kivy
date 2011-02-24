'''
Float Layout
============

The :class:`FloatLayout` class will just honor the :data:`Widget.pos_hint` and
:data:`Widget.size_hint` attributes.

For example, if you create a :class:`FloatLayout` with size of (300, 300)::

    layout = FloatLayout(size=(300, 300))

    # by default, all widgets have size_hint=(1, 1)
    # So this button will have the same size as layout
    button = Button(text='Hello world')
    layout.add_widget(button)

    # if you want to create a button to be the 50% of the layout width, and 25%
    # of the layout height, and set position to 20, 20, you can do
    button = Button(text='Hello world', size_hint=(.5, .25), pos=(20, 20))

    # If you want to create a button that will always be the size of layout -
    # 20% each sides
    button = Button(text='Hello world', size_hint=(.6, .6),
                    pos_hint={'x':.2, 'y':.2})

.. note::

    This layout can be used to start an application. Most of time, you need to
    want which size is your Window.

.. warning::

    If you are not using pos_hint, you must handle yourself the position of your
    childs. Mean if the float layout is moving, your must handle the moving
    childs too.

'''

__all__ = ('FloatLayout', )

from kivy.clock import Clock
from kivy.uix.layout import Layout


class FloatLayout(Layout):
    '''Float layout class. See module documentation for more informations.
    '''

    def __init__(self, **kwargs):
        kwargs.setdefault('size', (1, 1))
        self._minimum_size = (0, 0)
        super(FloatLayout, self).__init__(**kwargs)
        self.bind(
            children = self._trigger_layout,
            pos = self._trigger_layout,
            size = self._trigger_layout)

    def _trigger_layout(self, *largs):
        Clock.unschedule(self._do_layout)
        Clock.schedule_once(self._do_layout)

    def update_minimum_size(self, *largs):
        '''Calculates the minimum size of the layout.
        '''
        width = height = 0

        for w in self.children:
            shw, shh = w.size_hint
            if isinstance(w, Layout):
                _w, _h = w.minimum_size
                if shw is None:
                    width = max(_w, width)
                if shh is not None:
                    height = max(_h, height)
            else:
                if shw is None:
                    width = max(w.width, width)
                if shh is None:
                    height = max(w.height, height)

        self.minimum_size = (width, height)

    def _do_layout(self, *largs):
        # optimize layout by preventing looking at the same attribute in a loop
        w, h = self.size
        x, y = self.pos
        for c in self.children:
            # size
            shw, shh = c.size_hint
            if shw and shh:
                c.size = w * shw, h * shh
            elif shw:
                c.width = w * shw
            elif shh:
                c.height = h * shh

            # pos
            for key, value in c.pos_hint.iteritems():
                if key == 'x':
                    c.x = x + value * w
                elif key == 'right':
                    c.right = x + value * w
                elif key == 'y':
                    c.y = y + value * h
                elif key == 'top':
                    c.top = y + value * h
                elif key == 'center_x':
                    c.center_x = x + value * w
                elif key == 'center_y':
                    c.center_y = y + value * h


