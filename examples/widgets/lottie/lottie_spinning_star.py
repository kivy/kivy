'''
Spinning star
=============

Combines :class:`~kivy.uix.behaviors.ButtonBehavior` with
:class:`~kivy.uix.lottie.LottieWidget`. The bundled Lottie defines two
**markers** — ``spin`` (one full rotation) and ``grow`` (scale pulse) — and
each tap alternates which marker plays so behaviour comes from the file, not
hard-coded animation names in Python.

**Press** slightly shrinks the widget; **release** plays the next marker and
returns to the idle frame when the segment ends
(:attr:`~kivy.uix.lottie.LottieWidget.eos` ``'stop'``).

Requires a Lottie provider (e.g. ``pip install thorvg-python``).

Run from ``examples/widgets/lottie/``::

    python lottie_spinning_star.py

Or from the Kivy source tree root::

    python examples/widgets/lottie/lottie_spinning_star.py
'''

from pathlib import Path

from kivy.animation import Animation
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.lottie import LottieWidget

DIR = Path(__file__).resolve().parent
SOURCE = str(DIR / 'lottie_spinning_star.json')


kv = '''
<LottieReactionButton>:
    canvas.before:
        PushMatrix
        Translate:
            xy: self.center_x, self.center_y
        Scale:
            xyz: self.pulse, self.pulse, 1
        Translate:
            xy: -self.center_x, -self.center_y
    canvas.after:
        PopMatrix

BoxLayout:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: 0.96, 0.96, 0.96, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: 'Tap the star: alternate spin/grow markers (lottie_spinning_star.json).'
        size_hint_y: None
        height: self.texture_size[1] + dp(8)
        color: 0.15, 0.15, 0.15, 1

    LottieReactionButton:
        id: lottie
        source: app.json_source
        fit_mode: 'contain'
        state: 'stop'
        eos: 'stop'
'''

class LottieReactionButton(ButtonBehavior, LottieWidget):
    '''Tappable Lottie; press squash, release plays alternating Lottie markers.'''

    pulse = NumericProperty(1.0)
    prefer_spin = BooleanProperty(True)

    def on_press(self, touch):
        """ Use Animation to squash the star when pressed. """
        Animation.cancel_all(self, 'pulse')
        Animation(pulse=0.88, d=0.07, t='out_quad').start(self)

    def on_release(self, touch):
        if not self.loaded:
            return
        Animation.cancel_all(self, 'pulse')
        self.pulse = 1.0
        marker = 'spin' if self.prefer_spin else 'grow'
        self.prefer_spin = not self.prefer_spin
        self.play_marker(marker)
        self.state = 'play'


class SpinningStarApp(App):
    json_source = SOURCE

    def build(self):
        return Builder.load_string(kv)


if __name__ == '__main__':
    SpinningStarApp().run()
