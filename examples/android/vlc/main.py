import kivy
from select import select
kivy.require('1.9.0')
from kivy.app import App
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.slider import Slider
from kivy.logger import Logger

from vlcvideoview import VlcVideoView
VlcVideoView.VlcLibOptions.append('-vvv')
# VlcVideoView.VlcLibOptions.append('--network-caching=100')

from mediastore import query_storage_video


DEFAULT_PLAYLIST = [
    'rtsp://184.72.239.149/vod/mp4:BigBuckBunny_115k.mov',
]


class VlcExampleVideoProgress(ProgressBar):
    seek = NumericProperty(-1)
    seekable = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(VlcExampleVideoProgress, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if not self.seekable:
            return
        if self.collide_point(*touch.pos):
            return
        touch.grab(self)
        self._update_seek(touch.x)
        return True

    def on_touch_move(self, touch):
        if not self.seekable:
            return
        if touch.grab_current is not self:
            return
        self._update_seek(touch.x)
        return True

    def on_touch_up(self, touch):
        if not self.seekable:
            return
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        self.seek = -1
        return True

    def _update_seek(self, x):
        if not self.seekable:
            return
        if self.width == 0:
            return
        x = max(self.x, min(self.right, x)) - self.x
        self.seek = x / float(self.width)


class VlcExampleApp(App):
    source = StringProperty(DEFAULT_PLAYLIST[0])

    def build(self):
        Logger.info('VlcExampleApp: building...')
        self._playlist_idx = 0
        self._playlist_cache = None

        box = FloatLayout()

        self._progress = VlcExampleVideoProgress(
            pos_hint={'x': 0.0, 'top': 0.9},
            size_hint=(1.0, None),
        )
        self._progress.bind(seek=self.on_progress_seek)
        box.add_widget(self._progress)

        self._video = VlcVideoView(
            source=self.source,
            pos_hint={'x': 0.0, 'y': 0.0},
            size_hint=(1.0, 0.9),
            options={'hw-decoder': 'enable', 'network-caching': 200},
        )
        self._video.bind(
            duration=self._progress.setter('max'),
            position=self._progress.setter('value'),
            state=self.on_video_state,
            loaded=self.on_video_loaded,
            eos=self.on_video_eos,
            seekable=self.on_video_seekable,
        )
        box.add_widget(self._video)

        self._btn_play = Button(
            text='>',
            pos_hint={'x': 0.0, 'top': 1.0},
            size_hint=(0.1, 0.1)
        )
        self._btn_play.bind(on_press=self.on_btn_play_press)
        box.add_widget(self._btn_play)

        self._edt = TextInput(
            text=self.source,
            pos_hint={'x': 0.1, 'top': 1.0},
            size_hint=(0.8, 0.1)
        )
        self._edt.bind(text=self.setter('source'))
        box.add_widget(self._edt)

        self._btn_next = Button(
            text='>>',
            pos_hint={'x': 0.9, 'top': 1.0},
            size_hint=(0.1, 0.1)
        )
        self._btn_next.bind(on_press=self.on_btn_next_press)
        box.add_widget(self._btn_next)

        return box

    def _show_progress(self, seekable):
        Logger.info('VlcExampleApp: showing progress {}'.format(seekable))
        self._progress.opacity = 0.5

    def _hide_progress(self):
        self._progress.opacity = 0.0

    def on_source(self, instance, value):
        Logger.info('VlcExampleApp: on_source: {}'.format(value))
        self._video.source = value
        self._video.state = 'stop'

    def on_btn_play_press(self, instance):
        Logger.info('VlcExampleApp: on_btn_play_press')
        if self._video.state == 'play':
            self._video.state = 'pause'
        else:
            self._video.state = 'play'

    def on_btn_next_press(self, instance):
        Logger.info('VlcExampleApp: on_btn_next_press')
        self._playlist_idx = self._playlist_idx + 1
        if self._playlist_cache is not None:
            playlist = self._playlist_cache
        elif self._playlist_idx < len(DEFAULT_PLAYLIST):
            playlist = DEFAULT_PLAYLIST
        else:
            playlist = DEFAULT_PLAYLIST + query_storage_video()
            self._playlist_cache = playlist
        self._playlist_idx = self._playlist_idx % len(playlist)
        self._edt.text = playlist[self._playlist_idx]

    def on_video_loaded(self, instance, value):
        Logger.info('VlcExampleApp: on_video_loaded {}'.format(value))
        if value and self._video.duration > 0:
            self._video.state = 'play'
            self._show_progress(True)
        else:
            self._hide_progress()

    def on_video_state(self, instance, value):
        Logger.info('VlcExampleApp: on_video_state {}'.format(value))
        self._btn_play.text = {
            'play':  '||', 'pause': '|>', 'stop':  '>'}[value]
        for w in (self._btn_next, self._edt):
            w.disabled = (value == 'play')

    def on_video_eos(self, instance, value):
        Logger.info('VlcExampleApp: on_video_eos {}'.format(value))
        if value:
            self._video.state = 'stop'

    def on_video_seekable(self, instance, value):
        self._progress.seekable = value

    def on_progress_seek(self, instance, value):
        Logger.info('VlcExampleApp: on_progress_seek {}'.format(value))
        if value >= 0.0:
            self._video.seek(value)


def run():
    a = VlcExampleApp()
    a.run()

if __name__ == '__main__':
    run()
