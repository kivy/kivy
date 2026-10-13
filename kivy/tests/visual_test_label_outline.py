"""
Visual test for ``font_blended`` and ``outline_width`` with the SDL3 text
provider.

Run it with::

    python kivy/tests/visual_test_label_outline.py

It shows the same text four times, with ``font_blended`` on and off and with
and without an outline. Under each label is a crop of its texture, magnified
without smoothing, so single pixels are visible.

What to look for:

- ``font_blended=True``: soft, antialiased edges, with or without an outline.
- ``font_blended=False``: hard, jagged edges, with or without an outline.
  The edges of the outline are also hard, and with an outline the text is
  still drawn in its own color (green) inside the red outline.

To save an image and exit, instead of opening a window that stays open, set
``OUTLINE_SCREENSHOT`` to a file name::

    OUTLINE_SCREENSHOT=out.png python kivy/tests/visual_test_label_outline.py
"""

import os
import sys

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget

TEXT = 'Rag'
FONT_SIZE = 64
OUTLINE_WIDTH = 3
OUTLINE_COLOR = (1, 0, 0, 1)
TEXT_COLOR = (0, 1, 0, 1)
BACKGROUND = (0.15, 0.15, 0.15, 1)
CROP_SIZE = 48  # pixels of the texture that are magnified
ZOOM = 6


class Magnifier(Widget):
    """Draws the lower left corner of a label's texture, magnified, without
    smoothing."""

    def __init__(self, label, **kwargs):
        super().__init__(**kwargs)
        label.texture_update()
        texture = label.texture
        texture.mag_filter = 'nearest'
        texture.min_filter = 'nearest'
        width = min(CROP_SIZE, texture.width)
        height = min(CROP_SIZE, texture.height)
        crop = texture.get_region(0, 0, width, height)
        self._crop_size = (width * ZOOM, height * ZOOM)
        with self.canvas:
            Color(1, 1, 1, 1)
            self._rect = Rectangle(texture=crop, size=self._crop_size)
        self.bind(pos=self._center, size=self._center)

    def _center(self, *args):
        self._rect.pos = (
            self.center_x - self._crop_size[0] / 2,
            self.center_y - self._crop_size[1] / 2,
        )


class Sample(BoxLayout):

    def __init__(self, font_blended, outline_width, **kwargs):
        super().__init__(orientation='vertical', padding=10, **kwargs)
        self.add_widget(Label(
            text='font_blended={}, outline_width={}'.format(
                font_blended, outline_width),
            font_size=16,
            size_hint_y=None,
            height=30,
        ))
        label = Label(
            text=TEXT,
            font_size=FONT_SIZE,
            font_blended=font_blended,
            outline_width=outline_width,
            outline_color=OUTLINE_COLOR,
            color=TEXT_COLOR,
            text_provider='sdl3',
        )
        label.size_hint_y = None
        label.height = FONT_SIZE * 2
        self.add_widget(label)
        self.add_widget(Magnifier(label))


class OutlineApp(App):

    def __init__(self, screenshot=None, **kwargs):
        super().__init__(**kwargs)
        self.screenshot = screenshot

    def build(self):
        Window.size = (1000, 900)
        grid = GridLayout(cols=2)
        # Draw the background in the widget, so it is also in the screenshot.
        with grid.canvas.before:
            Color(*BACKGROUND)
            background = Rectangle(size=grid.size)
        grid.bind(
            pos=lambda widget, pos: setattr(background, 'pos', pos),
            size=lambda widget, size: setattr(background, 'size', size),
        )
        for font_blended in (True, False):
            for outline_width in (0, OUTLINE_WIDTH):
                grid.add_widget(Sample(font_blended, outline_width))
        if self.screenshot:
            Clock.schedule_once(self._save_and_exit, 1)
        return grid

    def _save_and_exit(self, dt):
        self.root.export_to_png(self.screenshot)
        self.stop()


def main():
    if LabelBase.get_provider_class('sdl3') is None:
        print('The sdl3 text provider is not available.')
        return 1
    OutlineApp(screenshot=os.environ.get('OUTLINE_SCREENSHOT')).run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
