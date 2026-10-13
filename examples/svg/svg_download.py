"""
svg_download.py
---------------
Download and display SVGs from a number of websites using AsyncSvgWidget.
Use the slider to zoom from 64 px to 2 K, scroll to pan, and Prev/Next
to cycle through a set of SVGs.

Run from the repo root::

    python examples/svg/svg_download.py
"""

# Verified working SVG sources (checked at time of writing):
SVGS = [
    (
        'Ghostscript Tiger',
        'https://upload.wikimedia.org/wikipedia/commons/f/fd/Ghostscript_Tiger.svg',
    ),
    (
        'World Map',
        'https://upload.wikimedia.org/wikipedia/commons/0/0a/Four_color_world_map.svg',
    ),
    (
        'Flag — Italy',
        'https://flagcdn.com/it.svg',
    ),
    (
        'Flag — South Africa',
        'https://flagcdn.com/za.svg',
    ),
    (
        'Flag — United Kingdom',
        'https://flagcdn.com/gb.svg',
    ),
    (
        'Flag — Costa Rica',
        'https://flagcdn.com/cr.svg',
    ),
    (
        'Flag — Netherlands',
        'https://flagcdn.com/nl.svg',
    ),
    (
        'Flag — USA',
        'https://flagcdn.com/us.svg',
    ),
    (
        'Flag — India',
        'https://flagcdn.com/in.svg',
    ),
    (
        'Flag — Finland',
        'https://flagcdn.com/fi.svg',
    ),
    (
        'Flag — Norway',
        'https://flagcdn.com/no.svg',
    ),
    (
        'Python Logo',
        'https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg',
    ),
    (
        'Sun',
        'https://raw.githubusercontent.com/hfg-gmuend/openmoji/master/color/svg/2600.svg',
    ),
    (
        'Earth',
        'https://raw.githubusercontent.com/hfg-gmuend/openmoji/master/color/svg/1F30D.svg',
    ),
    (
        'Dragon',
        'https://raw.githubusercontent.com/hfg-gmuend/openmoji/master/color/svg/1F409.svg',
    ),
    (
        'Robot',
        'https://raw.githubusercontent.com/hfg-gmuend/openmoji/master/color/svg/1F916.svg',
    ),
]

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window

KV = """
<DownloadTestRoot>:
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
            on_release: root.prev_svg()
        Label:
            text: root.svg_name
            font_size: '13sp'
            bold: True
            color: 0.9, 0.9, 0.9, 1
        Button:
            text: 'Next >'
            size_hint_x: None
            width: '64sp'
            on_release: root.next_svg()

    # ---- status / info ----
    Label:
        id: info
        size_hint_y: None
        height: '22sp'
        font_size: '12sp'
        color: 0.6, 0.9, 1, 1
        text: 'Loading...'

    # ---- scrollable stage ----
    ScrollView:
        do_scroll_x: True
        do_scroll_y: True
        bar_width: 8
        AsyncSvgWidget:
            id: svg
            source: root.svg_url
            fit_mode: 'contain'
            size_hint: None, None
            size: slider.value, slider.value
            on_load:
                vw, vh = self.viewbox_size
                info.text = f'Ready  |  viewbox {vw:.0f} x {vh:.0f}'
            on_error: info.text = f'Error: {args[1]}'
            on_texture:
                vw, vh = self.viewbox_size
                tw, th = self.texture_size
                info.text = f'viewbox {vw:.0f} x {vh:.0f} px  |  Texture {tw} x {th} px'
            canvas.before:
                Color:
                    rgba: 0.08, 0.08, 0.08, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

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
            value: 512
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
        text: '%d px' % slider.value
"""

Builder.load_string(KV)


class DownloadTestRoot(BoxLayout):
    svg_url = StringProperty(SVGS[0][1])
    svg_name = StringProperty(SVGS[0][0])
    _index = NumericProperty(0)

    def _load(self):
        name, url = SVGS[int(self._index)]
        self.svg_name = name
        self.svg_url = url
        self.ids.info.text = 'Downloading %s…' % name

    def prev_svg(self):
        self._index = (self._index - 1) % len(SVGS)
        self._load()

    def next_svg(self):
        self._index = (self._index + 1) % len(SVGS)
        self._load()


class DownloadTestApp(App):
    title = 'AsyncSvgWidget download test'

    def build(self):
        Window.size = (800, 800)
        return DownloadTestRoot()


if __name__ == '__main__':
    DownloadTestApp().run()
