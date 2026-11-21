"""Tests for kivy.core.audio_output.audio_avplayer.

The provider imports rubicon-objc lazily through ``_objc()``, so most tests
replace that helper with fakes and run on any platform. ``audio_avplayer.py``
registers itself with the global ``SoundLoader`` on import, so it is loaded
by file path and the registry is restored afterwards, as in
``test_audio_android.py``. The tests at the end use the real AVFoundation and
only run on macOS.
"""

import importlib.machinery
import importlib.util
import math
import os
import struct
import sys
import time
import types
import wave
from contextlib import contextmanager
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).parent.parent / "core" / "audio_output" /
    "audio_avplayer.py"
)


class _FakePlayer:
    def __init__(self, path):
        self.path = path
        self.calls = []
        self.enableRate = False
        self.rate = 1.0
        self.volume = 1.0
        self.numberOfLoops = 0
        self.delegate = None
        self.currentTime = 0.0
        self.duration = 2.5
        self.play_result = True

    def prepareToPlay(self):
        self.calls.append(("prepareToPlay", self.enableRate))
        return True

    def play(self):
        self.calls.append(("play",))
        return self.play_result

    def stop(self):
        self.calls.append(("stop",))


class _FakeAlloc:
    def __init__(self, player_class):
        self._player_class = player_class

    def initWithContentsOfURL(self, url, error=None):
        if url.endswith("missing.m4a"):
            return None
        player = _FakePlayer(url)
        self._player_class.created.append(player)
        return player


class _FakeAVAudioPlayer:
    created = []

    @classmethod
    def alloc(cls):
        return _FakeAlloc(cls)


class _FakeNSURL:
    @staticmethod
    def fileURLWithPath(path):
        return path


class _FakeDelegate:
    created = 0

    @classmethod
    def alloc(cls):
        return cls()

    def init(self):
        type(self).created += 1
        self.sound = None
        return self


def _fake_objc():
    return _FakeAVAudioPlayer, _FakeNSURL, _FakeDelegate


@contextmanager
def _load_module(rubicon_installed=True):
    """Load a fresh ``audio_avplayer`` and restore the registry after."""
    from kivy.core.audio_output import SoundLoader

    saved_classes = list(SoundLoader._classes)
    saved_by_name = dict(SoundLoader._loaders_by_name)
    saved_rubicon = sys.modules.get("rubicon", False)
    if rubicon_installed:
        if saved_rubicon is False:
            fake = types.ModuleType("rubicon")
            fake.__spec__ = importlib.machinery.ModuleSpec("rubicon", None)
            sys.modules["rubicon"] = fake
    else:
        sys.modules["rubicon"] = None
    _FakeAVAudioPlayer.created = []
    _FakeDelegate.created = 0

    try:
        spec = importlib.util.spec_from_file_location(
            "audio_avplayer", _MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module._objc = _fake_objc
        yield module
    finally:
        SoundLoader._classes = saved_classes
        SoundLoader._loaders_by_name = saved_by_name
        if saved_rubicon is False:
            sys.modules.pop("rubicon", None)
        else:
            sys.modules["rubicon"] = saved_rubicon


class _Events:
    def __init__(self, sound):
        self.names = []
        sound.bind(on_play=lambda *a: self.names.append("on_play"),
                   on_stop=lambda *a: self.names.append("on_stop"))


def test_module_is_ignored_without_rubicon():
    with pytest.raises(ImportError, match="rubicon-objc"):
        with _load_module(rubicon_installed=False):
            pass


def test_rubicon_is_not_needed_until_load():
    with _load_module() as module:
        def fail():
            raise AssertionError("_objc() called before load()")

        module._objc = fail
        assert "m4a" in module.SoundAvplayer.extensions()
        module.SoundAvplayer()


def test_load_configures_the_player():
    with _load_module() as module:
        sound = module.SoundAvplayer(
            source="/tmp/a.m4a", volume=0.5, pitch=1.5, loop=True)

    player = sound._avplayer
    assert player.path == "/tmp/a.m4a"
    # enableRate must be set before prepareToPlay or rate is ignored
    assert player.calls == [("prepareToPlay", True)]
    assert player.rate == 1.5
    assert player.volume == 0.5
    assert player.numberOfLoops == -1
    assert player.delegate is sound._delegate
    assert sound._delegate.sound is sound
    assert sound.length == 2.5


def test_delegate_is_reused_across_loads():
    with _load_module() as module:
        sound = module.SoundAvplayer(source="/tmp/a.m4a")
        sound.source = "/tmp/b.m4a"

    assert _FakeDelegate.created == 1
    first, second = _FakeAVAudioPlayer.created
    assert first.delegate is None
    assert second.delegate is sound._delegate


def test_load_failure_leaves_a_silent_sound():
    with _load_module() as module:
        sound = module.SoundAvplayer(source="/tmp/missing.m4a")
        events = _Events(sound)
        sound.play()

    assert sound._avplayer is None
    assert sound.state == "stop"
    assert events.names == []


def test_play_from_stopped_does_not_dispatch_on_stop():
    with _load_module() as module:
        sound = module.SoundAvplayer(source="/tmp/a.m4a")
        events = _Events(sound)
        sound.play()

    assert sound.state == "play"
    assert events.names == ["on_play"]


def test_play_while_playing_restarts():
    with _load_module() as module:
        sound = module.SoundAvplayer(source="/tmp/a.m4a")
        sound.play()
        events = _Events(sound)
        sound.play()

    assert events.names == ["on_stop", "on_play"]


def test_failed_play_keeps_the_sound_stopped():
    with _load_module() as module:
        sound = module.SoundAvplayer(source="/tmp/a.ogg")
        sound._avplayer.play_result = False
        events = _Events(sound)
        sound.play()

    assert sound.state == "stop"
    assert events.names == []


def test_stop_rewinds_and_dispatches_once():
    with _load_module() as module:
        sound = module.SoundAvplayer(source="/tmp/a.m4a")
        sound.play()
        sound._avplayer.currentTime = 1.25
        events = _Events(sound)
        sound.stop()
        sound.stop()

    assert sound._avplayer.currentTime == 0.0
    assert sound.state == "stop"
    assert events.names == ["on_stop"]


def test_end_of_sound_dispatches_on_stop():
    with _load_module() as module:
        sound = module.SoundAvplayer(source="/tmp/a.m4a")
        sound.play()
        events = _Events(sound)
        sound._on_finished()
        sound._on_finished()

    assert sound.state == "stop"
    assert events.names == ["on_stop"]


def test_properties_update_the_player():
    with _load_module() as module:
        sound = module.SoundAvplayer(source="/tmp/a.m4a")
        sound.loop = True
        sound.pitch = 0.75
        sound.volume = 0.25
        sound.seek(1.5)

    player = sound._avplayer
    assert player.numberOfLoops == -1
    assert player.rate == 0.75
    assert player.volume == 0.25
    assert sound.get_pos() == 1.5


# Real AVFoundation (macOS only)

_needs_avfoundation = pytest.mark.skipif(
    sys.platform != "darwin" or importlib.util.find_spec("rubicon") is None,
    reason="needs macOS and rubicon-objc")


def _write_tone(path, seconds, rate=44100):
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(
            struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i /
                                                  rate)))
            for i in range(int(seconds * rate))))


@_needs_avfoundation
def test_real_load_reports_length(tmp_path):
    from kivy.core.audio_output import audio_avplayer

    path = tmp_path / "tone.wav"
    _write_tone(path, 0.5)
    sound = audio_avplayer.SoundAvplayer(source=str(path))
    try:
        assert sound._avplayer is not None
        assert sound.length == pytest.approx(0.5, abs=0.01)
    finally:
        sound.unload()


@_needs_avfoundation
@pytest.mark.skipif(os.environ.get("KIVY_TEST_AUDIO") == "0",
                    reason="Audio is not available")
def test_real_play_and_stop(tmp_path):
    from kivy.core.audio_output import audio_avplayer

    path = tmp_path / "tone.wav"
    _write_tone(path, 2.0)
    sound = audio_avplayer.SoundAvplayer(source=str(path))
    try:
        sound.play()
        assert sound.state == "play"
        time.sleep(0.3)
        assert sound.get_pos() > 0
        sound.stop()
        assert sound.state == "stop"
        assert sound.get_pos() == 0
    finally:
        sound.unload()
