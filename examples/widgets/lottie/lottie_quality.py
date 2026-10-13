'''
Rendering quality (blur / shadow fidelity)
==========================================

:meth:`~kivy.uix.lottie.LottieWidget.set_quality` trades performance against
accuracy for **effect-heavy** Lotties (blur, drop shadow, etc.). This demo uses
a composition with Gaussian blur.

Requires a Lottie provider.  The default ThorVG backend ships with
Kivy's official desktop wheels and needs no extra install.

Run from ``examples/widgets/lottie/``::

    python lottie_quality.py

Or from the Kivy source tree root::

    python examples/widgets/lottie/lottie_quality.py
'''

from pathlib import Path

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

DIR = Path(__file__).resolve().parent
SOURCE = str(DIR / 'lottie_quality.json')

kv = '''
QualityRoot:
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
        text: 'Quality: lower = faster, higher = smoother blur / shadows.'
        size_hint_y: None
        height: self.texture_size[1] + dp(8)
        color: 0.15, 0.15, 0.15, 1

    LottieWidget:
        id: lottie
        source: app.json_source
        fit_mode: 'contain'
        state: 'play'
        eos: 'loop'
        on_load: root._sync_quality()

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(12)
        Label:
            text: '0'
            size_hint_x: None
            width: dp(28)
            color: 0.3, 0.3, 0.3, 1
        Slider:
            id: qslider
            min: 0
            max: 100
            value: 50
            on_value: root.set_quality_value(self.value)
        Label:
            text: '100'
            size_hint_x: None
            width: dp(36)
            color: 0.3, 0.3, 0.3, 1

    Label:
        id: qlabel
        text: 'Quality: 50'
        size_hint_y: None
        height: dp(26)
        color: 0.25, 0.25, 0.25, 1
'''


class QualityRoot(BoxLayout):

    def set_quality_value(self, value):
        v = int(value)
        self.ids.qlabel.text = f'Quality: {v}'
        w = self.ids.lottie
        if w.loaded:
            w.set_quality(v)

    def _sync_quality(self, *args):
        self.set_quality_value(self.ids.qslider.value)


class QualityApp(App):

    json_source = SOURCE

    def build(self):
        return Builder.load_string(kv)


if __name__ == '__main__':
    QualityApp().run()
