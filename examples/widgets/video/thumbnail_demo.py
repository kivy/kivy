'''
Video thumbnail + playback — minimal example
==============================================

Downloads a small (~1 MB) sample clip, generates a thumbnail via
:meth:`kivy.uix.video.Video.generate_thumbnail`, and plays the clip on
tap. Deliberately small — see ``video_demo.py`` in this same directory
for a fuller exercise of the V3.0 video APIs (buffering overlay, seek
bar, multiple clips).

Run::

    python examples/widgets/video/thumbnail_demo.py
'''
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.network.urlrequest import UrlRequest
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.video import Video

# Big Buck Bunny (CC-licensed open movie, https://peach.blender.org/),
# re-encoded as a small 10s/1MB H.264 sample by test-videos.co.uk.
CLIP_URL = (
    'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/'
    'Big_Buck_Bunny_360_10s_1MB.mp4')

# Some CDNs return 403 Forbidden for the default Python urllib
# User-Agent; a generic browser string works around that.
_HTTP_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) '
        'AppleWebKit/605.1.15 (KHTML, like Gecko) '
        'Version/17.0 Safari/605.1.15'),
}

KV = '''
<Root>:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: 0.10, 0.10, 0.13, 1
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: root.status
        size_hint_y: None
        height: dp(36)
        font_size: '16sp'
        bold: True
        color: 1, 1, 1, 1

    FloatLayout:
        # Visible until the thumbnail (or video) actually has pixels to
        # show, so the window never just looks like an unlit black box
        # while the clip downloads / the thumbnail is generated.
        Label:
            text: 'Preparing clip...'
            opacity: 0 if (root.thumb_texture or root.playing) else 1
            font_size: '20sp'
            color: 0.75, 0.75, 0.80, 1

        # Swap thumbnail -> video only once the first frame has arrived
        # (video.loaded); before that, Video has no texture and would
        # draw a plain white rectangle.
        Image:
            texture: root.thumb_texture
            opacity: 0 if (root.playing and video.loaded) else 1
            fit_mode: 'contain'
            size_hint: 1, 1

        Video:
            id: video
            opacity: 1 if (root.playing and video.loaded) else 0
            state: root.video_state
            fit_mode: 'contain'
            size_hint: 1, 1
            on_eos: root.video_state = 'stop'

    Button:
        text: 'Stop' if root.playing else 'Play'
        size_hint_y: None
        height: dp(44)
        disabled: not root.ready
        on_release: root.toggle_play()
'''


def _cache_path_for(url, cache_dir):
    name = url.rsplit('/', 1)[-1] or 'download.bin'
    return os.path.join(cache_dir, name)


class Root(BoxLayout):
    status = StringProperty('Downloading sample clip...')
    thumb_texture = ObjectProperty(None, allownone=True)
    ready = BooleanProperty(False)
    playing = BooleanProperty(False)
    video_state = StringProperty('stop')
    local_path = StringProperty('')

    def toggle_play(self):
        if self.playing:
            self.video_state = 'stop'
            self.playing = False
            self.status = 'Ready -- tap Play'
        else:
            if not self.ids.video.source:
                self.ids.video.source = self.local_path
            self.playing = True
            self.video_state = 'play'
            self.status = 'Playing'

    def make_thumbnail(self):
        # generate_thumbnail() is synchronous and blocks the UI thread
        # briefly. Deferring the call by one Clock tick lets Kivy paint
        # the status text first.
        self.status = 'Generating thumbnail...'
        Clock.schedule_once(self._generate_thumbnail_now, 0)

    def _generate_thumbnail_now(self, dt):
        texture = Video.generate_thumbnail(
            self.local_path, time=2, size=(480, 270))
        if texture is None:
            self.status = 'Thumbnail unavailable (see log for details)'
            Logger.warning(
                'ThumbnailDemo: generate_thumbnail returned None')
        else:
            self.thumb_texture = texture
            self.status = 'Ready -- tap Play'
        self.ready = True


class ThumbnailDemoApp(App):
    title = 'Video thumbnail demo'

    def build(self):
        # Must touch Window explicitly here, before returning root: in
        # this build, App._run_prepare() checks EventLoop.window right
        # after build() returns, and the real window/GL context isn't
        # guaranteed to exist yet unless something already forced it
        # (confirmed empirically -- a build() that never references
        # Window hits "No window is created. Terminating application
        # run." and on_start never fires, even though the window *does*
        # get created a moment later as part of the main loop startup).
        Window.size = (900, 600)
        # KV defines <Root>: as a rule, not an instantiation -- it must
        # be constructed explicitly in Python; Builder.load_string(KV)
        # alone would return None here.
        Builder.load_string(KV)
        self.root_widget = Root()
        return self.root_widget

    def on_start(self):
        Clock.schedule_once(self._start_download, 0)

    def _start_download(self, *_):
        cache_dir = self.user_cache_dir
        local = _cache_path_for(CLIP_URL, cache_dir)
        if os.path.exists(local):
            self.root_widget.local_path = local
            self.root_widget.make_thumbnail()
            return

        tmp = local + '.part'

        def on_progress(req, current, total):
            frac = f'{int(current / total * 100)}%' if total > 0 else '...'
            self.root_widget.status = f'Downloading sample clip... {frac}'

        def on_success(req, result):
            os.replace(tmp, local)
            self.root_widget.local_path = local
            self.root_widget.make_thumbnail()

        def on_failure(req, result):
            self.root_widget.status = f'Download failed: HTTP {req.resp_status}'
            Logger.warning(f'ThumbnailDemo: download failed: {result}')

        def on_error(req, error):
            self.root_widget.status = f'Download failed: {error}'
            Logger.warning(f'ThumbnailDemo: download error: {error}')

        UrlRequest(
            CLIP_URL,
            req_headers=_HTTP_HEADERS,
            file_path=tmp,
            on_progress=on_progress,
            on_success=on_success,
            on_failure=on_failure,
            on_error=on_error,
        )


if __name__ == '__main__':
    ThumbnailDemoApp().run()
