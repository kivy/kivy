"""Tests for kivy.core.audio_output.audio_android.

``audio_android`` does ``from jnius import autoclass, java_method,
PythonJavaClass`` and ``from kivy.mobile._platform.android import
get_app_context`` at module scope, so it cannot be imported off-device by
normal means: ``jnius`` is not installed, and importing ``kivy.mobile`` on a
non-mobile platform raises ``ImportError`` (see ``kivy/mobile/__init__.py``).

Like ``test_clipboard_android.py``, this installs fake ``jnius`` and
``kivy.mobile._platform.android`` modules in ``sys.modules`` and loads
``audio_android.py`` directly by file path. The fakes only stand in for what
``SoundAndroidPlayer.load`` touches.
"""

import importlib.util
import sys
import types
from contextlib import contextmanager
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).parent.parent / "core" / "audio_output" / "audio_android.py"
)


class _FakeVersion:
    SDK_INT = 33


class _FakeUri:
    parsed = []

    def __init__(self, value):
        self.value = value

    @classmethod
    def parse(cls, value):
        cls.parsed.append(value)
        return cls(value)


class _FakeAudioManager:
    STREAM_MUSIC = 3


class _FakeAudioAttributesBuilder:
    def setLegacyStreamType(self, stream_type):
        self.stream_type = stream_type
        return self

    def build(self):
        return "audio-attributes"


class _FakeMediaPlayer:
    """Records the calls ``SoundAndroidPlayer.load`` makes."""

    def __init__(self):
        self.data_source = None
        self.calls = []

    def setAudioAttributes(self, attributes):
        self.calls.append(("setAudioAttributes", attributes))

    def setAudioStreamType(self, stream_type):
        self.calls.append(("setAudioStreamType", stream_type))

    def setDataSource(self, *args):
        self.data_source = args
        self.calls.append(("setDataSource", args))

    def setOnCompletionListener(self, listener):
        pass

    def prepare(self):
        self.calls.append(("prepare",))

    def release(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def setLooping(self, looping):
        pass

    def setVolume(self, left, right):
        pass

    def getDuration(self):
        return 1000

    def getCurrentPosition(self):
        return 0


_CLASSES = {
    "android.os.Build$VERSION": _FakeVersion,
    "android.media.MediaPlayer": _FakeMediaPlayer,
    "android.media.AudioManager": _FakeAudioManager,
    "android.media.AudioAttributes$Builder": _FakeAudioAttributesBuilder,
    "android.net.Uri": _FakeUri,
}


def _autoclass(name):
    return _CLASSES[name]


@contextmanager
def _fake_environment(get_app_context):
    """Install fake ``jnius``/backend modules, then load a fresh module."""
    jnius_module = types.ModuleType("jnius")
    jnius_module.autoclass = _autoclass
    jnius_module.java_method = lambda *_a, **_kw: (lambda func: func)
    jnius_module.PythonJavaClass = object

    android_module = types.ModuleType("kivy.mobile._platform.android")
    android_module.get_app_context = get_app_context

    affected = (
        "jnius",
        "kivy.mobile",
        "kivy.mobile._platform",
        "kivy.mobile._platform.android",
    )
    saved = {name: sys.modules.get(name) for name in affected}

    sys.modules["jnius"] = jnius_module
    sys.modules["kivy.mobile"] = types.ModuleType("kivy.mobile")
    sys.modules["kivy.mobile._platform"] = types.ModuleType(
        "kivy.mobile._platform")
    sys.modules["kivy.mobile._platform.android"] = android_module

    # The module under test registers itself with the global provider
    # registry on import, so put the registry back afterwards.
    from kivy.core.audio_output import SoundLoader

    saved_classes = list(SoundLoader._classes)
    saved_by_name = dict(SoundLoader._loaders_by_name)
    _FakeUri.parsed = []

    try:
        spec = importlib.util.spec_from_file_location(
            "audio_android", _MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module
    finally:
        SoundLoader._classes = saved_classes
        SoundLoader._loaders_by_name = saved_by_name
        for name, mod in saved.items():
            if mod is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = mod


class TestSoundAndroidPlayerDataSource:
    URI = "content://media/external/audio/media/42"

    def test_content_uri_uses_the_context_overload(self):
        context = object()

        with _fake_environment(lambda: context) as module:
            player = module.SoundAndroidPlayer(source=self.URI)

        first, second = player._mediaplayer.data_source
        assert first is context
        assert isinstance(second, _FakeUri)
        assert second.value == self.URI
        assert _FakeUri.parsed == [self.URI]

    def test_plain_path_uses_the_string_overload(self):
        with _fake_environment(lambda: object()) as module:
            player = module.SoundAndroidPlayer(source="/sdcard/Music/a.mp3")

        assert player._mediaplayer.data_source == ("/sdcard/Music/a.mp3",)
        assert _FakeUri.parsed == []

    def test_missing_context_raises_with_an_explanation(self):
        with _fake_environment(lambda: None) as module:
            with pytest.raises(RuntimeError, match="content://"):
                module.SoundAndroidPlayer(source=self.URI)
