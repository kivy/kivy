'''
Spinning Kivy-style logo with runtime color slots
=================================================

Demonstrates :meth:`~kivy.uix.lottie.LottieWidget.set_color` on a named slot
(``logoFill`` on the main logo fill in ``lottie_logo_anim.json``) so the same
Lottie file can be tinted for different brands or themes without reloading.

Requires a Lottie provider (e.g. ``pip install thorvg-python``).

Run from ``examples/widgets/lottie/``::

    python lottie_slot_theme.py

Or from the Kivy source tree root::

    python examples/widgets/lottie/lottie_slot_theme.py
'''

from pathlib import Path

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

DIR = Path(__file__).resolve().parent
SOURCE = str(DIR / 'lottie_logo_anim.json')

kv ='''
ThemeRoot:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: 0.96, 0.96, 0.96, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: 'Tap a button to recolor the logo (slot logoFill).'
        size_hint_y: None
        height: self.texture_size[1] + dp(8)
        color: 0.15, 0.15, 0.15, 1

    LottieWidget:
        id: lottie
        source: app.json_source
        fit_mode: 'contain'
        state: 'play'
        eos: 'loop'

    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(6)
        Button:
            text: 'Green'
            on_release: root._apply((0.07, 0.6, 0.41, 1))
        Button:
            text: 'Ocean'
            on_release: root._apply((0.15, 0.45, 0.95, 1))
        Button:
            text: 'Sunset'
            on_release: root._apply((0.95, 0.45, 0.2, 1))
        Button:
            text: 'Violet'
            on_release: root._apply((0.55, 0.25, 0.85, 1))
'''


class ThemeRoot(BoxLayout):
    def _apply(self, rgba):
        w = self.ids.lottie
        if not w.loaded or not w.has_slot('logoFill'):
            return
        w.set_color('logoFill', rgba)


class SlotThemeApp(App):
    json_source = SOURCE

    def build(self):
        return Builder.load_string(kv)


if __name__ == '__main__':
    SlotThemeApp().run()
