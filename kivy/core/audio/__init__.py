'''
Audio
=====

Load an audio sound and play it with::

    from kivy.core.audio import SoundLoader

    sound = SoundLoader.load('mytest.wav')
    if sound:
        print "Sound found at %s" % sound.source
        print "Sound is %.3f seconds" % sound.length
        sound.play()

You should not use directly the sound class yourself. The result will use the
best sound provider for reading the file, so you might have a different Sound
class depending the file.

.. note::

    Recording audio is not supported.

'''

__all__ = ('Sound', 'SoundLoader')

import sys
from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.core import core_register_libs
from kivy.resources import resource_find
from kivy.properties import StringProperty, NumericProperty, OptionProperty, \
        AliasProperty


class SoundLoader:
    '''Load a sound, with usage of the best loader for a given filename.
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
        rfn = resource_find(filename)
        if rfn is not None:
            filename = rfn
        ext = filename.split('.')[-1].lower()
        for classobj in SoundLoader._classes:
            if ext in classobj.extensions():
                return classobj(source=filename)
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

    source = StringProperty(None)
    '''Filename / source of your image.

    .. versionadded:: 1.3.0

    :data:`source` a :class:`~kivy.properties.StringProperty`, default to None,
    read-only. Use the :meth:`SoundLoader.load` for loading audio.
    '''

    volume = NumericProperty(1.)
    '''Volume, in the range 0-1. 1 mean full volume, 0 mean mute.

    .. versionadded:: 1.3.0

    :data:`volume` is a :class:`~kivy.properties.NumericProperty`, default to
    1.
    '''

    state = OptionProperty('stop', options=('stop', 'play'))
    '''State of the sound, one of 'stop' or 'play'

    .. versionadded:: 1.3.0

    :data:`state` is an :class:`~kivy.properties.OptionProperty`, read-only.
    '''

    #
    # deprecated
    #
    def _get_status(self):
        return self.state
    status = AliasProperty(_get_status, None, bind=('state', ))
    '''
    .. deprecated:: 1.3.0
        Use :data:`state` instead
    '''

    def _get_filename(self):
        return self.source
    filename = AliasProperty(_get_filename, None, bind=('source', ))
    '''
    .. deprecated:: 1.3.0
        Use :data:`source` instead
    '''

    def __init__(self, **kwargs):
        self.register_event_type('on_play')
        self.register_event_type('on_stop')
        super(Sound, self).__init__(**kwargs)
        self.bind(volume=lambda _, v: self._set_volume(v))

    def on_source(self, instance, filename):
        self.unload()
        if filename is None:
            return
        self.load()

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
        self.state = 'play'
        self.dispatch('on_play')

    def stop(self):
        '''Stop playback'''
        self.state = 'stop'
        self.dispatch('on_stop')

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
