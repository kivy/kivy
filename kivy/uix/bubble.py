'''
Bubble
======

.. versionadded:: 1.1.0

.. image:: images/bubble.jpg
    :align: right

The Bubble widget is a form of menu or a small popup where the menu options
are stacked either vertically or horizontally.

The :class:`Bubble` contains an arrow pointing in the direction you
choose.

Simple example
--------------

.. include:: ../../examples/widgets/bubble_test.py
    :literal:

Customize the Bubble
--------------------

You can choose the direction in which the arrow points::

    Bubble(arrow_pos='top_mid')

The widgets added to the Bubble are ordered horizontally by default, like a
Boxlayout. You can change that by::

    orientation = 'vertical'

To add items to the bubble::

    bubble = Bubble(orientation = 'vertical')
    bubble.add_widget(your_widget_instance)

To remove items::

    bubble.remove_widget(widget)
    or
    bubble.clear_widgets()

To access the list of children, use content.children::

    bubble.content.children

.. warning::
  This is important! Do not use bubble.children

To change the appearance of the bubble::

    bubble.background_color = (1, 0, 0, .5) #50% translucent red
    bubble.border = [0, 0, 0, 0]
    background_image = 'path/to/background/image'
    arrow_image = 'path/to/arrow/image'
'''

__all__ = ('Bubble', 'BubbleButton', 'BubbleContent')

from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import ObjectProperty, StringProperty, OptionProperty, \
    ListProperty, BooleanProperty
from kivy.clock import Clock
from kivy.base import EventLoop
from kivy.metrics import dp


class BubbleButton(Button):
    '''A button intended for use in a Bubble widget.
    You can use a "normal" button class, but it will not look good unless
    the background is changed.

    Rather use this BubbleButton widget that is already defined and provides a
    suitable background for you.
    '''
    pass


class BubbleContent(GridLayout):
    pass


class Bubble(GridLayout):
    '''Bubble class. See module documentation for more information.
    '''

    background_color = ListProperty([1, 1, 1, 1])
    '''Background color, in the format (r, g, b, a). To use it you have to set
    either :attr:`background_image` or :attr:`arrow_image` first.

    :attr:`background_color` is a :class:`~kivy.properties.ListProperty` and
    defaults to [1, 1, 1, 1].
    '''

    border = ListProperty([16, 16, 16, 16])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction. Used with the :attr:`background_image`.
    It should be used when using custom backgrounds.

    It must be a list of 4 values: (bottom, right, top, left). Read the
    BorderImage instructions for more information about how to use it.

    :attr:`border` is a :class:`~kivy.properties.ListProperty` and defaults to
    (16, 16, 16, 16)
    '''

    background_image = StringProperty(
        'atlas://data/images/defaulttheme/bubble')
    '''Background image of the bubble.

    :attr:`background_image` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/bubble'.
    '''

    arrow_image = StringProperty(
        'atlas://data/images/defaulttheme/bubble_arrow')
    ''' Image of the arrow pointing to the bubble.

    :attr:`arrow_image` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/bubble_arrow'.
    '''

    show_arrow = BooleanProperty(True)
    ''' Indicates whether to show arrow.

    .. versionadded:: 1.8.0

    :attr:`show_arrow` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to `True`.
    '''

    arrow_pos = OptionProperty('bottom_mid', options=(
        'left_top', 'left_mid', 'left_bottom', 'top_left', 'top_mid',
        'top_right', 'right_top', 'right_mid', 'right_bottom',
        'bottom_left', 'bottom_mid', 'bottom_right'))
    '''Specifies the position of the arrow relative to the bubble.
    Can be one of: left_top, left_mid, left_bottom top_left, top_mid, top_right
    right_top, right_mid, right_bottom bottom_left, bottom_mid, bottom_right.

    :attr:`arrow_pos` is a :class:`~kivy.properties.OptionProperty` and
    defaults to 'bottom_mid'.
    '''

    content = ObjectProperty(None)
    '''This is the object where the main content of the bubble is held.

    :attr:`content` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to 'None'.
    '''

    orientation = OptionProperty('horizontal',
                                 options=('horizontal', 'vertical'))
    '''This specifies the manner in which the children inside bubble
    are arranged. Can be one of 'vertical' or 'horizontal'.

    :attr:`orientation` is a :class:`~kivy.properties.OptionProperty` and
    defaults to 'horizontal'.
    '''

    limit_to = ObjectProperty(None, allownone=True)
    '''Specifies the widget to which the bubbles position is restricted.

    .. versionadded:: 1.6.0

    :attr:`limit_to` is a :class:`~kivy.properties.ObjectProperty` and
    defaults to 'None'.
    '''

    border_auto_scale = OptionProperty(
        'both_lower',
        options=[
            'off', 'both', 'x_only', 'y_only', 'y_full_x_lower',
            'x_full_y_lower', 'both_lower'
        ]
    )
    '''Specifies the :attr:`kivy.graphics.BorderImage.auto_scale`
    value on the background BorderImage.

    .. versionadded:: 1.11.0

    :attr:`border_auto_scale` is a
    :class:`~kivy.properties.OptionProperty` and defaults to
    'both_lower'.
    '''

    def __init__(self, **kwargs):
        self._prev_arrow_pos = None
        self._arrow_layout = BoxLayout()
        self._bk_img = Image(
            source=self.background_image, allow_stretch=True,
            keep_ratio=False, color=self.background_color)
        self.background_texture = self._bk_img.texture
        self._arrow_img = Image(source=self.arrow_image,
                                allow_stretch=True,
                                color=self.background_color)
        self.content = content = BubbleContent(parent=self)
        super(Bubble, self).__init__(**kwargs)
        content.parent = None
        self.add_widget(content)
        self.on_arrow_pos()

    def add_widget(self, *l):
        content = self.content
        if content is None:
            return
        if l[0] == content or l[0] == self._arrow_img\
                or l[0] == self._arrow_layout:
            super(Bubble, self).add_widget(*l)
        else:
            content.add_widget(*l)

    def remove_widget(self, *l):
        content = self.content
        if not content:
            return
        if l[0] == content or l[0] == self._arrow_img\
                or l[0] == self._arrow_layout:
            super(Bubble, self).remove_widget(*l)
        else:
            content.remove_widget(l[0])

    def clear_widgets(self, **kwargs):
        content = self.content
        if not content:
            return
        if kwargs.get('do_super', False):
            super(Bubble, self).clear_widgets()
        else:
            content.clear_widgets()

    def on_show_arrow(self, instance, value):
        self._arrow_img.opacity = int(value)

    def on_parent(self, instance, value):
        Clock.schedule_once(self._update_arrow)

    def on_pos(self, instance, pos):
        lt = self.limit_to

        if lt:
            self.limit_to = None
            if lt is EventLoop.window:
                x = y = 0
                top = lt.height
                right = lt.width
            else:
                x, y = lt.x, lt.y
                top, right = lt.top, lt.right

            self.x = max(self.x, x)
            self.right = min(self.right, right)
            self.top = min(self.top, top)
            self.y = max(self.y, y)
            self.limit_to = lt

    def on_background_image(self, *l):
        self._bk_img.source = self.background_image

    def on_background_color(self, *l):
        if self.content is None:
            return
        self._arrow_img.color = self._bk_img.color = self.background_color

    def on_orientation(self, *l):
        content = self.content
        if not content:
            return
        if self.orientation[0] == 'v':
            content.cols = 1
            content.rows = 99
        else:
            content.cols = 99
            content.rows = 1

    def on_arrow_image(self, *l):
        self._arrow_img.source = self.arrow_image

    def on_arrow_pos(self, *l):
        self_content = self.content
        if not self_content:
            Clock.schedule_once(self.on_arrow_pos)
            return
        if self_content not in self.children:
            Clock.schedule_once(self.on_arrow_pos)
            return
        self_arrow_pos = self.arrow_pos
        if self._prev_arrow_pos == self_arrow_pos:
            return
        self._prev_arrow_pos = self_arrow_pos

        self_arrow_layout = self._arrow_layout
        self_arrow_layout.clear_widgets()
        self_arrow_img = self._arrow_img
        self._sctr = self._arrow_img
        self.clear_widgets(do_super=True)
        self_content.parent = None

        self_arrow_img.size_hint = (1, None)
        self_arrow_img.height = dp(self_arrow_img.texture_size[1])
        self_arrow_img.pos = 0, 0
        widget_list = []
        arrow_list = []
        parent = self_arrow_img.parent
        if parent:
            parent.remove_widget(self_arrow_img)

        if self_arrow_pos[0] == 'b' or self_arrow_pos[0] == 't':
            self.cols = 1
            self.rows = 3
            self_arrow_layout.orientation = 'horizontal'
            self_arrow_img.width = self.width / 3
            self_arrow_layout.size_hint = (1, None)
            self_arrow_layout.height = self_arrow_img.height
            if self_arrow_pos[0] == 'b':
                if self_arrow_pos == 'bottom_mid':
                    widget_list = (self_content, self_arrow_img)
                else:
                    if self_arrow_pos == 'bottom_left':
                        arrow_list = (self_arrow_img, Widget(), Widget())
                    elif self_arrow_pos == 'bottom_right':
                        # add two dummy widgets
                        arrow_list = (Widget(), Widget(), self_arrow_img)
                    widget_list = (self_content, self_arrow_layout)
            else:
                sctr = Scatter(do_translation=False,
                               rotation=180,
                               do_rotation=False,
                               do_scale=False,
                               size_hint=(None, None),
                               size=self_arrow_img.size)
                sctr.add_widget(self_arrow_img)
                if self_arrow_pos == 'top_mid':
                    # add two dummy widgets
                    arrow_list = (Widget(), sctr, Widget())
                elif self_arrow_pos == 'top_left':
                    arrow_list = (sctr, Widget(), Widget())
                elif self_arrow_pos == 'top_right':
                    arrow_list = (Widget(), Widget(), sctr)
                widget_list = (self_arrow_layout, self_content)
        elif self_arrow_pos[0] == 'l' or self_arrow_pos[0] == 'r':
            self.cols = 3
            self.rows = 1
            self_arrow_img.width = self.height / 3
            self_arrow_layout.orientation = 'vertical'
            self_arrow_layout.cols = 1
            self_arrow_layout.size_hint = (None, 1)
            self_arrow_layout.width = self_arrow_img.height

            rotation = -90 if self_arrow_pos[0] == 'l' else 90
            self._sctr = sctr = Scatter(do_translation=False,
                                        rotation=rotation,
                                        do_rotation=False,
                                        do_scale=False,
                                        size_hint=(None, None),
                                        size=(self_arrow_img.size))
            sctr.add_widget(self_arrow_img)

            if self_arrow_pos[-4:] == '_top':
                arrow_list = (Widget(size_hint=(1, .07)),
                              sctr, Widget(size_hint=(1, .3)))
            elif self_arrow_pos[-4:] == '_mid':
                arrow_list = (Widget(), sctr, Widget())
                Clock.schedule_once(self._update_arrow)
            elif self_arrow_pos[-7:] == '_bottom':
                arrow_list = (Widget(), Widget(), sctr)

            if self_arrow_pos[0] == 'l':
                widget_list = (self_arrow_layout, self_content)
            else:
                widget_list = (self_content, self_arrow_layout)

        # add widgets to arrow_layout
        add = self_arrow_layout.add_widget
        for widg in arrow_list:
            add(widg)

        # add widgets to self
        add = self.add_widget
        for widg in widget_list:
            add(widg)

    def _update_arrow(self, *dt):
        if self.arrow_pos in ('left_mid', 'right_mid'):
            self._sctr.center_y = self._arrow_layout.center_y
