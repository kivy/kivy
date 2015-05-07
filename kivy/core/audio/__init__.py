'''
Audio
=====

Load an audio sound and play it with::

    from kivy.core.audio import SoundLoader

    sound = SoundLoader.load('mytest.wav')
    if sound:
        print("Sound found at %s" % sound.source)
        print("Sound is %.3f seconds" % sound.length)
        sound.play()

You should not use the Sound class directly. The class returned by
**SoundLoader.load** will be the best sound provider for that particular file
type, so it might return different Sound classes depending the file type.

.. versionchanged:: 1.8.0
    There are now 2 distinct Gstreamer implementations: one using Gi/Gst working
    for both Python 2+3 with Gstreamer 1.0, and one using PyGST working
    only for Python 2 + Gstreamer 0.10.
    If you have issue with GStreamer, have a look at
    :ref:`gstreamer-compatibility`

.. note::

    The core audio library does not support recording audio. If you require
    this functionality, please refer to the
    `audiostream <https://github.com/kivy/audiostream>`_ extension.

'''

__all__ = ('Sound', 'SoundLoader')

from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.core import core_register_libs
from kivy.compat import PY2
from kivy.resources import resource_find
from kivy.properties import StringProperty, NumericProperty, OptionProperty, \
    AliasProperty, BooleanProperty
from kivy.utils import platform
from kivy.setupconfig import USE_SDL2


class SoundLoader:
    '''Load a sound, using the best loader for the given file type.
    '''

    _classes = []

    @staticmethod
    def register(classobj):
        '''Register a new class to load the sound.'''
        Logger.debug('Audio: register %s' % classobj.__name__)
        SoundLoader._classes.append(classobj)

    @staticmethod
    def load(filename):
        '''Load a sound, and return a Sound() instance.'''
        rfn = resource_find(filename)
        if rfn is not None:
            filename = rfn
        ext = filename.split('.')[-1].lower()
        if '?' in ext:
            ext = ext.split('?')[0]
        for classobj in SoundLoader._classes:
            if ext in classobj.extensions():
                return classobj(source=filename)
        Logger.warning('Audio: Unable to find a loader for <%s>' %
                       filename)
        return None


class Sound(EventDispatcher):
    '''Represents a sound to play. This class is abstract, and cannot be used
    directly.

    Use SoundLoader to load a sound.

    :Events:
        `on_play` : None
            Fired when the sound is played.
        `on_stop` : None
            Fired when the sound is stopped.
    '''

    source = StringProperty(None)
    '''Filename / source of your audio file.

    .. versionadded:: 1.3.0

    :attr:`source` is a :class:`~kivy.properties.StringProperty` that defaults
    to None and is read-only. Use the :meth:`SoundLoader.load` for loading
    audio.
    '''

    volume = NumericProperty(1.)
    '''Volume, in the range 0-1. 1 means full volume, 0 means mute.

    .. versionadded:: 1.3.0

    :attr:`volume` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 1.
    '''

    state = OptionProperty('stop', options=('stop', 'play'))
    '''State of the sound, one of 'stop' or 'play'.

    .. versionadded:: 1.3.0

    :attr:`state` is a read-only :class:`~kivy.properties.OptionProperty`.'''

    loop = BooleanProperty(False)
    '''Set to True if the sound should automatically loop when it finishes.

    .. versionadded:: 1.8.0

    :attr:`loop` is a :class:`~kivy.properties.BooleanProperty` and defaults to
    False.'''

    #
    # deprecated
    #
    def _get_status(self):
        return self.state
    status = AliasProperty(_get_status, None, bind=('state', ))
    '''
    .. deprecated:: 1.3.0
        Use :attr:`state` instead.
    '''

    def _get_filename(self):
        return self.source
    filename = AliasProperty(_get_filename, None, bind=('source', ))
    '''
    .. deprecated:: 1.3.0
        Use :attr:`source` instead.
    '''

    __events__ = ('on_play', 'on_stop')

    def on_source(self, instance, filename):
        self.unload()
        if filename is None:
            return
        self.load()

    def get_pos(self):
        '''
        Returns the current position of the audio file.
        Returns 0 if not playing.

        .. versionadded:: 1.4.1
        '''
        return 0

    def _get_length(self):
        return 0

    length = property(lambda self: self._get_length(),
                      doc='Get length of the sound (in seconds).')

    def load(self):
        '''Load the file into memory.'''
        pass

    def unload(self):
        '''Unload the file from memory.'''
        pass

    def play(self):
        '''Play the file.'''
        self.state = 'play'
        self.dispatch('on_play')

    def stop(self):
        '''Stop playback.'''
        self.state = 'stop'
        self.dispatch('on_stop')

    def seek(self, position):
        '''Go to the <position> (in seconds).'''
        pass

    def on_play(self):
        pass

    def on_stop(self):
        pass


# Little trick here, don't activate gstreamer on window
# seem to have lot of crackle or something...
audio_libs = []
if platform in ('macosx', 'ios'):
    audio_libs += [('avplayer', 'audio_avplayer')]
# from now on, prefer our gstplayer instead of gi/pygst.
try:
    from kivy.lib.gstplayer import GstPlayer  # NOQA
    audio_libs += [('gstplayer', 'audio_gstplayer')]
except ImportError:
    #audio_libs += [('gi', 'audio_gi')]
    if PY2:
        audio_libs += [('pygst', 'audio_pygst')]
audio_libs += [('ffpyplayer', 'audio_ffpyplayer')]
if USE_SDL2:
    audio_libs += [('sdl2', 'audio_sdl2')]
else:
    audio_libs += [('pygame', 'audio_pygame')]

core_register_libs('audio', audio_libs)
