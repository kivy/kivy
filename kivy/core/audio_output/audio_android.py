"""
AudioAndroid: Kivy audio implementation for Android using native API
"""

__all__ = ("SoundAndroidPlayer", )

from jnius import autoclass, java_method, PythonJavaClass
from kivy.core.audio_output import Sound, SoundLoader
from kivy.logger import Logger
from kivy.mobile._platform.android import get_app_context

api_version = autoclass("android.os.Build$VERSION").SDK_INT

MediaPlayer = autoclass("android.media.MediaPlayer")
AudioManager = autoclass("android.media.AudioManager")
Uri = autoclass("android.net.Uri")
if api_version >= 21:
    AudioAttributesBuilder = autoclass("android.media.AudioAttributes$Builder")


class OnCompletionListener(PythonJavaClass):
    __javainterfaces__ = ["android/media/MediaPlayer$OnCompletionListener"]
    __javacontext__ = "app"

    def __init__(self, callback, **kwargs):
        super(OnCompletionListener, self).__init__(**kwargs)
        self.callback = callback

    @java_method("(Landroid/media/MediaPlayer;)V")
    def onCompletion(self, mp):
        self.callback()


class SoundAndroidPlayer(Sound):
    _provider_name = 'android'

    @staticmethod
    def extensions():
        return ("mp3", "mp4", "aac", "3gp", "flac", "mkv", "wav", "ogg", "m4a",
                "gsm", "mid", "xmf", "mxmf", "rtttl", "rtx", "ota", "imy")

    def __init__(self, **kwargs):
        self._mediaplayer = None
        self._completion_listener = None
        super(SoundAndroidPlayer, self).__init__(**kwargs)

    def load(self):
        self.unload()
        context = None
        if self.source.startswith("content://"):
            context = get_app_context()
            if context is None:
                message = (
                    "AudioAndroid: cannot load <%s>: content:// URIs need an "
                    "Android Context, and none is available (no Activity and "
                    "the bootstrap exposes no get_context())." % self.source
                )
                Logger.error(message)
                raise RuntimeError(message)

        self._mediaplayer = MediaPlayer()
        if api_version >= 21:
            self._mediaplayer.setAudioAttributes(
                AudioAttributesBuilder()
                .setLegacyStreamType(AudioManager.STREAM_MUSIC)
                .build())
        else:
            self._mediaplayer.setAudioStreamType(AudioManager.STREAM_MUSIC)

        if context is not None:
            self._mediaplayer.setDataSource(context, Uri.parse(self.source))
        else:
            self._mediaplayer.setDataSource(self.source)
        self._completion_listener = OnCompletionListener(
            self._completion_callback
        )
        self._mediaplayer.setOnCompletionListener(self._completion_listener)
        self._mediaplayer.prepare()

    def unload(self):
        if self._mediaplayer:
            self._mediaplayer.release()
            self._mediaplayer = None

    def play(self):
        if not self._mediaplayer:
            return
        self._mediaplayer.start()
        super(SoundAndroidPlayer, self).play()

    def stop(self):
        if not self._mediaplayer:
            return
        self._mediaplayer.stop()
        self._mediaplayer.prepare()

    def seek(self, position):
        if not self._mediaplayer:
            return
        self._mediaplayer.seekTo(float(position) * 1000)

    def get_pos(self):
        if self._mediaplayer:
            return self._mediaplayer.getCurrentPosition() / 1000.
        return super(SoundAndroidPlayer, self).get_pos()

    def on_volume(self, instance, volume):
        if self._mediaplayer:
            volume = float(volume)
            self._mediaplayer.setVolume(volume, volume)

    def _completion_callback(self):
        super(SoundAndroidPlayer, self).stop()

    def _get_length(self):
        if self._mediaplayer:
            return self._mediaplayer.getDuration() / 1000.
        return super(SoundAndroidPlayer, self)._get_length()

    def on_loop(self, instance, loop):
        if self._mediaplayer:
            self._mediaplayer.setLooping(loop)


SoundLoader.register(SoundAndroidPlayer)
