'''
Bubble
======

.. versionadded:: 1.1.0

.. image:: images/bubble.jpg
    :align: right

The :class:`Bubble` widget is a form of menu or a small popup with an arrow
arranged on one side of it's content.

The :class:`Bubble` contains an arrow attached to the content
(e.g., :class:`BubbleContent`) pointing in the direction you choose. It can
be placed either at a predefined location or flexibly by specifying a relative
position on the border of the widget.

The :class:`BubbleContent` is a styled BoxLayout and is thought to be added to
the :class:`Bubble` as a child widget. The :class:`Bubble` will then arrange
an arrow around the content as desired. Instead of the class:`BubbleContent`,
you can theoretically use any other :class:`Widget` as well as long as it
supports the 'bind' and 'unbind' function of the :class:`EventDispatcher` and
is compatible with Kivy to be placed inside a :class:`BoxLayout`.

The :class:`BubbleButton`is a styled Button. It suits to the style of
:class:`Bubble` and :class:`BubbleContent`. Feel free to place other Widgets
inside the 'content' of the :class:`Bubble`.


.. versionchanged:: 2.2.0
The properties :attr:`background_image`, :attr:`background_color`,
:attr:`border` and :attr:`border_auto_scale` were removed from :class:`Bubble`.
These properties had only been used by the content widget that now uses it's
own properties instead. The color of the arrow is now changed with
:attr:`arrow_color` instead of :attr:`background_color`.
These changes makes the :class:`Bubble` transparent to use with other layouts
as content without any side-effects due to property inheritance.

The property :attr:`flex_arrow_pos` has been added to allow further
customization of the arrow positioning.

The properties :attr:`arrow_margin`, :attr:`arrow_margin_x`,
:attr:`arrow_margin_y`, :attr:`content_size`, :attr:`content_width` and
:attr:`content_height` have been added to ease proper sizing of a
:class:`Bubble` e.g., based on it's content size.

BubbleContent
=============

The :class:`BubbleContent` is a styled BoxLayout that can be used to
add e.g., :class:`BubbleButtons` as menu items.

.. versionchanged:: 2.2.0
The properties :attr:`background_image`, :attr:`background_color`,
:attr:`border` and :attr:`border_auto_scale` were added to the
:class:`BubbleContent`. The :class:`BubbleContent` does no longer rely on these
properties being present in the parent class.

BubbleButton
============

The :class:`BubbleButton` is a styled :class:`Button` that can be used to be
added to the :class:`BubbleContent`.

Simple example
--------------

.. include:: ../../examples/widgets/bubble_test.py
    :literal:

Customize the Bubble
--------------------

You can choose the direction in which the arrow points::

    Bubble(arrow_pos='top_mid')
    or
    Bubble(size=(200, 40), flex_arrow_pos=(175, 40))

    Similarly, the corresponding properties in the '.kv' language can be used
    as well.

You can change the appearance of the bubble::

    Bubble(
        arrow_image='/path/to/arrow/image',
        arrow_color=(1, 0, 0, .5)),
    )
    BubbleContent(
        background_image='/path/to/background/image',
        background_color=(1, 0, 0, .5),  # 50% translucent red
        border=(0,0,0,0),
    )

    Similarly, the corresponding properties in the '.kv' language can be used
    as well.

-----------------------------
'''

__all__ = ('Bubble', 'BubbleButton', 'BubbleContent')

from kivy.uix.image import Image
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.properties import OptionProperty
from kivy.properties import ListProperty
from kivy.properties import BooleanProperty
from kivy.properties import ColorProperty
from kivy.properties import NumericProperty
from kivy.properties import ReferenceListProperty
from kivy.base import EventLoop
from kivy.metrics import dp


class BubbleException(Exception):
    pass


class BubbleButton(Button):
    '''A button intended for use in a BubbleContent widget.
    You can use a "normal" button class, but it will not look good unless the
    background is changed.

    Rather use this BubbleButton widget that is already defined and provides a
    suitable background for you.
    '''
    pass


class BubbleContent(BoxLayout):
    '''A styled BoxLayout that can be used as the content widget of a Bubble.

    .. versionchanged:: 2.2.0
    The graphical appearance of :class:`BubbleContent` is now based on it's
    own properties :attr:`background_image`, :attr:`background_color`,
    :attr:`border` and :attr:`border_auto_scale`. The parent widget properties
    are no longer considered. This makes the BubbleContent a standalone themed
    BoxLayout.
    '''

    background_color = ColorProperty([1, 1, 1, 1])
    '''Background color, in the format (r, g, b, a). To use it you have to set
    :attr:`background_image` first.

    .. versionadded:: 2.2.0

    :attr:`background_color` is a :class:`~kivy.properties.ColorProperty` and
    defaults to [1, 1, 1, 1].
    '''

    background_image = StringProperty('atlas://data/images/defaulttheme/bubble')
    '''Background image of the bubble.

    .. versionadded:: 2.2.0

    :attr:`background_image` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/bubble'.
    '''

    border = ListProperty([16, 16, 16, 16])
    '''Border used for :class:`~kivy.graphics.vertex_instructions.BorderImage`
    graphics instruction. Used with the :attr:`background_image`.
    It should be used when using custom backgrounds.

    It must be a list of 4 values: (bottom, right, top, left). Read the
    BorderImage instructions for more information about how to use it.

    .. versionadded:: 2.2.0

    :attr:`border` is a :class:`~kivy.properties.ListProperty` and defaults to
    (16, 16, 16, 16)
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

    .. versionadded:: 2.2.0

    :attr:`border_auto_scale` is a
    :class:`~kivy.properties.OptionProperty` and defaults to
    'both_lower'.
    '''


class Bubble(BoxLayout):
    '''Bubble class. See module documentation for more information.
    '''

    content = ObjectProperty(allownone=True)
    '''This is the object where the main content of the bubble is held.

    The content of the Bubble set by 'add_widget' and removed with
    'remove_widget' similarly to the :class:`ActionView` which is placed into
    a class:`ActionBar`

    :attr:`content` is a :class:`~kivy.properties.ObjectProperty` and defaults
    to None.
    '''

    arrow_image = StringProperty(
        'atlas://data/images/defaulttheme/bubble_arrow'
    )
    ''' Image of the arrow pointing to the bubble.

    :attr:`arrow_image` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/bubble_arrow'.
    '''

    arrow_color = ColorProperty([1, 1, 1, 1])
    '''Arrow color, in the format (r, g, b, a). To use it you have to set
    :attr:`arrow_image` first.

    .. versionadded:: 2.2.0

    :attr:`arrow_color` is a :class:`~kivy.properties.ColorProperty` and
    defaults to [1, 1, 1, 1].
    '''

    show_arrow = BooleanProperty(True)
    ''' Indicates whether to show arrow.

    .. versionadded:: 1.8.0

    :attr:`show_arrow` is a :class:`~kivy.properties.BooleanProperty` and
    defaults to `True`.
    '''

    arrow_pos = OptionProperty(
        'bottom_mid',
        options=(
            'left_top', 'left_mid', 'left_bottom',
            'top_left', 'top_mid', 'top_right',
            'right_top', 'right_mid', 'right_bottom',
            'bottom_left', 'bottom_mid', 'bottom_right',
        )
    )
    '''Specifies the position of the arrow as predefined relative position to
    the bubble.
    Can be one of: left_top, left_mid, left_bottom top_left, top_mid, top_right
    right_top, right_mid, right_bottom bottom_left, bottom_mid, bottom_right.

    :attr:`arrow_pos` is a :class:`~kivy.properties.OptionProperty` and
    defaults to 'bottom_mid'.
    '''

    flex_arrow_pos = ListProperty(None)
    '''Specifies the position of the arrow as flex coordinate around the
    border of the :class:`Bubble` Widget.
    If this property is set to a proper position (relative pixel coordinates
    within the :class:`Bubble` widget, it overwrites the setting
    :attr:`arrow_pos`.

    .. versionadded:: 2.2.0

    :attr:`flex_arrow_pos` is a :class:`~kivy.properties.ListProperty` and
    defaults to None.
    '''

    limit_to = ObjectProperty(None, allownone=True)
    '''Specifies the widget to which the bubbles position is restricted.

    .. versionadded:: 1.6.0

    :attr:`limit_to` is a :class:`~kivy.properties.ObjectProperty` and defaults
    to 'None'.
    '''

    arrow_margin_x = NumericProperty(0)
    '''Automatically computed margin in x direction that the arrow widget
    occupies in pixel.

    In combination with the :attr:`content_width`, this property can be used
    to determine the correct width of the Bubble to exactly enclose the
    arrow + content by adding :attr:`content_width` and :attr:`arrow_margin_x`

    .. versionadded:: 2.2.0

    :attr:`arrow_margin_x` is a :class:`~kivy.properties.NumericProperty` and
    represents the added margin in x direction due to the arrow widget.
    It defaults to 0 and is read only.
    '''

    arrow_margin_y = NumericProperty(0)
    '''Automatically computed margin in y direction that the arrow widget
    occupies in pixel.

    In combination with the :attr:`content_height`, this property can be used
    to determine the correct height of the Bubble to exactly enclose the
    arrow + content by adding :attr:`content_height` and :attr:`arrow_margin_y`

    .. versionadded:: 2.2.0

    :attr:`arrow_margin_y` is a :class:`~kivy.properties.NumericProperty` and
    represents the added margin in y direction due to the arrow widget.
    It defaults to 0 and is read only.
    '''

    arrow_margin = ReferenceListProperty(arrow_margin_x, arrow_margin_y)
    '''Automatically computed margin that the arrow widget occupies in
    x and y direction in pixel.

    Check the description of :attr:`arrow_margin_x` and :attr:`arrow_margin_y`.

    .. versionadded:: 2.2.0

    :attr:`arrow_margin` is a :class:`~kivy.properties.ReferenceListProperty`
    of (:attr:`arrow_margin_x`, :attr:`arrow_margin_y`) properties.
    It is read only.
    '''

    content_width = NumericProperty(0)
    '''The width of the content Widget.

    .. versionadded:: 2.2.0

    :attr:`content_width` is a :class:`~kivy.properties.NumericProperty` and
    is the same as self.content.width if content is not None, else it defaults
    to 0. It is read only.
    '''

    content_height = NumericProperty(0)
    '''The height of the content Widget.

    .. versionadded:: 2.2.0

    :attr:`content_height` is a :class:`~kivy.properties.NumericProperty` and
    is the same as self.content.height if content is not None, else it defaults
    to 0. It is read only.
    '''

    content_size = ReferenceListProperty(content_width, content_height)
    ''' The size of the content Widget.

    .. versionadded:: 2.2.0

    :attr:`content_size` is a :class:`~kivy.properties.ReferenceListProperty`
    of (:attr:`content_width`, :attr:`content_height`) properties.
    It is read only.
    '''

    # Internal map that specifies the different parameters for fixed arrow
    # position layouts. The flex_arrow_pos uses these parameter sets
    # as a template.
    # 0: orientation of the children of Bubble ([content, arrow])
    # 1: order of widgets to add to the BoxLayout (default: [content, arrow])
    # 2: size_hint of _arrow_image_layout
    # 3: rotation of the _arrow_image
    # 4: pos_hint of the _arrow_image_layout
    ARROW_LAYOUTS = {
        "bottom_left":  (   "vertical",  1, (   1, None),   0, {   "top": 1.0,        "x": 0.05}),  # noqa: E201,E241,E501
        "bottom_mid":   (   "vertical",  1, (   1, None),   0, {   "top": 1.0, "center_x": 0.50}),  # noqa: E201,E241,E501
        "bottom_right": (   "vertical",  1, (   1, None),   0, {   "top": 1.0,    "right": 0.95}),  # noqa: E201,E241,E501
        "right_bottom": ( "horizontal",  1, (None,    1),  90, {  "left": 0.0,        "y": 0.05}),  # noqa: E201,E241,E501
        "right_mid":    ( "horizontal",  1, (None,    1),  90, {  "left": 0.0, "center_y": 0.50}),  # noqa: E201,E241,E501
        "right_top":    ( "horizontal",  1, (None,    1),  90, {  "left": 0.0,      "top": 0.95}),  # noqa: E201,E241,E501
        "top_left":     (   "vertical", -1, (   1, None), 180, {"bottom": 0.0,        "x": 0.05}),  # noqa: E201,E241,E501
        "top_mid":      (   "vertical", -1, (   1, None), 180, {"bottom": 0.0, "center_x": 0.50}),  # noqa: E201,E241,E501
        "top_right":    (   "vertical", -1, (   1, None), 180, {"bottom": 0.0,    "right": 0.95}),  # noqa: E201,E241,E501
        "left_bottom":  ( "horizontal", -1, (None,    1), -90, {"right":  1.0,        "y": 0.05}),  # noqa: E201,E241,E501
        "left_mid":     ( "horizontal", -1, (None,    1), -90, {"right":  1.0, "center_y": 0.50}),  # noqa: E201,E241,E501
        "left_top":     ( "horizontal", -1, (None,    1), -90, {"right":  1.0,      "top": 0.95}),  # noqa: E201,E241,E501
    }

    def __init__(self, **kwargs):
        self.content = None

        self._flex_arrow_layout_params = None
        self._temporarily_ignore_limits = False

        self._arrow_image = Image(
            source=self.arrow_image,
            fit_mode="scale-down",
            color=self.arrow_color
        )
        self._arrow_image.width = self._arrow_image.texture_size[0]
        self._arrow_image.height = dp(self._arrow_image.texture_size[1])
        self._arrow_image_scatter = Scatter(
            size_hint=(None, None),
            do_scale=False,
            do_rotation=False,
            do_translation=False,
        )
        self._arrow_image_scatter.add_widget(self._arrow_image)
        self._arrow_image_scatter.size = self._arrow_image.texture_size
        self._arrow_image_scatter_wrapper = BoxLayout(
            size_hint=(None, None),
        )
        self._arrow_image_scatter_wrapper.add_widget(self._arrow_image_scatter)
        self._arrow_image_layout = RelativeLayout()
        self._arrow_image_layout.add_widget(self._arrow_image_scatter_wrapper)

        self._arrow_layout = None

        super().__init__(**kwargs)
        self.reposition_inner_widgets()

    def add_widget(self, widget, *args, **kwargs):
        if self.content is None:
            self.content = widget
            self.content_size = widget.size
            self.content.bind(size=self.update_content_size)
            self.reposition_inner_widgets()
        else:
            raise BubbleException(
                "Bubble can only contain a single Widget or Layout"
            )

    def remove_widget(self, widget, *args, **kwargs):
        if widget == self.content:
            self.content.unbind(size=self.update_content_size)
            self.content = None
            self.content_size = [0, 0]
            self.reposition_inner_widgets()
            return
        super().remove_widget(widget, *args, **kwargs)

    def on_content_size(self, instance, value):
        self.adjust_position()

    def on_limit_to(self, instance, value):
        self.adjust_position()

    def on_pos(self, instance, value):
        self.adjust_position()

    def on_size(self, instance, value):
        self.reposition_inner_widgets()

    def on_arrow_image(self, instance, value):
        self._arrow_image.source = self.arrow_image
        self._arrow_image.width = self._arrow_image.texture_size[0]
        self._arrow_image.height = dp(self._arrow_image.texture_size[1])
        self._arrow_image_scatter.size = self._arrow_image.texture_size
        self.reposition_inner_widgets()

    def on_arrow_color(self, instance, value):
        self._arrow_image.color = self.arrow_color

    def on_arrow_pos(self, instance, value):
        self.reposition_inner_widgets()

    def on_flex_arrow_pos(self, instance, value):
        self._flex_arrow_layout_params = self.get_flex_arrow_layout_params()
        self.reposition_inner_widgets()

    def get_flex_arrow_layout_params(self):
        pos = self.flex_arrow_pos

        if pos is None:
            return None

        x, y = pos
        if not (0 <= x <= self.width and 0 <= y <= self.height):
            return None

        # the order of the following list defines the side that the arrow
        # will be attached to in case of ambiguity (same distances)
        base_layouts_map = [
            ("bottom_mid", y),
            ("top_mid", self.height - y),
            ("left_mid", x),
            ("right_mid", self.width - x),
        ]
        base_layout_key = min(base_layouts_map, key=lambda val: val[1])[0]
        arrow_layout = list(Bubble.ARROW_LAYOUTS[base_layout_key])

        arrow_width = self._arrow_image.width

        # This function calculates the proper value for pos_hint, i.e., the
        # arrow texture does not 'overflow' and stays entirely connected to
        # the side of the content.
        def calc_x0(x, length):
            return x * (length - arrow_width) / (length * length)

        if base_layout_key == "bottom_mid":
            arrow_layout[-1] = {"top": 1.0, "x": calc_x0(x, self.width)}
        elif base_layout_key == "top_mid":
            arrow_layout[-1] = {"bottom": 0.0, "x": calc_x0(x, self.width)}
        elif base_layout_key == "left_mid":
            arrow_layout[-1] = {"right": 1.0, "y": calc_x0(y, self.height)}
        elif base_layout_key == "right_mid":
            arrow_layout[-1] = {"left": 0.0, "y": calc_x0(y, self.height)}
        return arrow_layout

    def update_content_size(self, instance, value):
        self.content_size = self.content.size

    def adjust_position(self):
        if self.limit_to is not None and not self._temporarily_ignore_limits:
            if self.limit_to is EventLoop.window:
                lim_x, lim_y = 0, 0
                lim_top, lim_right = self.limit_to.size
            else:
                lim_x = self.limit_to.x
                lim_y = self.limit_to.y
                lim_top = self.limit_to.top
                lim_right = self.limit_to.right

            self._temporarily_ignore_limits = True

            if not (lim_x > self.x and lim_right < self.right):
                self.x = max(lim_x, min(lim_right - self.width, self.x))

            if not (lim_y > self.y and lim_right < self.right):
                self.y = min(lim_top - self.height, max(lim_y, self.y))

            self._temporarily_ignore_limits = False

    def reposition_inner_widgets(self):
        arrow_image_layout = self._arrow_image_layout
        arrow_image_scatter = self._arrow_image_scatter
        arrow_image_scatter_wrapper = self._arrow_image_scatter_wrapper
        content = self.content

        # Remove the children of the Bubble (BoxLayout) as a first step
        for child in list(self.children):
            super().remove_widget(child)

        if self.canvas is None or content is None:
            return

        # find the layout parameters that define a specific bubble setup
        if self._flex_arrow_layout_params is not None:
            layout_params = self._flex_arrow_layout_params
        else:
            layout_params = Bubble.ARROW_LAYOUTS[self.arrow_pos]
        (bubble_orientation,
         widget_order,
         arrow_size_hint,
         arrow_rotation,
         arrow_pos_hint) = layout_params

        # rotate the arrow, place it at the right pos and setup the size
        # of the widget, so the BoxLayout can do the rest.
        arrow_image_scatter.rotation = arrow_rotation
        arrow_image_scatter_wrapper.size = arrow_image_scatter.bbox[1]
        arrow_image_scatter_wrapper.pos_hint = arrow_pos_hint
        arrow_image_layout.size_hint = arrow_size_hint
        arrow_image_layout.size = arrow_image_scatter.bbox[1]

        # set the orientation of the Bubble (BoxLayout)
        self.orientation = bubble_orientation

        # Add the updated children of the Bubble (BoxLayout) and update
        # properties
        widgets_to_add = [content, arrow_image_layout]

        # Set the arrow_margin, so we can use this property for proper sizing
        # of the Bubble Widget.
        # Determine whether to add the arrow_image_layout to the
        # Bubble (BoxLayout) or not.
        arrow_margin_x, arrow_margin_y = (0, 0)
        if self.show_arrow:
            if bubble_orientation[0] == "h":
                arrow_margin_x = arrow_image_layout.width
            elif bubble_orientation[0] == "v":
                arrow_margin_y = arrow_image_layout.height
        else:
            widgets_to_add.pop(1)

        for widget in widgets_to_add[::widget_order]:
            super().add_widget(widget)

        self.arrow_margin = (arrow_margin_x, arrow_margin_y)
