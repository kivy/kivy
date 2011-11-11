'''
Audio
=====

Core class for loading and play sound.

.. note::

    Recording audio is not supported.

'''

__all__ = ('Sound', 'SoundLoader')

import sys
from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.core import core_register_libs


class SoundLoader:
    '''Load a sound, with usage of the best loader for a given filename.
    If you want to load an audio file ::

        sound = SoundLoader.load(filename='test.wav')
        if not sound:
            # unable to load this sound ?
            pass
        else:
            # sound loaded, let's play!
            sound.play()

    '''

    _classes = []

    @staticmethod
    def register(classobj):
        '''Register a new class to load sound'''
        Logger.debug('Audio: register %s' % classobj.__name__)
        SoundLoader._classes.append(classobj)

    @staticmethod
    def load(filename):
        '''Load a sound, and return a Sound() instance'''
        ext = filename.split('.')[-1].lower()
        for classobj in SoundLoader._classes:
            if ext in classobj.extensions():
                return classobj(filename=filename)
        Logger.warning('Audio: Unable to found a loader for <%s>' %
                       filename)
        return None


class Sound(EventDispatcher):
    '''Represent a sound to play. This class is abstract, and cannot be used
    directly.
    Use SoundLoader to load a sound !

    :Events:
        `on_play` : None
            Fired when the sound is played
        `on_stop` : None
            Fired when the sound is stopped
    '''

    __slots__ = ('_filename', '_volume', '_status')

    def __init__(self, **kwargs):
        kwargs.setdefault('filename', None)
        kwargs.setdefault('volume', 1.)

        self.register_event_type('on_play')
        self.register_event_type('on_stop')

        super(Sound, self).__init__()

        self._status = 'stop'
        self._volume = kwargs.get('volume')
        self._filename = kwargs.get('filename')
        self.load()

    def _get_filename(self):
        return self._filename

    def _set_filename(self, filename):
        if filename == self._filename:
            return
        self.unload()
        self._filename = filename
        if self._filename is None:
            return
        self.load()

    filename = property(lambda self: self._get_filename(),
            lambda self, x: self._set_filename(x),
            doc='Get/set the filename/uri of the sound')

    def _get_volume(self):
        return self._volume

    def _set_volume(self, volume):
        if self._volume == volume:
            return
        self._volume = volume

    volume = property(lambda self: self._get_volume(),
            lambda self, x: self._set_volume(x),
            doc='Get/set the volume of the sound')

    def _get_status(self):
        return self._status

    def _set_status(self, x):
        # this function must not be available for user
        if self._status == x:
            return
        self._status = x
        if x == 'stop':
            self.dispatch('on_stop')
        elif x == 'play':
            self.dispatch('on_play')
        else:
            assert('unknown status %s' % x)

    status = property(_get_status,
            doc='Get the status of the sound (stop, play)')

    def _get_length(self):
        return 0

    length = property(lambda self: self._get_length(),
            doc='Get length of the sound (in seconds)')

    def load(self):
        '''Load the file into memory'''
        pass

    def unload(self):
        '''Unload the file from memory'''
        pass

    def play(self):
        '''Play the file'''
        self._set_status('play')

    def stop(self):
        '''Stop playback'''
        self._set_status('stop')

    def seek(self, position):
        '''Seek to the <position> (in seconds)'''
        pass

    def on_play(self):
        pass

    def on_stop(self):
        pass


# Little trick here, don't activate gstreamer on window
# seem to have lot of crackle or something...
# XXX test in macosx
audio_libs = []
if sys.platform not in ('win32', 'cygwin'):
    audio_libs += [('gstreamer', 'audio_gstreamer')]
audio_libs += [('pygame', 'audio_pygame')]

core_register_libs('audio', audio_libs)
