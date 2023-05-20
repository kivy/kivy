'''
Bubble unit tests
=================
author: Anthony Zimmermann (Anthony.Zimmermann@protonmail.com)
'''

import pytest
from kivy.tests.common import GraphicUnitTest

from kivy.base import EventLoop

from kivy.uix.bubble import Bubble
from kivy.uix.bubble import BubbleContent
from kivy.uix.bubble import BubbleButton


class _TestBubbleButton(BubbleButton):

    def __init__(self, button_size=(None, None), *args, **kwargs):
        super().__init__(*args, **kwargs)

        size_x, size_y = button_size
        if size_x is not None:
            self.size_hint_x = None
            self.width = size_x
        if size_y is not None:
            self.size_hint_y = None
            self.height = size_y


class _TestBubbleContent(BubbleContent):

    def update_size(self, instance, value):
        self.size = self.minimum_size

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bind(minimum_size=self.update_size)


class _TestBubble(Bubble):

    @property
    def arrow_length(self):
        return self._arrow_image.height

    @property
    def arrow_width(self):
        return self._arrow_image.width

    @property
    def arrow_rotation(self):
        return self._arrow_image_scatter.rotation

    @property
    def arrow_layout_pos(self):
        return self._arrow_image_layout.pos

    @property
    def arrow_layout_size(self):
        return self._arrow_image_layout.size

    @property
    def arrow_center_pos_within_arrow_layout(self):
        x = self._arrow_image_scatter_wrapper.center_x
        y = self._arrow_image_scatter_wrapper.center_y
        return x, y


# (bubble_width, button_height, arrow_pos)
bubble_layout_with_predefined_arrow_pos_test_params = [
    (158.9, 34.3, "bottom_left"),   # noqa: E201,E241
    (651.4, 26.1, "bottom_mid"),    # noqa: E201,E241
    (  6.5, 44.7, "bottom_right"),  # noqa: E201,E241
    (754.6, 50.6, "top_left"),      # noqa: E201,E241
    (957.8, 74.1, "top_mid"),       # noqa: E201,E241
    (852.1, 33.1, "top_right"),     # noqa: E201,E241
    (472.9, 45.1, "left_top"),      # noqa: E201,E241
    (578.3, 52.7, "left_mid"),      # noqa: E201,E241
    (687.8, 17.7, "left_bottom"),   # noqa: E201,E241
    (313.7,  8.6, "right_top"),     # noqa: E201,E241
    (194.3, 46.4, "right_mid"),     # noqa: E201,E241
    ( 59.3, 29.7, "right_bottom"),  # noqa: E201,E241
]

bubble_layout_with_flex_arrow_pos_test_params = [
    (101.3, 346.0,   0.0,  73.6, "l"),  # noqa: E201,E241
    (489.0, 535.1,   0.0, 442.1, "l"),  # noqa: E201,E241
    (390.9, 728.1,   0.0, 114.3, "l"),  # noqa: E201,E241
    (224.5, 675.5,   0.0, 560.6, "l"),  # noqa: E201,E241
    (264.9, 677.3,   0.0,   8.3, "l"),  # noqa: E201,E241
    (544.6, 126.0,   0.0, 120.9, "l"),  # noqa: E201,E241
    (290.9, 962.6,   0.0, 275.5, "l"),  # noqa: E201,E241
    (358.4, 514.4,   0.0, 427.1, "l"),  # noqa: E201,E241
    (604.3, 648.2,   0.0, 226.1, "l"),  # noqa: E201,E241
    (287.4, 875.6,   0.0, 446.5, "l"),  # noqa: E201,E241
    (755.7, 103.5, 444.6,   0.0, "b"),  # noqa: E201,E241
    (307.9, 471.7,  80.9,   0.0, "b"),  # noqa: E201,E241
    (849.9, 194.8, 652.7,   0.0, "b"),  # noqa: E201,E241
    (975.7, 691.0, 120.9,   0.0, "b"),  # noqa: E201,E241
    (539.1, 903.3, 530.6,   0.0, "b"),  # noqa: E201,E241
    ( 37.5, 727.5,  37.0,   0.0, "b"),  # noqa: E201,E241
    (856.5, 779.0, 565.5,   0.0, "b"),  # noqa: E201,E241
    (536.7, 228.3,  48.4,   0.0, "b"),  # noqa: E201,E241
    (170.9, 870.4, 127.6,   0.0, "b"),  # noqa: E201,E241
    (955.7, 530.6, 526.0,   0.0, "b"),  # noqa: E201,E241
    (878.1, 690.4, 878.1,  18.8, "r"),  # noqa: E201,E241
    (771.6, 365.2, 771.6,  31.1, "r"),  # noqa: E201,E241
    (679.7, 305.4, 679.7, 259.6, "r"),  # noqa: E201,E241
    (700.2, 614.6, 700.2, 105.4, "r"),  # noqa: E201,E241
    (444.1, 864.5, 444.1, 152.3, "r"),  # noqa: E201,E241
    (189.0, 790.4, 189.0, 602.9, "r"),  # noqa: E201,E241
    (376.0, 993.9, 376.0, 486.4, "r"),  # noqa: E201,E241
    (518.5, 338.5, 518.5, 194.6, "r"),  # noqa: E201,E241
    (982.1, 666.1, 982.1, 282.5, "r"),  # noqa: E201,E241
    (926.4, 565.1, 926.4, 187.3, "r"),  # noqa: E201,E241
    (375.2, 746.6,  36.2, 746.6, "t"),  # noqa: E201,E241
    (448.9, 228.5, 297.4, 228.5, "t"),  # noqa: E201,E241
    (792.3, 593.5, 746.2, 593.5, "t"),  # noqa: E201,E241
    (856.1,  89.7,  23.1,  89.7, "t"),  # noqa: E201,E241
    (721.3, 319.0, 356.5, 319.0, "t"),  # noqa: E201,E241
    (127.7, 355.7,  69.3, 355.7, "t"),  # noqa: E201,E241
    (412.3, 493.8, 163.2, 493.8, "t"),  # noqa: E201,E241
    ( 40.8, 115.8,  15.8, 115.8, "t"),  # noqa: E201,E241
    (233.9, 148.5, 189.4, 148.5, "t"),  # noqa: E201,E241
    (982.4, 661.5, 105.9, 661.5, "t"),  # noqa: E201,E241
]


class BubbleTest(GraphicUnitTest):

    def move_frames(self, t):
        for i in range(t):
            EventLoop.idle()

    def test_no_content(self):
        bubble = Bubble()
        self.render(bubble)

    def test_add_remove_content(self):
        bubble = Bubble()
        content = BubbleContent()
        bubble.add_widget(content)
        self.render(bubble)

        bubble.remove_widget(content)
        self.render(bubble)

    def test_add_arbitrary_content(self):
        from kivy.uix.gridlayout import GridLayout
        bubble = Bubble()
        content = GridLayout()
        bubble.add_widget(content)
        self.render(bubble)

    def test_add_two_content_widgets_fails(self):
        from kivy.uix.bubble import BubbleException
        bubble = Bubble()
        content_1 = BubbleContent()
        content_2 = BubbleContent()
        bubble.add_widget(content_1)
        with self.assertRaises(BubbleException):
            bubble.add_widget(content_2)

    def test_add_content_with_buttons(self):
        bubble = Bubble()

        content = BubbleContent()
        content.add_widget(BubbleButton(text="Option A"))
        content.add_widget(BubbleButton(text="Option B"))

        bubble.add_widget(content)
        self.render(bubble)

    def assertSequenceAlmostEqual(self, seq1, seq2, delta=None):
        assert len(seq1) == len(seq2)
        for a, b in zip(seq1, seq2):
            self.assertAlmostEqual(a, b, delta=delta)

    def assertTestBubbleLayoutWithPredefinedArrowPos(self, bubble):
        arrow_length = bubble.arrow_length
        arrow_width = bubble.arrow_width
        bubble_width = bubble.test_bubble_width
        button_height = bubble.test_button_height

        # assert content size
        expected_content_size = {
            "bottom_left": (bubble_width, button_height),
            "bottom_mid": (bubble_width, button_height),
            "bottom_right": (bubble_width, button_height),
            "top_left": (bubble_width, button_height),
            "top_mid": (bubble_width, button_height),
            "top_right": (bubble_width, button_height),
            "left_top": (bubble_width - arrow_length, button_height),
            "left_mid": (bubble_width - arrow_length, button_height),
            "left_bottom": (bubble_width - arrow_length, button_height),
            "right_top": (bubble_width - arrow_length, button_height),
            "right_mid": (bubble_width - arrow_length, button_height),
            "right_bottom": (bubble_width - arrow_length, button_height),
        }[bubble.arrow_pos]
        self.assertSequenceAlmostEqual(
            bubble.content.size,
            expected_content_size,
        )

        # assert arrow layout size
        expected_arrow_layout_size = {
            "bottom_left": (bubble_width, arrow_length),
            "bottom_mid": (bubble_width, arrow_length),
            "bottom_right": (bubble_width, arrow_length),
            "top_left": (bubble_width, arrow_length),
            "top_mid": (bubble_width, arrow_length),
            "top_right": (bubble_width, arrow_length),
            "left_top": (arrow_length, button_height),
            "left_mid": (arrow_length, button_height),
            "left_bottom": (arrow_length, button_height),
            "right_top": (arrow_length, button_height),
            "right_mid": (arrow_length, button_height),
            "right_bottom": (arrow_length, button_height),
        }[bubble.arrow_pos]
        self.assertSequenceAlmostEqual(
            bubble.arrow_layout_size,
            expected_arrow_layout_size,
        )

        # assert content position
        expected_content_position = {
            "bottom_left": (0, arrow_length),
            "bottom_mid": (0, arrow_length),
            "bottom_right": (0, arrow_length),
            "top_left": (0, 0),
            "top_mid": (0, 0),
            "top_right": (0, 0),
            "left_top": (arrow_length, 0),
            "left_mid": (arrow_length, 0),
            "left_bottom": (arrow_length, 0),
            "right_top": (0, 0),
            "right_mid": (0, 0),
            "right_bottom": (0, 0),
        }[bubble.arrow_pos]
        self.assertSequenceAlmostEqual(
            bubble.content.pos,
            expected_content_position,
        )

        # assert arrow layout position
        expected_arrow_layout_position = {
            "bottom_left": (0, 0),
            "bottom_mid": (0, 0),
            "bottom_right": (0, 0),
            "top_left": (0, button_height),
            "top_mid": (0, button_height),
            "top_right": (0, button_height),
            "left_top": (0, 0),
            "left_mid": (0, 0),
            "left_bottom": (0, 0),
            "right_top": (bubble_width - arrow_length, 0),
            "right_mid": (bubble_width - arrow_length, 0),
            "right_bottom": (bubble_width - arrow_length, 0),
        }[bubble.arrow_pos]
        self.assertSequenceAlmostEqual(
            bubble.arrow_layout_pos,
            expected_arrow_layout_position,
        )

        # assert arrow position within arrow layout
        hal = arrow_length / 2  # hal := half arrow length
        x_offset = 0.05 * bubble_width
        y_offset = 0.05 * button_height
        expected_arrow_center_pos_within_arrow_layout = {
            "bottom_left": (x_offset + arrow_width / 2, hal),
            "bottom_mid": (bubble_width / 2, hal),
            "bottom_right": (bubble_width - arrow_width / 2 - x_offset, hal),
            "top_left": (x_offset + arrow_width / 2, hal),
            "top_mid": (bubble_width / 2, hal),
            "top_right": (bubble_width - arrow_width / 2 - x_offset, hal),
            "left_top": (hal, button_height - arrow_width / 2 - y_offset),
            "left_mid": (hal, button_height / 2),
            "left_bottom": (hal, y_offset + arrow_width / 2),
            "right_top": (hal, button_height - arrow_width / 2 - y_offset),
            "right_mid": (hal, button_height / 2),
            "right_bottom": (hal, y_offset + arrow_width / 2),
        }[bubble.arrow_pos]
        self.assertSequenceAlmostEqual(
            bubble.arrow_center_pos_within_arrow_layout,
            expected_arrow_center_pos_within_arrow_layout,
        )

        # assert arrow rotation
        expected_arrow_rotation = {
            "bottom_left": 0,
            "bottom_mid": 0,
            "bottom_right": 0,
            "top_left": 180,
            "top_mid": 180,
            "top_right": 180,
            "left_top": 270,
            "left_mid": 270,
            "left_bottom": 270,
            "right_top": 90,
            "right_mid": 90,
            "right_bottom": 90,
        }[bubble.arrow_pos]
        self.assertAlmostEqual(
            bubble.arrow_rotation,
            expected_arrow_rotation,
        )

    def test_bubble_layout_with_predefined_arrow_pos(self):

        for params in bubble_layout_with_predefined_arrow_pos_test_params:
            bubble_width, button_height, arrow_pos = params

            with self.subTest():
                print(
                    "(bubble_width={}, button_height={}, arrow_pos={})".format(
                        *params
                    )
                )
                bubble = _TestBubble(arrow_pos=arrow_pos)
                bubble.size_hint = (None, None)
                bubble.test_bubble_width = bubble_width
                bubble.test_button_height = button_height

                def update_bubble_size(instance, value):
                    w = bubble_width
                    h = bubble.content_height + bubble.arrow_margin_y
                    bubble.size = (w, h)
                bubble.bind(
                    content_size=update_bubble_size,
                    arrow_margin=update_bubble_size,
                )

                content = _TestBubbleContent()
                for i in range(3):
                    content.add_widget(
                        _TestBubbleButton(
                            button_size=(None, button_height),
                            text="Option {}".format(i)
                        )
                    )

                bubble.add_widget(content)
                self.render(bubble)

                self.assertTestBubbleLayoutWithPredefinedArrowPos(bubble)

    def test_bubble_layout_without_arrow(self):
        bubble_width = 200
        button_height = 30

        bubble = _TestBubble(show_arrow=False)
        bubble.size_hint = (None, None)

        def update_bubble_size(instance, value):
            w = bubble_width
            h = bubble.content_height
            bubble.size = (w, h)
        bubble.bind(content_size=update_bubble_size)

        content = _TestBubbleContent(orientation="vertical")
        for i in range(7):
            content.add_widget(
                _TestBubbleButton(
                    button_size=(None, button_height),
                    text="Option_{}".format(i)
                )
            )

        bubble.add_widget(content)
        self.render(bubble)

        # assert content size
        self.assertSequenceAlmostEqual(
            bubble.content.size,
            (bubble_width, 7 * button_height),
        )

        # assert content position
        self.assertSequenceAlmostEqual(
            bubble.content.pos,
            (0, 0),
        )

    def test_bubble_layout_with_flex_arrow_pos(self):
        for params in bubble_layout_with_flex_arrow_pos_test_params:
            bubble_size = params[:2]
            flex_arrow_pos = params[2:4]
            arrow_side = params[4]
            with self.subTest():
                print("(w={}, h={}, x={}, y={}, side={})".format(*params))

                bubble = _TestBubble()
                bubble.size_hint = (None, None)
                bubble.size = bubble_size
                bubble.flex_arrow_pos = flex_arrow_pos

                content = _TestBubbleContent(orientation="vertical")
                content.size_hint = (1, 1)

                button = _TestBubbleButton(
                    button_size=(None, None),
                    text="Option",
                )
                button.size_hint_y = 1

                content.add_widget(button)
                bubble.add_widget(content)

                self.render(bubble)

                haw = bubble.arrow_width / 2  # half arrow_width
                if arrow_side in ["l", "r"]:
                    self.assertSequenceAlmostEqual(
                        bubble.arrow_center_pos_within_arrow_layout,
                        (haw, flex_arrow_pos[1]),
                        delta=haw,
                    )
                elif arrow_side in ["b", "t"]:
                    self.assertSequenceAlmostEqual(
                        bubble.arrow_center_pos_within_arrow_layout,
                        (flex_arrow_pos[0], haw),
                        delta=haw,
                    )
