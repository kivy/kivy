"""
AudioAndroid: Kivy audio implementation for Android using native API
"""

__all__ = ("SoundAndroidPlayer", )

from jnius import autoclass
from kivy.core.audio import Sound, SoundLoader


MediaPlayer = autoclass("android.media.MediaPlayer")
AudioManager = autoclass("android.media.AudioManager")


class SoundAndroidPlayer(Sound):
    @staticmethod
    def extensions():
        return ("mp3", "mp4", "aac", "3gp", "flac", "mkv", "wav", "ogg", "m4a")

    def __init__(self, **kwargs):
        self._mediaplayer = None
        super(SoundAndroidPlayer, self).__init__(**kwargs)

    def load(self):
        self.unload()
        self._mediaplayer = MediaPlayer()
        self._mediaplayer.setAudioStreamType(AudioManager.STREAM_MUSIC);
        self._mediaplayer.setDataSource(self.source)
        self._mediaplayer.prepare()

    def unload(self):
        if self._mediaplayer:
            self._mediaplayer.reset()
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

    def _get_length(self):
        if self._mediaplayer:
            return self._mediaplayer.getDuration() / 1000.
        return super(SoundAndroidPlayer, self)._get_length()


SoundLoader.register(SoundAndroidPlayer)
