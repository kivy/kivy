"""
svg_scale.py
------------
Manual test: load SVGs from the same directory, zoom with the slider
(64 px - 2 K), and scroll freely around the image when it is larger
than the viewport.

Run from the repo root::

    python examples/svg/svg_scale.py
"""

from pathlib import Path

SVG_DIR = Path(__file__).parent
SVG_FILES = sorted(str(p) for p in SVG_DIR.glob('*.svg'))

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout

KV = """
<ScaleTestRoot>:  # a BoxLayout
    orientation: 'vertical'
    padding: 16
    spacing: 8

    # ---- file switcher ----
    BoxLayout:
        size_hint_y: None
        height: '36sp'
        spacing: 6
        Button:
            text: '< Prev'
            size_hint_x: None
            width: '64sp'
            on_release: root.prev_file()
        Label:
            text: root.current_filename
            font_size: '12sp'
            color: 0.8, 0.8, 0.8, 1
        Button:
            text: 'Next >'
            size_hint_x: None
            width: '64sp'
            on_release: root.next_file()

    # ---- info ----
    Label:
        id: info
        size_hint_y: None
        height: '24sp'
        font_size: '12sp'
        color: 0.6, 0.9, 1, 1
        text: 'Loading...'

    # ---- scrollable stage ----
    ScrollView:
        do_scroll_x: True
        do_scroll_y: True
        bar_width: 8
        canvas.before:
            Color:
                rgba: 0.96, 0.96, 0.94, 1
            Rectangle:
                pos: self.pos
                size: self.size
        SvgWidget:
            id: svg
            source: root.svg_path
            fit_mode: 'contain'
            size_hint: None, None
            size: slider.value, slider.value
            on_load:
                vw, vh = self.viewbox_size
                info.text = f'Loaded  |  viewbox {vw:.0f} x {vh:.0f}'
            on_texture:
                vw, vh = self.viewbox_size
                tw, th = self.texture_size
                info.text = f'viewbox {vw:.0f} x {vh:.0f} px  |  Texture {tw} x {th} px'

    # ---- slider ----
    BoxLayout:
        size_hint_y: None
        height: '44sp'
        spacing: 8
        Label:
            text: '64 px'
            size_hint_x: None
            width: '52sp'
            font_size: '12sp'
            halign: 'right'
            valign: 'middle'
            text_size: self.size
        Slider:
            id: slider
            min: 64
            max: 2048
            value: 256
            step: 1
        Label:
            text: '2 K'
            size_hint_x: None
            width: '36sp'
            font_size: '12sp'
            halign: 'left'
            valign: 'middle'
            text_size: self.size

    Label:
        size_hint_y: None
        height: '18sp'
        font_size: '12sp'
        color: 0.7, 0.7, 0.7, 1
        text: f'{slider.value} px'

ScaleTestRoot:
"""


class ScaleTestRoot(BoxLayout):
    svg_path = StringProperty(SVG_FILES[0])
    current_filename = StringProperty(Path(SVG_FILES[0]).name)
    _file_index = NumericProperty(0)

    def _update_file(self):
        self.svg_path = SVG_FILES[self._file_index]
        self.current_filename = Path(self.svg_path).name

    def prev_file(self):
        self._file_index = (self._file_index - 1) % len(SVG_FILES)
        self._update_file()

    def next_file(self):
        self._file_index = (self._file_index + 1) % len(SVG_FILES)
        self._update_file()


class ScaleTestApp(App):
    title = 'SvgWidget scale test'

    def build(self):
        return Builder.load_string(KV)


if __name__ == '__main__':
    ScaleTestApp().run()
