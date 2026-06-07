'''
Video provider demo — cross-platform
=====================================

Visual / interactive test-bed for the new V3.0
:class:`kivy.core.video.VideoBase` API additions: thumbnails, and the
``buffering`` signal.

The demo exercises features that every Kivy video provider should
support once the new APIs land:

* **Thumbnails** — each clip card on the home grid displays a frame
  generated via :meth:`kivy.uix.video.Video.generate_thumbnail`.  If a
  thumbnail appears, the API works end-to-end.
* **Buffering overlay** — the player screen shows a "Loading…" /
  "Buffering…" overlay gated on the canonical rule::

      visible = not video.loaded or video.buffering

  This covers the initial pre-playback wait (``loaded`` is False) and
  any mid-stream rebuffer (``buffering`` flips True while ``loaded`` is
  already True).
* **Live state readout** — the right-hand panel surfaces ``loaded``,
  ``buffering``, ``state``, provider name, texture size, and the active
  source filename for at-a-glance debugging.

Clips are limited to H.264/MP4 so the same file runs on every platform
without provider-specific workarounds.  Remote clips are downloaded once
to :attr:`~kivy.app.App.user_cache_dir` and replayed from disk.

Run::

    python examples/widgets/video/video_demo.py

or from this directory::

    python video_demo.py
'''

import os

# Several CDNs that host the sample clips return 403 Forbidden for the
# default Python urllib User-Agent.  Send a generic Safari string so
# downloads work out of the box.
_HTTP_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) '
        'AppleWebKit/605.1.15 (KHTML, like Gecko) '
        'Version/17.0 Safari/605.1.15'),
}

from kivy.app import App
from kivy.core.video import Video as CoreVideo
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.network.urlrequest import UrlRequest
from kivy.properties import (BooleanProperty, ListProperty, NumericProperty,
                             ObjectProperty, StringProperty)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.uix.slider import Slider
from kivy.uix.video import Video


# --------------------------------------------------------------------- #
# Clip catalogue — four H.264/MP4 clips that work on all platforms
# --------------------------------------------------------------------- #

CLIPS = [
    {
        'title': 'Big Buck Bunny trailer, ~33s (H.264 + AAC)',
        'source': (
            'https://download.blender.org/peach/trailer/'
            'trailer_iphone.m4v'),
        'remote': True,
        'note': '~4 MB. Short clip with audio — good for a quick sanity check.',
    },
    {
        'title': 'Sintel trailer 480p, ~1 min (H.264 + AAC)',
        'source': (
            'https://download.blender.org/durian/trailer/'
            'sintel_trailer-480p.mp4'),
        'remote': True,
        'note': '~4 MB. Longer clip with audio — best for testing the seek bar.',
    },
    {
        'title': 'Big Buck Bunny 720p, 10s (H.264, silent)',
        'source': (
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/'
            'Big_Buck_Bunny_720_10s_5MB.mp4'),
        'remote': True,
        'note': '5 MB at 720p. Quick-to-download smoke-test clip.',
    },
    {
        'title': 'Jellyfish 1080p, 10s (H.264, silent)',
        'source': (
            'https://test-videos.co.uk/vids/jellyfish/mp4/h264/1080/'
            'Jellyfish_1080_10s_30MB.mp4'),
        'remote': True,
        'note': ('30 MB at 1080p. High-motion content — '
                 'good pixel-pipeline stress test.'),
    },
]


def _cache_path_for(url: str, cache_dir: str) -> str:
    '''Local file path for a cached download of *url* inside *cache_dir*.'''
    name = url.rsplit('/', 1)[-1] or 'download.bin'
    return os.path.join(cache_dir, name)


def _download_to_cache(url: str, cache_dir: str,
                       on_progress=None, on_done=None) -> None:
    '''Download *url* to *cache_dir* using :class:`~kivy.network.urlrequest.UrlRequest`.

    ``UrlRequest`` runs in its own thread and dispatches all callbacks on
    the main thread, so neither manual threading nor ``Clock.schedule_once``
    is required here.

    ``on_progress(frac: float | None)`` — fraction in ``[0, 1]`` when the
    server reports a ``Content-Length``, otherwise ``None``.

    ``on_done(local_path: str | None, error: Exception | None)``
    '''
    dest = _cache_path_for(url, cache_dir)
    tmp = dest + '.part'

    def _on_progress(req, current, total):
        if on_progress is not None:
            frac = (current / total) if total > 0 else None
            on_progress(frac)

    def _on_success(req, result):
        try:
            os.replace(tmp, dest)
        except OSError as e:
            if on_done is not None:
                on_done(None, e)
            return
        if on_done is not None:
            on_done(dest, None)

    def _on_failure(req, result):
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        if on_done is not None:
            on_done(None, Exception(f'HTTP {req.resp_status}'))

    def _on_error(req, error):
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        if on_done is not None:
            on_done(None, error)

    UrlRequest(
        url,
        req_headers=_HTTP_HEADERS,
        file_path=tmp,
        on_progress=_on_progress,
        on_success=_on_success,
        on_failure=_on_failure,
        on_error=_on_error,
    )


# --------------------------------------------------------------------- #
# KV layout
# --------------------------------------------------------------------- #

KV = '''
<ClipCard>:
    orientation: 'vertical'
    padding: dp(6)
    spacing: dp(4)
    canvas.before:
        Color:
            rgba: 0.13, 0.13, 0.15, 1
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.25, 0.25, 0.30, 1
        Line:
            rectangle: (self.x + 1, self.y + 1, self.width - 2, self.height - 2)
            width: 1

    ThumbnailButton:
        texture: root.thumb_texture
        fit_mode: 'contain'
        size_hint_y: 1
        on_release: app.open_player(root.clip_index)
        canvas.before:
            Color:
                rgba: 0, 0, 0, 1
            Rectangle:
                pos: self.pos
                size: self.size

    Label:
        text: root.title
        size_hint_y: None
        height: dp(22)
        bold: True
        font_size: '12sp'
        halign: 'left'
        valign: 'middle'
        text_size: self.size
        shorten: True
        color: 0.95, 0.95, 0.95, 1

    Label:
        text: root.status_text
        size_hint_y: None
        height: dp(16)
        font_size: '10sp'
        halign: 'left'
        valign: 'middle'
        text_size: self.size
        color: 0.55, 0.85, 1.00, 1

    Button:
        text: 'Open'
        size_hint_y: None
        height: dp(28)
        on_release: app.open_player(root.clip_index)


<GridScreen>:
    name: 'grid'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(8)

        BoxLayout:
            size_hint_y: None
            height: dp(36)
            spacing: dp(8)
            Label:
                text: 'Video provider demo'
                bold: True
                font_size: '15sp'
                halign: 'left'
                valign: 'middle'
                text_size: self.size
            Label:
                text: root.provider_label
                font_size: '12sp'
                halign: 'right'
                valign: 'middle'
                text_size: self.size
                color: 0.7, 0.9, 1, 1
                size_hint_x: None
                width: dp(240)

        Label:
            size_hint_y: None
            height: dp(20)
            font_size: '11sp'
            halign: 'left'
            valign: 'middle'
            text_size: self.size
            color: 0.7, 0.7, 0.7, 1
            text: 'Tap any card to open the player. Thumbnails load after download.'

        GridLayout:
            id: cards
            cols: 2
            rows: 2
            spacing: dp(6)


<StatusReadout@BoxLayout>:
    label: ''
    value: ''
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(20)
    Label:
        text: root.label
        size_hint_x: 0.5
        font_size: '11sp'
        halign: 'left'
        valign: 'middle'
        text_size: self.size
        color: 0.7, 0.7, 0.7, 1
    Label:
        text: root.value
        size_hint_x: 0.5
        font_size: '11sp'
        halign: 'right'
        valign: 'middle'
        text_size: self.size
        shorten: True
        shorten_from: 'left'
        bold: True
        color: 0.9, 0.95, 1, 1


<PlayerScreen>:
    name: 'player'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(6)

        # ---- title bar ----
        BoxLayout:
            size_hint_y: None
            height: dp(32)
            spacing: dp(8)
            Button:
                text: '< Back'
                size_hint_x: None
                width: dp(70)
                on_release: app.go_to_grid()
            Label:
                text: root.title
                bold: True
                font_size: '13sp'
                halign: 'left'
                valign: 'middle'
                text_size: self.size

        # ---- video area + status panel ----
        BoxLayout:
            size_hint_y: 1
            spacing: dp(8)

            # Video stage with loading/buffering overlay
            FloatLayout:
                size_hint_x: 0.72
                Video:
                    id: video
                    state: root.video_state
                    volume: 0.5
                    fit_mode: 'contain'
                    size_hint: 1, 1
                    pos_hint: {'x': 0, 'y': 0}
                    on_eos: root.video_state = 'stop'

                # Overlay: visible while loading or rebuffering.
                # Canonical gate: not video.loaded or video.buffering
                BoxLayout:
                    opacity: 1 if (not video.loaded or video.buffering) else 0
                    disabled: video.loaded and not video.buffering
                    size_hint: None, None
                    size: dp(210), dp(52)
                    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                    orientation: 'vertical'
                    padding: dp(8)
                    canvas.before:
                        Color:
                            rgba: 0, 0, 0, 0.75 if self.opacity else 0
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(8)]
                    Label:
                        text: 'Buffering...' if video.buffering else 'Loading...'
                        font_size: '14sp'
                        bold: True
                        color: 1, 1, 1, 1

            # Live-state readout panel
            BoxLayout:
                orientation: 'vertical'
                size_hint_x: 0.28
                spacing: dp(2)
                padding: dp(6)
                canvas.before:
                    Color:
                        rgba: 0.10, 0.10, 0.13, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size

                Label:
                    text: 'Live state'
                    size_hint_y: None
                    height: dp(22)
                    bold: True
                    font_size: '12sp'
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size
                    color: 0.95, 0.95, 0.95, 1

                StatusReadout:
                    label: 'provider'
                    value: app.provider_name
                StatusReadout:
                    label: 'state'
                    value: video.state
                StatusReadout:
                    label: 'loaded'
                    value: str(bool(video.loaded))
                StatusReadout:
                    label: 'buffering'
                    value: str(bool(video.buffering))
                StatusReadout:
                    label: 'texture size'
                    value: root.fmt_texture_size(video.texture)
                StatusReadout:
                    label: 'source'
                    value: root.source.rsplit('/', 1)[-1] if root.source else '-'

                Widget:

        # ---- transport controls ----
        BoxLayout:
            size_hint_y: None
            height: dp(36)
            spacing: dp(6)
            Button:
                text: 'Play' if root.video_state != 'play' else 'Pause'
                size_hint_x: None
                width: dp(80)
                on_release: root.toggle_play()
            Button:
                text: 'Stop'
                size_hint_x: None
                width: dp(60)
                on_release: root.stop_play()
            Button:
                text: 'Restart'
                size_hint_x: None
                width: dp(72)
                on_release: root.restart_clip()
            SeekSlider:
                id: seek
                min: 0
                max: max(video.duration, 0.0001)
                on_press: root.scrub_start()
                on_scrub: root.scrub_move(self.value)
                on_release: root.scrub_end(self.value)
            Label:
                text: root.fmt_time_range(video.position, video.duration)
                size_hint_x: None
                width: dp(110)
                font_size: '11sp'


ScreenManager:
    GridScreen:
    PlayerScreen:
'''


# --------------------------------------------------------------------- #
# Widget helpers
# --------------------------------------------------------------------- #


class ThumbnailButton(ButtonBehavior, Image):
    '''Thumbnail image that acts as a button.

    Mixes :class:`~kivy.uix.behaviors.ButtonBehavior` into
    :class:`~kivy.uix.image.Image` so the thumbnail on each clip card
    dispatches ``on_release`` when tapped, opening the player directly
    without requiring the separate "Open" button.
    '''


# --------------------------------------------------------------------- #
# Seek slider
# --------------------------------------------------------------------- #


class SeekSlider(Slider):
    '''Slider subclass that tracks whether the user is actively touching it.

    ``touched`` is set to ``True`` on ``on_touch_down`` (before Kivy's
    Slider processes the touch, so the KV binding is gated immediately)
    and cleared to ``False`` after ``on_release`` fires on
    ``on_touch_up``.  The ``on_press`` / ``on_release`` events mirror
    the Button convention and can be used in KV directly.

    Typical KV usage to prevent the video position from fighting the
    user's drag::

        SeekSlider:
            value: video.position if not self.touched else self.value
            on_release: app.seek_to(self.value)
    '''

    __events__ = ('on_press', 'on_scrub', 'on_release')

    touched = BooleanProperty(False)

    def on_press(self):
        pass

    def on_scrub(self):
        pass

    def on_release(self):
        pass

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touched = True
            self.dispatch('on_press')
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        result = super().on_touch_move(touch)
        if self.touched:
            self.dispatch('on_scrub')
        return result

    def on_touch_up(self, touch):
        if self.touched:
            self.dispatch('on_release')
            self.touched = False
        return super().on_touch_up(touch)


# --------------------------------------------------------------------- #
# Widget classes
# --------------------------------------------------------------------- #


class ClipCard(BoxLayout):
    '''Single clip cell in the 2x2 home grid.

    The visual layout is defined in KV; this class declares the
    properties KV binds to.
    '''

    title = StringProperty('')
    note = StringProperty('')
    status_text = StringProperty('Not downloaded')
    thumb_texture = ObjectProperty(None, allownone=True)
    clip_index = NumericProperty(0)


class GridScreen(Screen):
    provider_label = StringProperty('')
    clips = ListProperty()

    # ---- grid population ----

    def populate(self, *_):
        '''Create one :class:`ClipCard` per clip and kick off downloads /
        thumbnail generation.  Called once from ``App.on_start`` after
        the KV tree is ready.
        '''
        cards_box = self.ids.cards
        cards_box.clear_widgets()
        for i, clip in enumerate(self.clips):
            card = ClipCard()
            card.clip_index = i
            card.title = clip['title']
            cards_box.add_widget(card)
            clip['_card'] = card
            self._prepare_clip(i)

    def _prepare_clip(self, index: int):
        '''Download a remote clip if needed, then generate its thumbnail.'''
        clip = self.clips[index]
        card = clip['_card']

        if not clip.get('remote'):
            local = clip['source']
            if not os.path.exists(local):
                card.status_text = 'Local file not found'
                return
            clip['_local'] = local
            Clock.schedule_once(lambda *_: self._make_thumbnail(index), 0.05)
            return

        cache_dir = App.get_running_app().user_cache_dir
        local = _cache_path_for(clip['source'], cache_dir)
        if os.path.exists(local):
            clip['_local'] = local
            card.status_text = 'Cached — generating thumbnail…'
            Clock.schedule_once(lambda *_: self._make_thumbnail(index), 0.05)
            return

        card.status_text = 'Downloading…'

        def on_progress(frac):
            card.status_text = (
                'Downloading…' if frac is None
                else f'Downloading {int(frac * 100)}%')

        def on_done(local_path, error):
            if error is not None or local_path is None:
                card.status_text = f'Download failed: {error}'
                return
            clip['_local'] = local_path
            card.status_text = 'Cached — generating thumbnail…'
            self._make_thumbnail(index)

        _download_to_cache(clip['source'], cache_dir,
                           on_progress=on_progress, on_done=on_done)

    def _make_thumbnail(self, index: int):
        clip = self.clips[index]
        card = clip['_card']
        local = clip.get('_local')
        if not local:
            card.status_text = 'Not available'
            return
        try:
            texture = Video.generate_thumbnail(local, time=2, size=(320, 180))
        except Exception as e:
            Logger.warning(
                f'VideoDemo: generate_thumbnail failed for {local}: {e}')
            card.status_text = 'Thumbnail unavailable'
            return
        if texture is None:
            card.status_text = 'Thumbnail unavailable'
            return
        card.thumb_texture = texture
        card.status_text = 'Ready — tap "Open" to play'


class PlayerScreen(Screen):
    title = StringProperty('')
    source = StringProperty('')
    video_state = StringProperty('stop')

    _scrub_was_playing = False

    def on_kv_post(self, base_widget):
        # Drive the seek bar from Python so the binding is gated by
        # SeekSlider.touched without creating a circular KV dependency.
        self.ids.video.bind(position=self._sync_seek_position)

    def _sync_seek_position(self, video, pos):
        '''Update the seek bar only when the user is not actively dragging.'''
        if not self.ids.seek.touched:
            self.ids.seek.value = pos

    # ---- transport ----

    def toggle_play(self):
        self.video_state = 'pause' if self.video_state == 'play' else 'play'

    def stop_play(self):
        self.video_state = 'stop'

    def restart_clip(self):
        '''Seek to the beginning and resume playback.'''
        self.ids.video.seek(0.0, precise=True)
        self.video_state = 'play'

    def seek_to(self, seconds: float):
        video = self.ids.video
        if video.duration > 0:
            video.seek(seconds / video.duration, precise=True)

    def scrub_start(self):
        '''Pause on scrub start so ``video.position`` stops advancing
        during the drag.
        '''
        self._scrub_was_playing = (self.video_state == 'play')
        self.video_state = 'pause'

    def scrub_move(self, seconds: float):
        '''Fast keyframe-aligned seek while dragging.

        Uses ``precise=False`` for low latency; ``scrub_end`` follows
        with ``precise=True`` to land on the exact chosen frame.
        '''
        video = self.ids.video
        if video.duration > 0:
            video.seek(seconds / video.duration, precise=False)

    def scrub_end(self, seconds: float):
        '''Precise seek on release, then restore play state.'''
        video = self.ids.video
        if video.duration > 0:
            video.seek(seconds / video.duration, precise=True)
        if self._scrub_was_playing:
            self.video_state = 'play'

    @staticmethod
    def fmt_time(seconds: float) -> str:
        if seconds is None or seconds <= 0:
            return '00:00'
        m, s = divmod(int(seconds), 60)
        return f'{m:02d}:{s:02d}'

    def fmt_time_range(self, pos: float, dur: float) -> str:
        return f'{self.fmt_time(pos)} / {self.fmt_time(dur)}'

    @staticmethod
    def fmt_texture_size(texture) -> str:
        if texture is None:
            return '-'
        return f'{texture.size[0]}x{texture.size[1]}'


# --------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------- #


class VideoDemoApp(App):
    title = 'Video provider demo'
    provider_name = StringProperty('?')

    def build(self):
        Window.size = (1280, 720)
        self.provider_name = (
            CoreVideo.__name__ if CoreVideo is not None else 'none')
        Logger.info(f'VideoDemo: core video provider is {self.provider_name}')
        self.sm = Builder.load_string(KV)
        grid = self.sm.get_screen('grid')
        grid.provider_label = f'provider: {self.provider_name}'
        grid.clips = [dict(c) for c in CLIPS]
        return self.sm

    def on_start(self):
        Clock.schedule_once(self.sm.get_screen('grid').populate, 0)

    # ---- navigation ----

    def open_player(self, index: int):
        clip = self.sm.get_screen('grid').clips[index]
        local = clip.get('_local')
        if not local:
            Logger.info(f'VideoDemo: clip {index} not yet available')
            return
        player = self.sm.get_screen('player')
        player.title = clip['title']
        player.source = local
        # Clear then re-assign to guarantee a fresh load.
        video = player.ids.video
        video.source = ''
        video.source = local
        player.video_state = 'play'
        self.sm.current = 'player'

    def go_to_grid(self):
        player = self.sm.get_screen('player')
        player.video_state = 'stop'
        player.ids.video.unload()
        self.sm.current = 'grid'

if __name__ == '__main__':
    VideoDemoApp().run()
