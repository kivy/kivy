"""Tests for kivy.core.video.video_android.

``video_android`` imports ``jnius`` and ``kivy.mobile._platform.android`` at
module scope, so it can't be imported off-device by normal means. Like
``test_audio_android.py``, these tests install fake modules in
``sys.modules`` and load ``video_android.py`` by file path.

The fake ``run_on_ui_thread`` and ``Handler.post`` queue work on a fake UI
thread that the tests drain explicitly, and the fake player fails any call
made outside it: ExoPlayer may only be called on its own thread, and that
rule is the core of the provider. GL is faked: texture names come from a
counter, and ``_build_fbo`` installs a fake FBO.
"""

import importlib.util
import struct
import sys
import types
from itertools import count
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).parent.parent / "core" / "video" / "video_android.py"

STATE_IDLE, STATE_BUFFERING, STATE_READY, STATE_ENDED = 1, 2, 3, 4
TIME_UNSET = -9223372036854775807


class _JavaException(Exception):
    pass


class _UiThread:
    """A FIFO standing in for the Android UI thread's message queue."""

    def __init__(self):
        self.queue = []
        self.active = False

    def post(self, func, *args, **kwargs):
        self.queue.append(lambda: func(*args, **kwargs))

    def run_all(self):
        while self.queue:
            work = self.queue.pop(0)
            self.active = True
            try:
                work()
            finally:
                self.active = False


_ui = None
_events = None


class _Looper:
    MAIN = object()

    @classmethod
    def getMainLooper(cls):
        return cls.MAIN


class _Handler:
    def __init__(self, looper):
        assert looper is _Looper.MAIN

    def post(self, runnable):
        _ui.post(runnable.run)
        return True


class _File:
    def __init__(self, path):
        self.path = path


class _Uri:
    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

    @classmethod
    def parse(cls, value):
        return cls("parse", value)

    @classmethod
    def fromFile(cls, file):
        return cls("file", file.path)

    def getPath(self):
        return self.value.split("://", 1)[1]


class _SurfaceTexture:
    def __init__(self, texture_id):
        self.texture_id = texture_id
        self.timestamp = 0
        self.transform = None

    def updateTexImage(self):
        pass

    def getTimestamp(self):
        return self.timestamp

    def getTransformMatrix(self, out):
        if self.transform is not None:
            out[:] = self.transform

    def release(self):
        _events.append(("surface_texture.release", self.texture_id))


class _Surface:
    def __init__(self, surface_texture):
        self.surface_texture = surface_texture

    def release(self):
        _events.append(("surface.release", self.surface_texture.texture_id))


class _VideoSize:
    def __init__(self, width, height, ratio=1.0):
        self.width = width
        self.height = height
        self.pixelWidthHeightRatio = ratio


class _Format:
    def __init__(self, width, height, rotation=0):
        self.width = width
        self.height = height
        self.rotationDegrees = rotation


class _Throwable:
    def __init__(self, message):
        self._message = message

    def getMessage(self):
        return self._message


class _PlaybackException(_Throwable):
    def __init__(self, code_name, message, cause=None):
        super().__init__(message)
        self._code_name = code_name
        self._cause = None if cause is None else _Throwable(cause)

    def getErrorCodeName(self):
        return self._code_name

    def getCause(self):
        return self._cause


class _FakePlayer:
    def __init__(self, builder):
        self.builder = builder
        self.calls = []
        self.state = STATE_IDLE
        self.position = 0
        self.duration = TIME_UNSET
        self.live = False
        self.live_edge = 0
        self.size = _VideoSize(0, 0)
        self.video_format = None
        self.error = None
        self.fail_on = None

    def _call(self, name, *args):
        assert _ui.active, "{} called off the UI thread".format(name)
        if name == self.fail_on:
            raise _JavaException("{} failed".format(name))
        self.calls.append((name,) + args)

    def _get(self, value):
        assert _ui.active, "player read off the UI thread"
        return value

    def setVideoSurface(self, surface):
        self._call("setVideoSurface", surface)

    def setVolume(self, volume):
        self._call("setVolume", volume)

    def setMediaItem(self, item):
        self._call("setMediaItem", item)

    def prepare(self):
        self._call("prepare")

    def play(self):
        self._call("play")

    def pause(self):
        self._call("pause")

    def setSeekParameters(self, parameters):
        self._call("setSeekParameters", parameters)

    def seekTo(self, position_ms):
        self._call("seekTo", position_ms)
        self.position = position_ms
        if self.state == STATE_ENDED:
            self.state = STATE_READY

    def stop(self):
        self._call("stop")
        self.state = STATE_IDLE

    def seekToDefaultPosition(self):
        self._call("seekToDefaultPosition")
        self.position = self.live_edge
        if self.state == STATE_ENDED:
            self.state = STATE_READY

    def release(self):
        self._call("release")
        _events.append(("player.release",))

    def getPlaybackState(self):
        return self._get(self.state)

    def getCurrentPosition(self):
        return self._get(self.position)

    def getDuration(self):
        return self._get(self.duration)

    def isCurrentMediaItemLive(self):
        return self._get(self.live)

    def getVideoSize(self):
        return self._get(self.size)

    def getVideoFormat(self):
        return self._get(self.video_format)

    def getPlayerError(self):
        return self._get(self.error)


class _Builder:
    built = []

    def __init__(self, context):
        self.context = context
        self.looper = None
        self.audio = None

    def setLooper(self, looper):
        self.looper = looper
        return self

    def setAudioAttributes(self, attributes, handle_audio_focus):
        self.audio = (attributes, handle_audio_focus)
        return self

    def build(self):
        player = _FakePlayer(self)
        _Builder.built.append(player)
        return player


class _AudioAttributesBuilder:
    def setUsage(self, usage):
        self.usage = usage
        return self

    def setContentType(self, content_type):
        self.content_type = content_type
        return self

    def build(self):
        return ("audio-attributes", self.usage, self.content_type)


class _MediaItem:
    @staticmethod
    def fromUri(uri):
        return ("media-item", uri)


class _SeekParameters:
    EXACT = "EXACT"
    CLOSEST_SYNC = "CLOSEST_SYNC"


class _C:
    USAGE_MEDIA = 1
    AUDIO_CONTENT_TYPE_MOVIE = 3


class _Player:
    STATE_IDLE = STATE_IDLE
    STATE_BUFFERING = STATE_BUFFERING
    STATE_READY = STATE_READY
    STATE_ENDED = STATE_ENDED


class _Retriever:
    OPTION_CLOSEST = 3
    instances = []

    def __init__(self):
        self.source = None
        self.frame_args = None
        self.released = False
        _Retriever.instances.append(self)

    def setDataSource(self, *args):
        self.source = args

    def getFrameAtTime(self, time_us, option):
        self.frame_args = (time_us, option)
        return None

    def release(self):
        self.released = True


_MEDIA3_CLASSES = {
    "androidx.media3.exoplayer.ExoPlayer$Builder": _Builder,
    "androidx.media3.common.MediaItem": _MediaItem,
    "androidx.media3.common.AudioAttributes$Builder": _AudioAttributesBuilder,
    "androidx.media3.exoplayer.SeekParameters": _SeekParameters,
    "androidx.media3.common.C": _C,
    "androidx.media3.common.Player": _Player,
}

_CLASSES = {
    "java.io.File": _File,
    "android.net.Uri": _Uri,
    "android.os.Looper": _Looper,
    "android.os.Handler": _Handler,
    "android.view.Surface": _Surface,
    "android.graphics.SurfaceTexture": _SurfaceTexture,
    "android.media.MediaMetadataRetriever": _Retriever,
    "java.util.HashMap": dict,
    **_MEDIA3_CLASSES,
}


class _FakeFbo:
    def __init__(self, size):
        self.size = size
        self.uniforms = {}
        self.draws = 0
        self.texture = ("fbo-texture", size)

    def __setitem__(self, key, value):
        self.uniforms[key] = value

    def draw(self):
        self.draws += 1


class _FakeCallback:
    def ask_update(self):
        pass


class _RecordingLogger:
    def __init__(self):
        self.records = []

    def __getattr__(self, level):
        return lambda message, *args: self.records.append((level, message))


class _Env:
    def __init__(self, module, deleted, settings):
        self.module = module
        self.deleted = deleted
        self.settings = settings
        self.ui = _ui
        self.events = _events

        class TestVideo(module.VideoAndroid):
            def _build_fbo(self, width, height):
                self._fbo = _FakeFbo((width, height))
                self._texture_cb = _FakeCallback()
                self._fbo_size = (width, height)
                return True

        self.Video = TestVideo

    def make(self, **kwargs):
        kwargs.setdefault("filename", "/sdcard/clip.mp4")
        return self.Video(**kwargs)

    @property
    def player(self):
        return _Builder.built[-1]

    def settle(self, video):
        """Let posted calls run, then two ticks: one to request a poll,
        one to act on the snapshot it took."""
        for _ in range(2):
            self.ui.run_all()
            video._update(0)
        self.ui.run_all()


@pytest.fixture
def env(monkeypatch):
    global _ui, _events
    _ui = _UiThread()
    _events = []
    _Builder.built = []
    _Retriever.instances = []
    settings = types.SimpleNamespace(
        context=object(), missing=set(), ui_error=None)

    def autoclass(name):
        if name in settings.missing:
            raise _JavaException("Class not found {!r}".format(name))
        return _CLASSES[name]

    def run_on_ui_thread(func, *args, **kwargs):
        if settings.ui_error is not None:
            raise settings.ui_error
        _ui.post(func, *args, **kwargs)

    jnius = types.ModuleType("jnius")
    jnius.autoclass = autoclass
    jnius.JavaException = _JavaException
    jnius.java_method = lambda *_a, **_kw: (lambda func: func)
    jnius.PythonJavaClass = object

    android = types.ModuleType("kivy.mobile._platform.android")
    android.get_app_context = lambda: settings.context
    android.run_on_ui_thread = run_on_ui_thread

    monkeypatch.setitem(sys.modules, "jnius", jnius)
    monkeypatch.setitem(sys.modules, "kivy.mobile", types.ModuleType("kivy.mobile"))
    monkeypatch.setitem(
        sys.modules, "kivy.mobile._platform",
        types.ModuleType("kivy.mobile._platform"))
    monkeypatch.setitem(sys.modules, "kivy.mobile._platform.android", android)

    spec = importlib.util.spec_from_file_location(
        "video_android_under_test", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    texture_ids = count(10)
    deleted = []
    module.glGenTextures = lambda n: [next(texture_ids)]
    module.glDeleteTextures = (
        lambda n, data: deleted.append(struct.unpack("I", data)[0]))
    return _Env(module, deleted, settings)


def _record(video, *events):
    log = []
    for name in events:
        video.bind(**{name: lambda *args, _name=name: log.append((_name,) + args[1:])})
    return log


class TestLoad:
    def test_player_runs_on_the_main_looper(self, env):
        env.make()

        assert env.player.builder.looper is _Looper.MAIN

    def test_audio_focus_is_handled(self, env):
        env.make()

        attributes, handle_audio_focus = env.player.builder.audio
        assert attributes == ("audio-attributes", _C.USAGE_MEDIA,
                              _C.AUDIO_CONTENT_TYPE_MOVIE)
        assert handle_audio_focus is True

    def test_no_player_call_is_made_on_kivys_thread(self, env):
        env.make()

        assert env.player.calls == []
        env.ui.run_all()
        names = [call[0] for call in env.player.calls]
        assert names == ["setVideoSurface", "setVolume", "setMediaItem", "prepare"]

    def test_plain_path_becomes_a_file_uri(self, env):
        env.make(filename="/sdcard/clip.mp4")
        env.ui.run_all()

        item = dict((c[0], c[1:]) for c in env.player.calls)["setMediaItem"][0]
        assert (item[1].kind, item[1].value) == ("file", "/sdcard/clip.mp4")

    @pytest.mark.parametrize("uri", [
        "content://media/external/video/media/42",
        "https://example.com/stream.m3u8",
        "file:///sdcard/clip.mp4",
    ])
    def test_uri_with_a_scheme_is_parsed(self, env, uri):
        env.make(filename=uri)
        env.ui.run_all()

        item = dict((c[0], c[1:]) for c in env.player.calls)["setMediaItem"][0]
        assert (item[1].kind, item[1].value) == ("parse", uri)

    def test_surface_is_bound_to_a_fresh_texture_name(self, env):
        video = env.make()
        env.ui.run_all()

        surface = env.player.calls[0][1]
        assert surface is video._surface
        assert surface.surface_texture.texture_id == video._oes_id

    def test_unknown_options_are_warned_about(self, env, monkeypatch):
        logger = _RecordingLogger()
        monkeypatch.setattr(env.module, "Logger", logger)

        env.make(options={"no_such_key": True})

        assert any(level == "warning" and "no_such_key" in message
                   for level, message in logger.records)

    def test_eos_in_options_is_not_unknown(self, env, monkeypatch):
        # The Video widget forwards options={'eos': ...} as a keyword too.
        logger = _RecordingLogger()
        monkeypatch.setattr(env.module, "Logger", logger)

        env.make(options={"eos": "loop"})

        assert not any(level == "warning" for level, _ in logger.records)


class TestErrors:
    def test_missing_media3_fires_on_error_from_update_once(self, env):
        env.settings.missing.update(_MEDIA3_CLASSES)
        video = env.make()  # must not raise
        log = _record(video, "on_error")
        video.play()

        video._update(0)
        video._update(0)

        assert len(log) == 1
        assert "androidx.media3:media3-exoplayer" in log[0][1]
        assert "-keep class androidx.media3.** { *; }" in log[0][1]
        assert video.state == ""
        assert _Builder.built == []

    def test_no_context_fires_on_error(self, env):
        env.settings.context = None
        video = env.make()
        log = _record(video, "on_error")

        video._update(0)

        assert log == [("on_error", "no Android Activity to play video in")]

    def test_player_error_fires_on_error_once_and_stops(self, env):
        video = env.make()
        log = _record(video, "on_error", "on_buffering")
        video.play()
        env.settle(video)
        env.player.error = _PlaybackException(
            "ERROR_CODE_IO_FILE_NOT_FOUND", "Source error",
            cause="/sdcard/clip.mp4: open failed: ENOENT")

        env.settle(video)
        env.settle(video)

        errors = [entry for entry in log if entry[0] == "on_error"]
        assert errors == [(
            "on_error",
            "ERROR_CODE_IO_FILE_NOT_FOUND: Source error "
            "(/sdcard/clip.mp4: open failed: ENOENT)")]
        assert video.state == ""
        assert video.buffering is False

    def test_error_without_a_message_has_just_its_code(self, env):
        video = env.make()
        log = _record(video, "on_error")
        env.settle(video)
        env.player.error = _PlaybackException(
            "ERROR_CODE_DECODING_FAILED", None)

        env.settle(video)

        assert log == [("on_error", "ERROR_CODE_DECODING_FAILED")]

    def test_failed_player_call_fires_on_error(self, env):
        video = env.make()
        log = _record(video, "on_error")
        env.settle(video)
        env.player.fail_on = "play"

        video.play()
        env.settle(video)

        assert log == [("on_error", "play failed")]

    def test_unreachable_ui_thread_fires_on_error(self, env):
        env.settings.ui_error = AttributeError("no Activity")
        video = env.make()
        log = _record(video, "on_error")

        video._update(0)

        assert log == [("on_error", "could not reach the Android UI thread: "
                                    "no Activity")]

    def test_reload_clears_a_reported_error(self, env):
        video = env.make()
        log = _record(video, "on_error")
        env.settle(video)
        env.player.error = _PlaybackException("ERROR_CODE_IO_UNSPECIFIED", "x")
        env.settle(video)

        video.filename = "/sdcard/other.mp4"
        env.settle(video)

        assert len(log) == 1
        assert video._error_reported is False


class TestPlayback:
    def test_buffering_until_ready_while_playing(self, env):
        video = env.make()
        log = _record(video, "on_buffering")
        video.play()

        video._update(0)
        assert log == [("on_buffering", True)]

        env.player.state = STATE_READY
        env.settle(video)
        assert log == [("on_buffering", True), ("on_buffering", False)]

    def test_no_buffering_while_paused(self, env):
        video = env.make()
        log = _record(video, "on_buffering")
        env.player.state = STATE_BUFFERING

        env.settle(video)

        assert log == []

    def test_play_pause_stop_reach_the_player(self, env):
        video = env.make()
        env.settle(video)
        env.player.calls.clear()

        video.play()
        video.pause()
        video.stop()
        env.ui.run_all()

        assert env.player.calls == [
            ("play",), ("pause",), ("pause",), ("seekTo", 0)]

    def test_play_after_the_end_rewinds_first(self, env):
        video = env.make()
        env.settle(video)
        env.player.state = STATE_ENDED
        env.player.calls.clear()

        video.play()
        env.ui.run_all()

        assert env.player.calls == [("seekTo", 0), ("play",)]

    def test_stop_then_play_reconnects_a_live_stream_at_the_live_edge(
            self, env):
        # Seeking stalls a live stream: position 0 is outside an HLS live
        # window, and RTSP delivers nothing after a seek.
        video = env.make()
        env.player.live = True
        env.player.position = env.player.live_edge = 40000
        video.play()
        env.settle(video)
        env.player.calls.clear()

        video.stop()
        # Not 0: the live edge's position isn't known until the next poll.
        assert video.position == 40.0
        env.ui.run_all()
        assert env.player.calls == [("pause",), ("stop",)]

        env.player.calls.clear()
        video.play()
        env.ui.run_all()
        assert env.player.calls == [
            ("seekToDefaultPosition",), ("prepare",), ("play",)]

        # Only once: a later play() after a pause just plays.
        env.player.calls.clear()
        video.pause()
        video.play()
        env.ui.run_all()
        assert env.player.calls == [("pause",), ("play",)]

    def test_stop_after_an_error_does_not_reconnect_a_live_stream(self, env):
        video = env.make()
        env.player.live = True
        env.player.error = _PlaybackException("ERROR_CODE_IO", "lost")
        env.settle(video)
        env.player.calls.clear()

        video.stop()
        video.play()
        env.ui.run_all()

        assert env.player.calls == [("pause",), ("seekTo", 0), ("play",)]

    def test_play_after_the_end_of_a_live_stream_reconnects(self, env):
        video = env.make()
        env.settle(video)
        env.player.live = True
        env.player.state = STATE_ENDED
        env.player.calls.clear()

        video.play()
        env.ui.run_all()

        assert env.player.calls == [
            ("stop",), ("seekToDefaultPosition",), ("prepare",), ("play",)]

    def test_volume(self, env):
        video = env.make()
        env.settle(video)
        env.player.calls.clear()

        video.volume = 0.25
        env.ui.run_all()

        assert env.player.calls == [("setVolume", 0.25)]

    def test_duration_is_zero_until_known(self, env):
        video = env.make()
        env.settle(video)
        assert video.duration == 0.0

        env.player.duration = 12500
        env.settle(video)
        assert video.duration == 12.5

    def test_seek_precise_and_position_until_the_player_catches_up(self, env):
        video = env.make()
        env.player.duration = 10000
        env.settle(video)
        env.player.calls.clear()

        video.seek(0.5)
        assert video.position == 5.0  # before the seek has even run

        env.settle(video)
        assert env.player.calls[:2] == [
            ("setSeekParameters", "EXACT"), ("seekTo", 5000)]
        assert video.position == 5.0

        env.player.position = 6000
        env.settle(video)
        assert video.position == 6.0

    def test_imprecise_seek_uses_the_nearest_keyframe(self, env):
        video = env.make()
        env.player.duration = 10000
        env.settle(video)
        env.player.calls.clear()

        video.seek(0.25, precise=False)
        env.ui.run_all()

        assert env.player.calls == [
            ("setSeekParameters", "CLOSEST_SYNC"), ("seekTo", 2500)]

    def test_seek_before_the_duration_is_known_does_nothing(self, env):
        video = env.make()
        env.settle(video)
        env.player.calls.clear()

        video.seek(0.5)
        env.ui.run_all()

        assert env.player.calls == []

    def test_end_fires_on_eos_once(self, env):
        video = env.make(eos="stop")
        log = _record(video, "on_eos")
        env.player.duration = 10000
        video.play()
        env.settle(video)

        env.player.state = STATE_ENDED
        env.settle(video)
        env.settle(video)

        assert log == [("on_eos",)]
        assert video.state == ""

    def test_loop_replays_and_fires_on_eos_each_time(self, env):
        video = env.make(eos="loop")
        log = _record(video, "on_eos")
        env.player.duration = 10000
        video.play()
        env.settle(video)

        env.player.state = STATE_ENDED
        env.settle(video)
        assert ("seekTo", 0) in env.player.calls
        assert env.player.calls[-1] == ("play",)
        env.settle(video)
        assert log == [("on_eos",)]

        env.player.state = STATE_ENDED
        env.settle(video)
        assert log == [("on_eos",), ("on_eos",)]


class TestFrames:
    def _playing(self, env, size=_VideoSize(640, 360)):
        video = env.make()
        log = _record(video, "on_load", "on_frame")
        env.player.size = size
        env.player.state = STATE_READY
        video.play()
        env.settle(video)
        return video, log

    def test_fbo_is_sized_from_the_video_size(self, env):
        video, _ = self._playing(env)

        assert video._fbo.size == (640, 360)

    def test_anamorphic_video_is_sized_for_display(self, env):
        video, _ = self._playing(env, size=_VideoSize(720, 576, ratio=16 / 15))

        assert video._fbo.size == (768, 576)

    def test_format_size_is_used_while_the_video_size_is_unknown(self, env):
        video = env.make()
        env.player.video_format = _Format(1920, 1080, rotation=90)

        env.settle(video)

        assert video._fbo.size == (1080, 1920)

    def test_on_load_once_and_on_frame_per_new_frame(self, env):
        video, log = self._playing(env)
        assert log == []  # no frame decoded yet

        video._surface_texture.timestamp = 100
        video._update(0)
        video._update(0)
        video._surface_texture.timestamp = 200
        video._update(0)

        assert log == [("on_load",), ("on_frame",), ("on_frame",)]
        assert video._fbo.draws == 2
        assert video.texture is video._fbo.texture

    def test_decoder_transform_is_applied(self, env):
        video, _ = self._playing(env)
        transform = [1.0, 0.0, 0.0, 0.0,
                     0.0, -1.0, 0.0, 0.0,
                     0.0, 0.0, 1.0, 0.0,
                     0.0, 1.0, 0.0, 1.0]
        video._surface_texture.transform = transform
        video._surface_texture.timestamp = 100

        video._update(0)

        assert video._fbo.uniforms["tex_matrix"].get() == tuple(transform)

    def test_missing_transform_falls_back_to_the_usual_one(self, env, monkeypatch):
        logger = _RecordingLogger()
        monkeypatch.setattr(env.module, "Logger", logger)
        video, _ = self._playing(env)
        video._surface_texture.timestamp = 100

        video._update(0)
        video._surface_texture.timestamp = 200
        video._update(0)

        assert (video._fbo.uniforms["tex_matrix"].get()
                == env.module._DEFAULT_TRANSFORM)
        assert sum(level == "info" for level, _ in logger.records) == 1


class TestUnload:
    def test_player_is_released_before_its_surface(self, env):
        video = env.make()
        env.settle(video)
        texture_id = video._oes_id

        video.unload()
        assert env.deleted == [texture_id]
        assert env.events == []  # release waits for the UI thread

        env.ui.run_all()
        assert env.events == [
            ("player.release",),
            ("surface.release", texture_id),
            ("surface_texture.release", texture_id)]

    def test_calls_posted_before_unload_reach_the_old_player_first(self, env):
        video = env.make()
        env.settle(video)
        player = env.player
        player.calls.clear()

        video.play()
        video.unload()
        env.ui.run_all()

        assert player.calls == [("play",), ("release",)]

    def test_snapshot_from_a_previous_video_is_ignored(self, env):
        video = env.make()
        env.player.duration = 10000
        video._update(0)  # posts a poll of the first player

        video.filename = "/sdcard/other.mp4"
        env.ui.run_all()

        assert video.duration == 0.0


class TestAppLifecycle:
    def test_pause_and_resume_with_the_app(self, env):
        video = env.make()
        video.play()
        env.settle(video)
        player = env.player
        old_surface = video._surface
        old_texture_id = video._oes_id
        player.calls.clear()

        video._on_app_pause()
        env.ui.run_all()
        assert player.calls == [("pause",)]

        video._on_app_resume()
        env.ui.run_all()
        assert player.calls[1] == ("setVideoSurface", video._surface)
        assert video._surface is not old_surface
        assert player.calls[2] == ("play",)
        assert ("surface.release", old_texture_id) in env.events
        # The old name may belong to another texture after a context loss.
        assert env.deleted == []

    def test_resume_does_not_play_a_paused_video(self, env):
        video = env.make()
        env.settle(video)
        player = env.player

        video._on_app_pause()
        video._on_app_resume()
        env.ui.run_all()

        assert ("play",) not in player.calls


class TestThumbnail:
    @pytest.mark.parametrize("filename, expected", [
        ("/sdcard/clip.mp4", ("/sdcard/clip.mp4",)),
        ("file:///sdcard/clip.mp4", ("/sdcard/clip.mp4",)),
    ])
    def test_local_files_use_the_path(self, env, filename, expected):
        env.Video.generate_thumbnail(filename, 1.5)

        retriever = _Retriever.instances[-1]
        assert retriever.source == expected
        assert retriever.frame_args == (1500000, _Retriever.OPTION_CLOSEST)

    def test_content_uri_uses_the_context(self, env):
        uri = "content://media/external/video/media/42"

        env.Video.generate_thumbnail(uri, 0)

        context, parsed = _Retriever.instances[-1].source
        assert context is env.settings.context
        assert (parsed.kind, parsed.value) == ("parse", uri)

    def test_http_url_uses_the_headers_overload(self, env):
        env.Video.generate_thumbnail("https://example.com/a.mp4", 0)

        url, headers = _Retriever.instances[-1].source
        assert url == "https://example.com/a.mp4"
        assert headers == {}

    def test_no_frame_returns_none_and_releases(self, env):
        assert env.Video.generate_thumbnail("/sdcard/clip.mp4", 3) is None
        assert _Retriever.instances[-1].released is True
