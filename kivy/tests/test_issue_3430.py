"""
Issue #3430 test
When Label.size is bound to Label.texture_size, it is not initially positioned
correctly when it is positioned via the right or top properties.
After its parent's width/height change, the Label position is corrected.

This unittest checks if the Label position changes between renders where
the parent width/height changes to a different value and then back to the
original value.
"""

from kivy.tests.common import GraphicUnitTest
from kivy.uix.widget import Widget
from kivy.uix.label import Label


def _create_widgets():
    # Create a Widget containing a Label
    widget = Widget()  # Label's parent
    label = Label(text='TestingLabel')
    # Bind Label's size to texture_size
    # Equivalent KV: size: self.texture_size
    label.bind(texture_size=label.setter('size'))
    widget.add_widget(label)
    return widget, label

class Issue3430LabelTextureSizePositionTopRight(GraphicUnitTest):

    def test_right(self):
        widget, label = _create_widgets()
        widget.bind(right=label.setter('right'))

        self.render(widget)
        # Sanity checks on widths
        self.assertGreater(label.width, 1)
        self.assertGreater(label.texture_size[0], 1)
        self.assertGreater(widget.width, 10)

        # This assertion fails on this render, but succeeds after the next.
        # self.assertEqual(label.right, widget.right)

        # Store values after first render
        label_x_1st_render = label.x
        label_right_1st_render = label.right
        label_width_1st_render = label.width
        widget_right_1st_render = widget.right
        widget_width_1st_render = widget.width

        # Set width to a different value and back to original value to trigger
        # property events, but keep a render image that *should be* identical.
        widget.width = widget_width_1st_render - 1
        widget.width = widget_width_1st_render
        self.render(widget)

        # Widths shouldn't have changed
        self.assertEqual(label.width, label_width_1st_render)
        self.assertEqual(widget.width, widget_width_1st_render)

        # Label is positioned correctly after 2nd render
        # These assertions would fail on the 1st render
        self.assertEqual(label.right, widget.right)
        self.assertEqual(label.x, widget.right - label.width)

        # Position shouldn't have changed
        self.assertEqual(widget.right, widget_right_1st_render)
        self.assertEqual(label.x, label_x_1st_render)
        self.assertEqual(label.right, label_right_1st_render)

    def test_top(self):
        widget, label = _create_widgets()
        widget.bind(top=label.setter('top'))

        self.render(widget)
        # Sanity checks on heights
        self.assertGreater(label.height, 1)
        self.assertGreater(label.texture_size[1], 1)
        self.assertGreater(widget.height, 10)

        # Store values after first render
        label_y_1st_render = label.y
        label_top_1st_render = label.top
        label_height_1st_render = label.height
        widget_top_1st_render = widget.top
        widget_height_1st_render = widget.height

        # Set height to a different value and back to original value to trigger
        # property events, but keep a render image that *should be* identical.
        widget.height = widget_height_1st_render - 1
        widget.height = widget_height_1st_render
        self.render(widget)

        # heights shouldn't have changed
        self.assertEqual(label.height, label_height_1st_render)
        self.assertEqual(widget.height, widget_height_1st_render)

        # Assert that Label is positioned correctly after 2nd render
        # These assertions would fail on the 1st render
        self.assertEqual(label.top, widget.top)
        self.assertEqual(label.y, widget.top - label.height)

        # Position shouldn't have changed
        self.assertEqual(widget.top, widget_top_1st_render)
        self.assertEqual(label.y, label_y_1st_render)
        self.assertEqual(label.top, label_top_1st_render)
