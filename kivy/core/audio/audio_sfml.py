'''
AudioSFML: implementation of Sound with SFML
'''

""" Todo:
        * error checking
"""
__all__ = ('SoundSFML', )

from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.audio import Sound, SoundLoader

try:
    from sfml.audio import Music, SoundSource
except:
    raise


class SoundSFML(Sound):

    @staticmethod
    def extensions():
        return ('ogg', 'wav', 'flac', 'aiff', 'au', 'raw', 'paf', 'svx',
                'nist', 'voc', 'ircam', 'w64', 'mat4', 'mat5', 'pvf', 'htk',
                'sds', 'avr', 'sd2', 'caf', 'wve', 'mpc2k', 'rf64')

    def __init__(self, **kwargs):
        self._data = None
        super(SoundSFML, self).__init__(**kwargs)

    def load(self):
        if not self.filename:
            return

        self.unload()
        self._data = Music.open_from_file(self.filename)

    def unload(self):
        self.stop()
        self._data = None

    def play(self):
        if not self._data:
            return

        self._data.play()
        super(SoundSFML, self).play()

    def stop(self):
        if not self._data:
            return

        self._data.stop()
        super(SoundSFML, self).stop()

    def _set_volume(self, volume):
        if not self._data:
            return

        self._data.volume = volume * 100

    def _get_volume(self):
        if not self._data:
            return

        return self._data.volume / 100

    def _get_legnth(self):
        if not self._data:
            return

        return self._data.duration

    def _get_status(self):
        if not self._data:
            return

        status = dict(
            SoundSource.PLAYING = 'play',
            SoundSource.PAUSED = 'pause',
            SoundSource.STOPPED = 'stop')

        return status[self._data.status]

SoundLoader.register(SoundSFML)
