'''
AudioPygame: implementation of Sound with Pygame

.. warning::

    Pygame has been deprecated and will be removed in the release after Kivy
    1.11.0.
'''

__all__ = ('SoundPygame', )

from kivy.clock import Clock
from kivy.utils import platform, deprecated
from kivy.core.audio import Sound, SoundLoader

_platform = platform
try:
    if _platform == 'android':
        try:
            import android.mixer as mixer
        except ImportError:
            # old python-for-android version
            import android_mixer as mixer
    else:
        from pygame import mixer
except:
    raise

# init pygame sound
mixer.pre_init(44100, -16, 2, 1024)
mixer.init()
mixer.set_num_channels(32)


class SoundPygame(Sound):

    # XXX we don't set __slots__ here, to automatically add
    # a dictionary. We need that to be able to use weakref for
    # SoundPygame object. Otherwise, it failed with:
    # TypeError: cannot create weak reference to 'SoundPygame' object
    # We use our clock in play() method.
    # __slots__ = ('_data', '_channel')
    _check_play_ev = None

    @staticmethod
    def extensions():
        if _platform == 'android':
            return ('wav', 'ogg', 'mp3', 'm4a')
        return ('wav', 'ogg')

    @deprecated(
        msg='Pygame has been deprecated and will be removed after 1.11.0')
    def __init__(self, **kwargs):
        self._data = None
        self._channel = None
        super(SoundPygame, self).__init__(**kwargs)

    def _check_play(self, dt):
        if self._channel is None:
            return False
        if self._channel.get_busy():
            return
        if self.loop:
            def do_loop(dt):
                self.play()
            Clock.schedule_once(do_loop)
        else:
            self.stop()
        return False

    def play(self):
        if not self._data:
            return
        self._data.set_volume(self.volume)
        self._channel = self._data.play()
        self.start_time = Clock.time()
        # schedule event to check if the sound is still playing or not
        self._check_play_ev = Clock.schedule_interval(self._check_play, 0.1)
        super(SoundPygame, self).play()

    def stop(self):
        if not self._data:
            return
        self._data.stop()
        # ensure we don't have anymore the callback
        if self._check_play_ev is not None:
            self._check_play_ev.cancel()
            self._check_play_ev = None
        self._channel = None
        super(SoundPygame, self).stop()

    def load(self):
        self.unload()
        if self.filename is None:
            return
        self._data = mixer.Sound(self.filename)

    def unload(self):
        self.stop()
        self._data = None

    def seek(self, position):
        if not self._data:
            return
        if _platform == 'android' and self._channel:
            self._channel.seek(position)

    def get_pos(self):
        if self._data is not None and self._channel:
            if _platform == 'android':
                return self._channel.get_pos()
            return Clock.time() - self.start_time
        return 0

    def on_volume(self, instance, volume):
        if self._data is not None:
            self._data.set_volume(volume)

    def _get_length(self):
        if _platform == 'android' and self._channel:
            return self._channel.get_length()
        if self._data is not None:
            return self._data.get_length()
        return super(SoundPygame, self)._get_length()


SoundLoader.register(SoundPygame)
