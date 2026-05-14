'''
AVFoundation video provider — manual demo
=========================================

Visual / interactive test bed for the macOS / iOS AVFoundation video
provider added in Kivy 3.0.0 and for the new
:class:`kivy.core.video.VideoBase` API surface (thumbnails, buffering
signal, provider-specific options).

What this demo lets you eyeball:

* **Thumbnails** — every clip card on the grid screen renders a frame
  generated via :meth:`kivy.uix.video.Video.generate_thumbnail` (calls
  ``AVAssetImageGenerator`` under the hood). If a thumbnail appears,
  the API works.
* **Buffering signal** — a "Loading..." overlay on the player screen
  is gated on ``not video.loaded or video.buffering`` (the canonical
  rule that covers both the initial pre-playback wait and any
  mid-stream rebuffer). The right-hand status panel surfaces the
  ``loaded`` / ``buffering`` booleans directly.
* **Provider options dict** — toggles map to keys on the
  ``options={...}`` dict forwarded to the AVFoundation provider:

  - ``force_cpu_copy`` bypasses the zero-copy
    (IOSurface → ANGLE pbuffer → GL_TEXTURE_2D) path and uses the CPU
    memcpy fallback, for A/B comparison on the same clip.
  - ``automatically_waits_to_minimize_stalling`` forwards to the
    ``AVPlayer`` property of the same name (when off, AVPlayer starts
    playback as soon as the first decodable frame is available rather
    than buffering ahead).

Run from the Kivy source tree root::

    python examples/widgets/video/avfoundation_demo.py

Or from this directory::

    python avfoundation_demo.py

Requires a Mac. On other platforms ``avfoundation`` is not built and
``CoreVideo`` will silently fall through to a different provider (the
demo still runs but exercises whatever provider was selected, which may
not honor the new APIs).
'''

from __future__ import annotations

import os
import threading
from urllib.error import URLError
from urllib.request import Request, urlopen

# Several of the CDNs that host the sample clips
# (``test-videos.co.uk``, ``download.blender.org``) return ``403
# Forbidden`` for the default Python ``urllib`` ``User-Agent``
# (``Python-urllib/3.x``) but accept any normal browser UA. Send a
# generic desktop Safari string so the downloads work out of the box.
_HTTP_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) '
        'AppleWebKit/605.1.15 (KHTML, like Gecko) '
        'Version/17.0 Safari/605.1.15'),
}

from kivy.app import App
from kivy.clock import Clock
from kivy.core.video import Video as CoreVideo
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import (BooleanProperty, ListProperty, NumericProperty,
                             ObjectProperty, StringProperty)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.video import Video


# --------------------------------------------------------------------- #
# Clips catalogue.
#
# Two kinds of entries are supported:
#
# * Progressive H.264/MP4 downloads from ``test-videos.co.uk`` (Blender
#   Open Movies re-encoded into fixed-size 10-second clips) and from
#   ``download.blender.org``. These are fetched to
#   ``~/.kivy/video_demo_cache/`` once and replayed from disk.
# * HLS streams from Apple's public BipBop test set
#   (``devstreaming-cdn.apple.com``). These are passed through to
#   ``AVPlayer`` as-is — no local cache, AVFoundation manages the
#   manifest + segments itself.
# --------------------------------------------------------------------- #

CACHE_DIR = os.path.expanduser('~/.kivy/video_demo_cache')

CLIPS = [
    {
        'title': 'Big Buck Bunny trailer, ~33s (H.264 / M4V + AAC)',
        'source': (
            'https://download.blender.org/peach/trailer/'
            'trailer_iphone.m4v'),
        'remote': True,
        'note': (
            "~4 MB. Short audio-bearing clip from the Blender "
            "Foundation Peach project."),
    },
    {
        'title': 'Sintel trailer 480p, ~1 min (H.264 / MP4 + AAC)',
        'source': (
            'https://download.blender.org/durian/trailer/'
            'sintel_trailer-480p.mp4'),
        'remote': True,
        'note': (
            "~4 MB. Longer-form clip with AAC audio — best for "
            "exercising the seek bar and the volume control."),
    },
    {
        'title': 'Big Buck Bunny 720p, 10s (H.264 / MP4, silent)',
        'source': (
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/'
            'Big_Buck_Bunny_720_10s_5MB.mp4'),
        'remote': True,
        'note': (
            "5 MB smoke clip. Downloads in seconds; useful for a "
            "quick first-frame sanity check. test-videos.co.uk "
            "standard clips ship without audio."),
    },
    {
        'title': 'Big Buck Bunny 1080p, 10s (H.264 / MP4, silent)',
        'source': (
            'https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/1080/'
            'Big_Buck_Bunny_1080_10s_5MB.mp4'),
        'remote': True,
        'note': (
            "5 MB at 1080p. Quick-to-download stress test for the "
            "pixel pipeline: 1920x1080x4 bytes per frame x ~30 fps is "
            "~240 MB/s of memcpy on the force_cpu_copy path."),
    },
    {
        'title': 'Sintel 1080p, 10s (H.264 / MP4, silent)',
        'source': (
            'https://test-videos.co.uk/vids/sintel/mp4/h264/1080/'
            'Sintel_1080_10s_30MB.mp4'),
        'remote': True,
        'note': (
            "30 MB at 1080p. test-videos.co.uk standard clips "
            "ship without audio."),
    },
    {
        'title': 'Jellyfish 1080p, 10s (H.264 / MP4, silent)',
        'source': (
            'https://test-videos.co.uk/vids/jellyfish/mp4/h264/1080/'
            'Jellyfish_1080_10s_30MB.mp4'),
        'remote': True,
        'note': (
            "30 MB at 1080p, high-motion content. Marquee zero-copy "
            "vs force_cpu_copy comparison clip: load it, toggle "
            "force_cpu_copy, hit Apply (reload), and watch the log "
            "for 'zero-copy active' vs 'using CPU-copy path'. The "
            "memcpy stress (~240 MB/s) is also visible in Activity "
            "Monitor's Energy column."),
    },
    {
        'title': 'BipBop 16x9 (HLS / TS, with audio)',
        'source': (
            'https://devstreaming-cdn.apple.com/videos/streaming/'
            'examples/bipbop_16x9/bipbop_16x9_variant.m3u8'),
        'remote': True,
        'streaming': True,
        'note': (
            "Apple BipBop reference HLS stream, TS segments, with "
            "the classic 'bip/bop' audio jingle. AVPlayer handles "
            "the manifest natively."),
    },
    {
        'title': 'BipBop advanced (HLS / fMP4, with audio)',
        'source': (
            'https://devstreaming-cdn.apple.com/videos/streaming/'
            'examples/img_bipbop_adv_example_fmp4/master.m3u8'),
        'remote': True,
        'streaming': True,
        'note': (
            "Apple's advanced BipBop reference HLS stream, fMP4 "
            "segments, with audio."),
    },
]


def _cache_path_for(url: str) -> str:
    '''Local file path for a cached download of ``url``.'''
    name = url.rsplit('/', 1)[-1] or 'download.bin'
    return os.path.join(CACHE_DIR, name)


def _download_to_cache(url: str, on_progress=None, on_done=None) -> None:
    '''Background-thread helper. Streams ``url`` to ``CACHE_DIR`` with
    optional progress callbacks. Both callbacks are invoked via
    ``Clock.schedule_once`` so the UI sees them on the main thread.

    ``on_progress(progress: float | None)`` — ``progress`` is the
    fraction in ``[0, 1]`` when the server reports a Content-Length,
    otherwise ``None`` (indeterminate).

    ``on_done(local_path: str | None, error: Exception | None)`` —
    invoked once when the download has finished or failed. ``error`` is
    ``None`` on success.
    '''

    def _run():
        os.makedirs(CACHE_DIR, exist_ok=True)
        dest = _cache_path_for(url)
        tmp = dest + '.part'
        try:
            req = Request(url, headers=_HTTP_HEADERS)
            with urlopen(req, timeout=30) as resp:
                total = resp.headers.get('Content-Length')
                total = int(total) if total else None
                seen = 0
                with open(tmp, 'wb') as out:
                    while True:
                        chunk = resp.read(1 << 16)
                        if not chunk:
                            break
                        out.write(chunk)
                        seen += len(chunk)
                        if on_progress is not None:
                            frac = (seen / total) if total else None
                            Clock.schedule_once(
                                lambda dt, f=frac: on_progress(f), 0)
            os.replace(tmp, dest)
            if on_done is not None:
                Clock.schedule_once(
                    lambda dt: on_done(dest, None), 0)
        except (URLError, OSError) as e:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            if on_done is not None:
                Clock.schedule_once(
                    lambda dt, err=e: on_done(None, err), 0)

    threading.Thread(target=_run, daemon=True).start()


# --------------------------------------------------------------------- #
# KV layout
# --------------------------------------------------------------------- #

KV = '''
<ClipCard>:
    on_release: app.open_player(self.clip_index)
    orientation: 'vertical'
    size_hint_y: None
    height: dp(220)
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

    BoxLayout:
        size_hint_y: 0.75
        Image:
            texture: root.thumb_texture
            fit_mode: 'contain'
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
        font_size: '13sp'
        halign: 'left'
        valign: 'middle'
        text_size: self.size
        shorten: True
        color: 0.95, 0.95, 0.95, 1
    Label:
        text: root.status_text
        size_hint_y: None
        height: dp(18)
        font_size: '11sp'
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
                text: 'AVFoundation provider demo'
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
                width: dp(220)

        Label:
            size_hint_y: None
            height: dp(22)
            font_size: '11sp'
            halign: 'left'
            valign: 'middle'
            text_size: self.size
            color: 0.7, 0.7, 0.7, 1
            text: 'Click any card to open the player. Thumbnails are generated synchronously via Video.generate_thumbnail() once each clip is local. Remote clips download to ~/.kivy/video_demo_cache/ first.'

        ScrollView:
            do_scroll_x: False
            do_scroll_y: True
            BoxLayout:
                id: cards
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(6)


<StatusReadout@BoxLayout>:
    label: ''
    value: ''
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(20)
    Label:
        text: root.label
        size_hint_x: 0.55
        font_size: '11sp'
        halign: 'left'
        valign: 'middle'
        text_size: self.size
        color: 0.7, 0.7, 0.7, 1
    Label:
        text: root.value
        size_hint_x: 0.45
        font_size: '11sp'
        halign: 'right'
        valign: 'middle'
        text_size: self.size
        bold: True
        color: 0.9, 0.95, 1, 1


<PlayerScreen>:
    name: 'player'
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(6)

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

        # --- video stage with loading overlay ---
        # The overlay uses the canonical single-rule gate recommended in
        # the kivy.uix.video docs:
        #
        #     visible = not video.loaded or video.buffering
        #
        # This covers both the initial pre-playback wait (``loaded`` is
        # still False) and any mid-stream rebuffer (``buffering`` flips
        # True while ``loaded`` is already True). Both signals are
        # driven by the AVFoundation provider:
        # ``loaded`` from the first ``on_load`` (frame texture
        # available), and ``buffering`` from
        # AVPlayer.timeControlStatus == .waitingToPlayAtSpecifiedRate.
        FloatLayout:
            size_hint_y: 1
            Video:
                id: video
                state: root.video_state
                volume: 0.5
                fit_mode: 'contain'
                size_hint: 1, 1
                pos_hint: {'x': 0, 'y': 0}

            BoxLayout:
                opacity: 1 if (not video.loaded or video.buffering) else 0
                disabled: video.loaded and not video.buffering
                size_hint: None, None
                size: dp(220), dp(56)
                pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                orientation: 'vertical'
                padding: dp(8)
                spacing: dp(4)
                canvas.before:
                    Color:
                        rgba: 0, 0, 0, 0.75 if self.opacity else 0
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8)]
                Label:
                    text: ('Buffering...' if video.buffering else 'Loading...') if not video.loaded else 'Buffering...'
                    font_size: '14sp'
                    bold: True
                    color: 1, 1, 1, 1

        BoxLayout:
            size_hint_y: None
            height: dp(36)
            spacing: dp(6)
            Button:
                text: 'Play' if root.video_state != 'play' else 'Pause'
                size_hint_x: None
                width: dp(80)
                on_release: app.toggle_play()
            Button:
                text: 'Stop'
                size_hint_x: None
                width: dp(60)
                on_release: app.stop_play()
            Slider:
                id: seek
                min: 0
                max: max(video.duration, 0.0001)
                value: video.position
                # NOTE: for a robust seek bar you'd add a user-is-dragging
                # flag and disable the value <- position binding while
                # held. This demo keeps it minimal -- pause before
                # scrubbing to avoid the cursor fighting playback.
                on_touch_up: app.seek_to(self.value) if self.collide_point(*args[1].pos) else None
            Label:
                text: f'{root.fmt_time(video.position)} / {root.fmt_time(video.duration)}'
                size_hint_x: None
                width: dp(110)
                font_size: '11sp'

        BoxLayout:
            size_hint_y: None
            height: dp(220)
            spacing: dp(10)

            BoxLayout:
                orientation: 'vertical'
                spacing: dp(4)
                size_hint_x: 0.55

                ToggleButton:
                    size_hint_y: None
                    height: dp(28)
                    font_size: '11sp'
                    text: f"automatically_waits_to_minimize_stalling = {root.auto_wait_to_minimize_stalling}"
                    state: 'down' if root.auto_wait_to_minimize_stalling else 'normal'
                    on_release: root.auto_wait_to_minimize_stalling = not root.auto_wait_to_minimize_stalling

                ToggleButton:
                    size_hint_y: None
                    height: dp(28)
                    font_size: '11sp'
                    text: f"force_cpu_copy = {root.force_cpu_copy}  (zero-copy is the default)"
                    state: 'down' if root.force_cpu_copy else 'normal'
                    on_release: root.force_cpu_copy = not root.force_cpu_copy

                BoxLayout:
                    size_hint_y: None
                    height: dp(32)
                    spacing: dp(6)
                    Button:
                        text: 'Apply (reload)'
                        on_release: app.apply_and_reload()
                    Button:
                        text: 'Restart clip'
                        on_release: app.restart_clip()

                Label:
                    text: 'options are construction-time hints; changing them only takes effect on the next "Apply (reload)".'
                    font_size: '10sp'
                    color: 0.55, 0.7, 0.55, 1
                    halign: 'left'
                    valign: 'top'
                    text_size: self.size

            BoxLayout:
                orientation: 'vertical'
                spacing: dp(2)
                size_hint_x: 0.45
                padding: dp(4)
                canvas.before:
                    Color:
                        rgba: 0.10, 0.10, 0.13, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size

                Label:
                    text: 'Live state'
                    size_hint_y: None
                    height: dp(20)
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
                    label: 'pixel path'
                    value: 'CPU copy (forced)' if root.force_cpu_copy else 'zero-copy if available'
                StatusReadout:
                    label: 'texture size'
                    value: f'{video.texture.size[0]} x {video.texture.size[1]}' if video.texture else '-'
                StatusReadout:
                    label: 'source'
                    value: root.source.rsplit('/', 1)[-1] if root.source else '-'


ScreenManager:
    GridScreen:
    PlayerScreen:
'''


# --------------------------------------------------------------------- #
# Screens
# --------------------------------------------------------------------- #


class ClipCard(BoxLayout):
    '''Single clip row on the grid. Visual layout lives in KV; this
    shim declares the properties KV binds to and surfaces an
    ``on_release`` event so ``on_release:`` can be used in KV like a
    Button.
    '''
    __events__ = ('on_release',)

    title = StringProperty('')
    note = StringProperty('')
    status_text = StringProperty('No thumbnail yet')
    thumb_texture = ObjectProperty(None, allownone=True)
    clip_index = NumericProperty(0)

    def on_release(self, *_):
        pass

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and not touch.is_mouse_scrolling:
            # Only treat clicks on the card area itself; the inner
            # "Open" Button has its own on_release.
            self.dispatch('on_release')
            return True
        return super().on_touch_up(touch)


class GridScreen(Screen):
    provider_label = StringProperty('')


class PlayerScreen(Screen):
    title = StringProperty('')
    source = StringProperty('')
    video_state = StringProperty('stop')

    # Hint controls. These are read by the App on "Apply (reload)" to
    # rebuild the underlying Video widget with new construction kwargs.
    # ``auto_wait_to_minimize_stalling`` defaults to True to match
    # AVPlayer's own default (the YES side of automaticallyWaits...).
    auto_wait_to_minimize_stalling = BooleanProperty(True)
    force_cpu_copy = BooleanProperty(False)

    @staticmethod
    def fmt_time(seconds: float) -> str:
        if seconds is None or seconds <= 0:
            return '00:00'
        m, s = divmod(int(seconds), 60)
        return f'{m:02d}:{s:02d}'


# --------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------- #


class AVFoundationDemoApp(App):
    title = 'AVFoundation demo'
    provider_name = StringProperty('?')
    clips = ListProperty()

    def build(self):
        Window.size = (2000, 1400)
        self.provider_name = (
            CoreVideo.__name__ if CoreVideo is not None else 'none')
        Logger.info(
            f'AVFDemo: core video provider is {self.provider_name}')
        self.clips = [dict(c) for c in CLIPS]
        self.sm = Builder.load_string(KV)
        grid = self.sm.get_screen('grid')
        grid.provider_label = f'provider: {self.provider_name}'
        return self.sm

    def on_start(self):
        Clock.schedule_once(self._populate_grid, 0)

    # ---- grid ----

    def _populate_grid(self, *_):
        grid = self.sm.get_screen('grid')
        cards_box = grid.ids.cards
        cards_box.clear_widgets()
        for i, clip in enumerate(self.clips):
            card = ClipCard()
            card.clip_index = i
            card.title = clip['title']
            card.note = clip['note']
            cards_box.add_widget(card)
            clip['_card'] = card
            self._prepare_clip(i)

    def _prepare_clip(self, index: int):
        '''Prepare a clip for playback / thumbnailing.

        Three shapes:

        * ``streaming: True`` — pass the URL straight to AVFoundation,
          no download (HLS playlists aren't single files). Thumbnail
          generation is skipped: ``AVAssetImageGenerator`` is not
          reliable for HLS and the round-trip to discover that would
          just add latency to the grid render.
        * ``remote: True`` — fetch to ``~/.kivy/video_demo_cache/`` on
          a background thread, thumbnail from the cached file.
        * neither — local file bundled with Kivy.
        '''
        clip = self.clips[index]
        card = clip['_card']

        if clip.get('streaming'):
            clip['_local'] = clip['source']
            card.status_text = (
                'HLS stream - open the player to start streaming. '
                'Thumbnails are not generated for HLS sources.')
            return

        if not clip['remote']:
            local = clip['source']
            if not os.path.exists(local):
                card.status_text = 'Local file not found'
                return
            clip['_local'] = local
            Clock.schedule_once(
                lambda *_a: self._make_thumbnail(index), 0.05)
            return

        local = _cache_path_for(clip['source'])
        if os.path.exists(local):
            clip['_local'] = local
            card.status_text = 'Cached. Generating thumbnail...'
            Clock.schedule_once(
                lambda *_a: self._make_thumbnail(index), 0.05)
            return

        card.status_text = 'Downloading...'

        def on_progress(frac):
            if frac is None:
                card.status_text = 'Downloading...'
            else:
                card.status_text = f'Downloading {int(frac * 100)}%'

        def on_done(local_path, error):
            if error is not None or local_path is None:
                card.status_text = f'Download failed: {error}'
                return
            clip['_local'] = local_path
            card.status_text = 'Cached. Generating thumbnail...'
            self._make_thumbnail(index)

        _download_to_cache(
            clip['source'],
            on_progress=on_progress,
            on_done=on_done)

    def _make_thumbnail(self, index: int):
        clip = self.clips[index]
        card = clip['_card']
        local = clip.get('_local')
        if not local:
            card.status_text = 'Not available'
            return
        try:
            texture = Video.generate_thumbnail(local, time=2,
                                               size=(320, 180))
        except Exception as e:
            Logger.warning(
                f'AVFDemo: generate_thumbnail failed for {local}: {e}')
            card.status_text = 'Thumbnail unavailable (provider does ' \
                'not support generate_thumbnail or codec is ' \
                'unsupported)'
            return
        if texture is None:
            card.status_text = (
                'Thumbnail unavailable (provider does not support '
                'generate_thumbnail or codec is unsupported)')
            return
        card.thumb_texture = texture
        card.status_text = 'Ready - click "Open" to play'

    # ---- navigation ----

    def open_player(self, index: int):
        clip = self.clips[index]
        local = clip.get('_local')
        if not local:
            Logger.info(
                f'AVFDemo: clip {index} not yet available, skipping')
            return
        player = self.sm.get_screen('player')
        player.title = clip['title']
        player.source = local
        self._rebuild_video(player)
        player.video_state = 'play'
        self.sm.current = 'player'

    def go_to_grid(self):
        player = self.sm.get_screen('player')
        player.video_state = 'stop'
        # Drop the Video so the underlying core video releases the file.
        video = player.ids.video
        video.unload()
        self.sm.current = 'grid'

    # ---- player controls ----

    def toggle_play(self):
        player = self.sm.get_screen('player')
        if player.video_state == 'play':
            player.video_state = 'pause'
        else:
            player.video_state = 'play'

    def stop_play(self):
        self.sm.get_screen('player').video_state = 'stop'

    def seek_to(self, seconds: float):
        player = self.sm.get_screen('player')
        video = player.ids.video
        if video.duration > 0:
            video.seek(seconds / video.duration, precise=True)

    def restart_clip(self):
        '''Seek the current clip back to its start and resume playback.

        Note: deliberately does NOT rebuild the underlying ``Video``
        widget. Rebuilding would tear down the AVPlayer, re-fetch any
        HLS manifest, and force ABR back down to its lowest rung —
        producing a brief small / low-res rendering before the
        bitrate ladder climbs back up. ``apply_and_reload`` is the
        right entry point if you specifically want to reapply
        construction-time hints.
        '''
        player = self.sm.get_screen('player')
        video = player.ids.video
        video.seek(0.0, precise=True)
        player.video_state = 'play'

    def apply_and_reload(self):
        '''Re-create the underlying Video widget so the new buffer
        hints / options take effect at construction time.
        '''
        player = self.sm.get_screen('player')
        was_playing = player.video_state == 'play'
        player.video_state = 'stop'
        self._rebuild_video(player)
        player.video_state = 'play' if was_playing else 'stop'

    def _rebuild_video(self, player: 'PlayerScreen'):
        '''Apply the player screen's current options state to the
        underlying Video widget. The widget's construction-time kwargs
        (``options``) are forwarded to the core video at next
        ``_do_video_load``, which is triggered by re-assigning
        ``source``.
        '''
        video = player.ids.video
        video.options = {
            'automatically_waits_to_minimize_stalling':
                bool(player.auto_wait_to_minimize_stalling),
            'force_cpu_copy': bool(player.force_cpu_copy),
        }
        # Force a reload of the same source (clear then re-assign).
        current_source = player.source
        video.source = ''
        video.source = current_source


if __name__ == '__main__':
    AVFoundationDemoApp().run()
