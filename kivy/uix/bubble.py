'''
Bubble
======

.. versionadded:: 1.1.0

.. image:: images/bubble.jpg
    :align: right

The Bubble widget is a form of menu or a small popup where the options
are stacked either vertically or horizontally.

The :class:`Bubble` contains one arrow pointing towards the direction you
choose.

Simple example
--------------

.. include:: ../../examples/widgets/bubble_test.py
    :literal:

Customize the Bubble
-----------------------

You can choose the direction the arrow points towards::

    Bubble(arrow_pos='top_mid')

The widgets added to Bubble are orderd by default horizintally like in a
Boxlayout. You can change that by::

    orientation = 'vertical'

Add Items to the bubble::

    bubble = Bubble(orientation = 'vertical')
    bubble.add_widget(your_widget_instance)

Remove Items::

    bubble.remove_widget(Widget)
    or
    bubble.clear_widgets()

Access children list, **Warning** This is important! use content.children to
access the children list::

    bubble.content.children

Change Appearance of the bubble::

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
from kivy.uix.button import Button
from kivy.properties import ObjectProperty, StringProperty, OptionProperty, \
        ListProperty


class BubbleButton(Button):
    '''A button intented to be used as a widget for Bubble widget.
    You can use "normal" button class, but it will not look good, and you'll
    need to change yourself the background to be ok.

    Instead, you can use this BubbleButton widget that already defined the good
    background for you.
    '''
    pass


class BubbleContent(GridLayout):
    pass


class Bubble(GridLayout):
    '''Bubble class, see module documentation for more information.
    '''

    background_color = ListProperty([1, 1, 1, 1])
    '''Background color, in the format (r, g, b, a).

    :data:`background_color` is a :class:`~kivy.properties.ListProperty`,
    default to [1, 1, 1, 1].
    '''

    border = ListProperty([16, 16, 16, 16])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction, used itself for :data:`background_image`.
    Can be used when using custom background.

    It must be a list of 4 value: (top, right, bottom, left). Read the
    BorderImage instruction for more information about how to play with it.

    :data:`border` is a :class:`~kivy.properties.ListProperty`, default to (16,
    16, 16, 16)
    '''

    background_image = StringProperty('atlas://data/images/defaulttheme/bubble')
    '''Background image of the bubble

    :data:`background_image` is a :class:`~kivy.properties.StringProperty`,
    default to 'atlas://data/images/defaulttheme/bubble'.
    '''

    arrow_image = StringProperty(
        'atlas://data/images/defaulttheme/bubble_arrow')
    ''' Image of the arrow pointing to the bubble

    :data:`arrow_image` is a :class:`~kivy.properties.StringProperty`,
    default to 'atlas://data/images/defaulttheme/bubble_arrow'.
    '''

    arrow_pos = OptionProperty('bottom_mid',
            options=('left_top', 'left_mid', 'left_bottom', 'top_left',
                'top_mid', 'top_right', 'right_top', 'right_mid',
                'right_bottom', 'bottom_left', 'bottom_mid', 'bottom_right'))
    '''Specifies the position of the arrow relative to the bubble.
    Can be one of: left_top, left_mid, left_bottom top_left, top_mid, top_right
    right_top, right_mid, right_bottom bottom_left, bottom_mid, bottom_right.

    :data:`arrow_pos` is a :class:`~kivy.properties.OptionProperty`,
    default to 'bottom_mid'.
    '''

    background_texture = ObjectProperty(None)
    '''Specifies the background texture of the bubble

    :data:`background_texture` is a :class:`~kivy.properties.ObjectProperty`,
    default to 'None'.
    '''

    content = ObjectProperty(None)
    '''This is the object where the main content of the bubble is held

    :data:`content` is a :class:`~kivy.properties.ObjectProperty`,
    default to 'None'.
    '''

    orientation = OptionProperty('horizontal',
            options=('horizontal', 'vertical'))
    '''This specifies the manner in which the children inside bubble
    are arranged. can be one of 'vertical', 'horizontal'

    :data:`orientation` is a :class:`~kivy.properties.OptionProperty`,
    default to 'horizontal'.
    '''

    def __init__(self, **kwargs):
        self._arrow_layout = GridLayout(rows=1)
        self._bk_img = Image(
            source=self.background_image, allow_stretch=True,
            keep_ratio=False, color=self.background_color)
        self.background_texture = self._bk_img.texture
        self._arrow_img = Image(source=self.arrow_image,
            color=self.background_color)
        self.content = content = BubbleContent()
        super(Bubble, self).__init__(**kwargs)
        self.add_widget(content)
        self._bk_img.bind(on_texture=self._on_texture)
        self.on_arrow_pos()

    def _on_texture(self, *l):
        self.background_texture = self._bk_img.texture

    def add_widget(self, *l):
        content = self.content
        if content is None:
            return
        if l[0] == content or l[0] == self._arrow_img\
            or l[0] == self._arrow_layout:
            super(Bubble, self).add_widget(*l)
        else:
            content.add_widget(l[0])

    def remove_widget(self, *l):
        content = self.content
        if content is None:
            return
        if l[0] == content or l[0] == self._arrow_img\
            or l[0] == self._arrow_layout:
            super(Bubble, self).remove_widget(*l)
        else:
            content.remove_widget(l[0])

    def clear_widgets(self, **kwargs):
        content = self.content
        if content is None:
            return
        if kwargs.get('do_super', False):
            super(Bubble, self).clear_widgets()
        else:
            content.clear_widgets()

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
            return
        self_arrow_pos = self.arrow_pos
        self_arrow_layout = self._arrow_layout
        self_arrow_layout.clear_widgets()
        self_arrow_img = self._arrow_img
        self_arrow_img.pos = (0, 0)

        self.clear_widgets(do_super=True)
        self_arrow_img.size_hint = (1, None)
        self_arrow_img.height = self_arrow_img.texture_size[1]
        widget_list = []
        arrow_list = []
        if self_arrow_pos[0] == 'b' or self_arrow_pos[0] == 't':
            self.cols = 1
            self.rows = 2
            self_arrow_layout.rows = 1
            self_arrow_layout.cols = 3
            self_arrow_img.width = self.width/3
            self_arrow_layout.size_hint = (1, None)
            self_arrow_layout.height = self_arrow_img.height
            if self_arrow_pos[0] == 'b':
                if self_arrow_pos == 'bottom_mid':
                    widget_list = (self_content, self_arrow_img)
                else:
                    if self_arrow_pos == 'bottom_left':
                        arrow_list = (self_arrow_img, Widget(), Widget())
                    elif self_arrow_pos == 'bottom_right':
                        #add two dummy widgets
                        arrow_list = (Widget(), Widget(), self_arrow_img)
                    widget_list = (self_content, self_arrow_layout)
            else:
                sctr = Scatter(do_translation = False,
                               rotation = 180,
                               do_rotation = False,
                               do_scale = False,
                               size_hint = (None, None),
                               size = self_arrow_img.size)
                sctr.add_widget(self_arrow_img)
                if self_arrow_pos == 'top_mid':
                    #add two dummy widgets
                    arrow_list = (Widget(), sctr, Widget())
                elif self_arrow_pos == 'top_left':
                    arrow_list = (sctr, Widget(), Widget())
                elif self_arrow_pos == 'top_right':
                    arrow_list = (Widget(), Widget(), sctr)
                widget_list = (self_arrow_layout, self_content)
        elif self_arrow_pos[0] == 'l' or self_arrow_pos[0] == 'r':
            self.cols = 2
            self.rows = 1
            self_arrow_img.width = self.height/3
            self_arrow_layout.rows = 3
            self_arrow_layout.cols = 1
            self_arrow_layout.size_hint = (None, 1)
            self_arrow_layout.width = self_arrow_img.height

            rotation = -90 if self_arrow_pos[0] == 'l' else 90
            sctr = Scatter(do_translation = False,
                               rotation = rotation,
                               do_rotation = False,
                               do_scale = False,
                               size_hint = (None, None),
                               size = self_arrow_img.size)
            sctr.add_widget(self_arrow_img)

            lenarrow_pos = len(self_arrow_pos)
            if self_arrow_pos[lenarrow_pos-4:] == '_top':
                arrow_list = (Widget(size_hint = (1, .07)),
                              sctr, Widget(size_hint = (1, .3)))
            elif self_arrow_pos[lenarrow_pos-4:] == '_mid':
                arrow_list = (Widget(), sctr, Widget())
            elif self_arrow_pos[lenarrow_pos-7:] == '_bottom':
                arrow_list = (Widget(), Widget(), sctr)

            if self_arrow_pos[0] =='l':
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

