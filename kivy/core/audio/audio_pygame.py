'''
AudioPygame: implementation of Sound with Pygame
'''

__all__ = ('SoundPygame', )

from kivy.clock import Clock
from kivy.utils import platform
from . import Sound, SoundLoader

try:
    if platform() == 'android':
        mixer = __import__('android_mixer')
    else:
        mixer = __import__('pygame.mixer')
except:
    raise

# init pygame sound
mixer.pre_init(44100, -16, 2, 1024)
mixer.init()
mixer.set_num_channels(32)


class SoundPygame(Sound):

    # XXX we don't set __slots__ here, to automaticly add
    # a dictionnary. We need that to be able to use weakref for
    # SoundPygame object. Otherwise, it failed with:
    # TypeError: cannot create weak reference to 'SoundPygame' object
    # We use our clock in play() method.
    # __slots__ = ('_data', '_channel')
    @staticmethod
    def extensions():
        return ('wav', 'ogg', )

    def __init__(self, **kwargs):
        self._data = None
        self._channel = None
        super(SoundPygame, self).__init__(**kwargs)

    def _check_play(self, dt):
        if self._channel is None:
            return False
        if self._channel.get_busy():
            return
        self.stop()
        return False

    def play(self):
        if not self._data:
            return
        self._channel = self._data.play()
        # schedule event to check if the sound is still playing or not
        Clock.schedule_interval(self._check_play, 0.1)
        super(SoundPygame, self).play()

    def stop(self):
        if not self._data:
            return
        self._data.stop()
        # ensure we don't have anymore the callback
        Clock.unschedule(self._check_play)
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
        # Unable to seek in pygame...
        pass

    def _get_volume(self):
        if self._data is not None:
            self._volume = self._data.get_volume()
        return super(SoundPygame, self)._get_volume()

    def _set_volume(self, volume):
        if self._data is not None:
            self._data.set_volume(volume)
        return super(SoundPygame, self)._set_volume(volume)

SoundLoader.register(SoundPygame)
