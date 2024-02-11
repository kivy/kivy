"""
Color Wheel and Color Picker Tests
==================================
"""

from kivy.tests.common import GraphicUnitTest, UTMotionEvent
from kivy.uix.colorpicker import ColorWheel, ColorPicker


class ColorWheelTest(GraphicUnitTest):
    def test_render(self):
        color_wheel = ColorWheel()
        self.render(color_wheel)

    def test_clicks(self):
        color_wheel = ColorWheel()

        # ColorPicker has a stated default colour (opaque white).
        # ColorWheel has a different default Color (transparent black).
        self.assertEqual(color_wheel.color, [0, 0, 0, 0])

        # Click on corner of widget
        pos = (color_wheel.pos[0], color_wheel.pos[1])
        touch = UTMotionEvent(
            "unittest",
            1,
            {
                "x": pos[0],
                "y": pos[1],
            },
        )
        touch.grab_current = color_wheel
        touch.pos = pos

        color_wheel.on_touch_down(touch)
        color_wheel.on_touch_up(touch)

        # Too far from the center. No effect.
        self.assertEqual(color_wheel.color, [0, 0, 0, 0])

        pos = (
            color_wheel.pos[0] + color_wheel.size[0] / 2,
            color_wheel.pos[1] + color_wheel.size[1] / 4,
        )
        # Click in middle, half-the-radius up.
        touch = UTMotionEvent(
            "unittest",
            1,
            {"x": pos[0], "y": pos[1]},
        )
        touch.grab_current = color_wheel
        touch.pos = pos

        color_wheel.on_touch_down(touch)
        color_wheel.on_touch_up(touch)

        self.assertEqual(color_wheel.color, [0.75, 0.5, 1, 1])


class ColorPickerTest(GraphicUnitTest):
    def test_render(self):
        color_picker = ColorPicker()
        self.render(color_picker)

    def test_set_colour(self):
        color_picker = ColorPicker()
        # ColorPicker has a stated default colour (opaque white).
        # ColorWheel has a different default Color (transparent black).
        self.assertEqual(color_picker.color, [1, 1, 1, 1])

        # Set without alpha
        color_picker.set_color((0.5, 0.6, 0.7))
        self.assertEqual(color_picker.color, [0.5, 0.6, 0.7, 1])

        # Set with alpha
        color_picker.set_color((0.5, 0.6, 0.7, 0.8))
        self.assertEqual(color_picker.color, [0.5, 0.6, 0.7, 0.8])
