'''
Async-style status (loading → success or error markers)
======================================================

Uses named **markers** in the Lottie file: ``loading`` (loop), ``success``,
and ``error`` (one-shot, then hold on the last frame with ``eos`` ``pause``).

The Lottie file (lottie_async_status.json) contains a dual arc loader plus
vector overlays: green **check mark** for **success**, red crossed bars for **error**.
Markers: ``loading`` (frames ``0 … 78``), ``success``, ``error``.

Requires a Lottie provider.  The default ThorVG backend ships with
Kivy's official desktop wheels and needs no extra install.

Run from ``examples/widgets/lottie/``::

    python lottie_async_status.py

Or from the Kivy source tree root::

    python examples/widgets/lottie/lottie_async_status.py
'''

from pathlib import Path

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

DIR = Path(__file__).resolve().parent
SOURCE = str(DIR / 'lottie_async_status.json')

kv = '''
<AsyncRoot>:
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
        text: 'Simulated task: Start loads a looping spinner; then pick the outcome.'
        size_hint_y: None
        height: self.texture_size[1] + dp(8)
        color: 0.15, 0.15, 0.15, 1

    LottieWidget:
        id: lottie
        source: app.json_source
        fit_mode: 'contain'
        eos: 'loop'
        on_load: root.start_loading()

    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(6)
        Button:
            id: btn_start
            text: 'Start / Reset'
            on_release: root.start_loading()
        Button:
            id: btn_finish_ok
            text: 'Finish OK'
            on_release: root.finish_ok()
        Button:
            id: btn_finish_err
            text: 'Finish error'
            on_release: root.finish_err()

AsyncRoot:
'''


class AsyncRoot(BoxLayout):

    def start_loading(self):
        w = self.ids.lottie
        if not w.loaded:
            return
        w.eos = 'loop'
        # If already ``play``, :meth:`LottieBase.play` is a no-op; stop first so
        # ``play_marker`` + ``play`` actually restart the loading segment.
        w.state = 'stop'
        w.play_marker('loading')
        w.state = 'play'
        self._set_finish_enabled(True)

    def _set_finish_enabled(self, enabled):
        self.ids.btn_finish_ok.disabled = not enabled
        self.ids.btn_finish_err.disabled = not enabled

    def finish_ok(self):
        w = self.ids.lottie
        if not w.loaded:
            return
        w.eos = 'pause'
        w.play_marker('success')
        w.state = 'play'
        self._set_finish_enabled(False)

    def finish_err(self):
        w = self.ids.lottie
        if not w.loaded:
            return
        w.eos = 'pause'
        w.play_marker('error')
        w.state = 'play'
        self._set_finish_enabled(False)


class AsyncStatusApp(App):

    json_source = SOURCE

    def build(self):
        return Builder.load_string(kv)


if __name__ == '__main__':
    AsyncStatusApp().run()
