'''
Audio Gstplayer
===============

.. versionadded:: 1.8.0

.. versionchanged:: 3.0.0
    Rewritten on the new GStreamer core shared with the ``gstplayer`` video
    provider: GStreamer is loaded at run time, and end of stream and errors
    are polled from the Clock instead of delivered on GStreamer's threads.
    The provider is now tried after ``sdl3``, so it plays the formats SDL3
    doesn't; ``KIVY_AUDIO_OUTPUT=gstplayer`` makes it the first choice.

Implementation of :class:`~kivy.core.audio_output.Sound` with GStreamer 1.x
(``playbin3``, audio only). See :mod:`kivy.core.video.video_gstplayer` for
where GStreamer comes from.
'''

import time

from kivy.lib.gstplayer import (
    GstPlayer, get_runtime_info, init_start, init_status, init_wait,
    filename_to_uri, STATE_PAUSED, STATE_PLAYING)
from kivy.lib.gstplayer._policy import BusError, error_text
from kivy.core.audio_output import Sound, SoundLoader
from kivy.logger import Logger
from kivy.clock import Clock

_version = get_runtime_info()[0]
Logger.info('AudioGstplayer: Using GStreamer {}'.format(
    '.'.join(map(str, _version[:3]))))


class SoundGstplayer(Sound):
    _provider_name = 'gstplayer'

    @staticmethod
    def extensions():
        return ('wav', 'ogg', 'oga', 'opus', 'mp3', 'm4a', 'aac', 'flac',
                'mp4', 'webm')

    def __init__(self, **kwargs):
        self._player = None
        self._uri = None
        self._tick = None
        self._prerolled = False
        self._error = None
        self._want_play = False
        super(SoundGstplayer, self).__init__(**kwargs)

    # ---------- Sound API ----------

    def load(self):
        self.unload()
        uri = self.source
        if not uri:
            return
        if '://' not in uri:
            uri = filename_to_uri(uri)
        self._uri = uri
        self._error = None
        self._prerolled = False
        init_start()
        if init_status()[0] == 'ok':
            self._build()
        self._tick = Clock.schedule_interval(self._update, 1 / 30.)

    def unload(self):
        if self._tick is not None:
            self._tick.cancel()
            self._tick = None
        if self._player is not None:
            self._player.teardown()
            self._player = None
        self._uri = None
        self._want_play = False

    def play(self):
        self._want_play = True
        if self._player is not None:
            self._player.set_volume(self.volume)
            self._player.set_state(STATE_PLAYING)
        super(SoundGstplayer, self).play()

    def stop(self):
        self._want_play = False
        if self._player is not None:
            self._player.set_state(STATE_PAUSED)
            self._player.seek(0.0, False)
        super(SoundGstplayer, self).stop()

    def seek(self, position):
        if self._player is not None:
            self._player.seek(float(position), True)

    def get_pos(self):
        if self._player is None:
            return 0
        pos = self._player.position()
        return pos if pos > 0 else 0

    def _get_length(self):
        if self._player is None and self._uri is not None:
            # Sound.length is synchronous, as it was with the old provider
            # (which blocked for up to 2 s): wait briefly for GStreamer.
            if init_wait(5)[0] == 'ok':
                self._build()
        if self._player is None:
            return 0
        if not self._prerolled:
            deadline = time.monotonic() + 1.0
            while not self._prerolled and self._player is not None and \
                    time.monotonic() < deadline:
                self._poll()
                time.sleep(0.005)
        if self._player is None:
            return 0
        dur = self._player.duration()
        return dur if dur > 0 else 0

    def on_volume(self, instance, volume):
        if self._player is not None:
            self._player.set_volume(volume)

    # ---------- GStreamer ----------

    def _build(self):
        if self._player is not None or self._uri is None:
            return
        player = GstPlayer(self._uri, sink=None)
        try:
            player.build()
        except RuntimeError as e:
            self._fail(str(e))
            return
        self._player = player
        player.set_volume(self.volume)
        player.set_state(STATE_PLAYING if self._want_play else STATE_PAUSED)

    def _fail(self, text):
        if self._error is None:
            self._error = text
            Logger.error('AudioGstplayer: <{}>: {}'.format(self.source, text))
        if self._player is not None:
            self._player.teardown()
            self._player = None
        if self.state != 'stop':
            super(SoundGstplayer, self).stop()

    def _poll(self):
        errors, missing, eos = [], [], False
        for m in self._player.pop_messages():
            if m[0] == 'error':
                errors.append(BusError(*m[1:]))
            elif m[0] == 'missing-plugin':
                missing.append(m[1])
            elif m[0] == 'async-done':
                self._prerolled = True
            elif m[0] == 'eos':
                eos = True
        if errors:
            self._fail(error_text(errors, missing))
        elif eos:
            if self.loop and self._want_play:
                self._player.seek(0.0, True)
            else:
                self.stop()

    def _update(self, dt):
        if self._error is not None:
            return
        if self._player is None:
            state, error = init_status()
            if state == 'error':
                self._fail(error)
            elif state == 'ok':
                self._build()
            return
        self._poll()


SoundLoader.register(SoundGstplayer)
