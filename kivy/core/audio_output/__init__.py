'''
Audio Output
=====

Load an audio sound and play it with::

    from kivy.core.audio_output import SoundLoader

    sound = SoundLoader.load('mytest.wav')
    if sound:
        print("Sound found at %s" % sound.source)
        print("Sound is %.3f seconds" % sound.length)
        sound.play()

You should not use the Sound class directly. The class returned by
:func:`SoundLoader.load` will be the best sound provider for that particular
file type, so it might return different Sound classes depending the file type.

Event dispatching and state changes
-----------------------------------

Audio is often processed in parallel to your code. This means you often need to
enter the Kivy :func:`eventloop <kivy.base.EventLoopBase>` in order to allow
events and state changes to be dispatched correctly.

You seldom need to worry about this as Kivy apps typically always
require this event loop for the GUI to remain responsive, but it is good to
keep this in mind when debugging or running in a
`REPL <https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop>`_
(Read-eval-print loop).

.. versionchanged:: 1.10.0
    The pygst and gi providers have been removed.

.. versionchanged:: 1.8.0
    There are now 2 distinct Gstreamer implementations: one using Gi/Gst
    working for both Python 2+3 with Gstreamer 1.0, and one using PyGST
    working only for Python 2 + Gstreamer 0.10.

.. note::

    The core audio library does not support recording audio. If you require
    this functionality, please refer to the
    `audiostream <https://github.com/kivy/audiostream>`_ extension.

Provider selection
------------------

.. versionadded:: 3.0.0

By default, Kivy automatically selects an audio provider based on platform
defaults and file type. You can override this to use a specific provider.

Querying available providers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To see which providers are available on your system::

    from kivy.core.audio_output import SoundLoader
    print(SoundLoader.available_providers())  # e.g., ['sdl3', 'ffpyplayer']

Using ``audio_output_provider`` parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Specify a provider when loading a sound::

    from kivy.core.audio_output import SoundLoader

    # Load with SDL3 provider
    sound = SoundLoader.load('music.mp3', audio_output_provider='sdl3')

    # Load with ffpyplayer provider
    sound = SoundLoader.load('music.mp3', audio_output_provider='ffpyplayer')

Strict mode
~~~~~~~~~~~

By default, if a requested provider is unavailable or fails, Kivy logs a warning
and falls back to other providers. Enable strict mode to raise exceptions instead::

    import os
    os.environ['KIVY_PROVIDER_STRICT'] = '1'
    import kivy

In strict mode:

- Invalid provider names raise ``ValueError``
- Provider load failures raise ``Exception``
- No fallback to other providers occurs

This is useful during development to catch configuration errors immediately.

'''

__all__ = ('Sound', 'SoundLoader')

import os

from kivy.logger import Logger
from kivy.event import EventDispatcher
from kivy.core import core_register_libs, load_with_provider_selection, \
    get_provider_modules, make_provider_tuple
from kivy.resources import resource_find
from kivy.properties import StringProperty, NumericProperty, OptionProperty, \
    AliasProperty, BooleanProperty, BoundedNumericProperty
from kivy.utils import platform
from kivy.setupconfig import USE_SDL3

from sys import float_info


class SoundLoader:
    '''Load a sound, using the best loader for the given file type.
    '''

    _classes = []
    _loaders_by_name = {}  # O(1) lookup by provider name

    @staticmethod
    def register(classobj):
        '''Register a new class to load the sound.'''
        Logger.debug('Audio: register %s' % classobj.__name__)

        # Require explicit _provider_name attribute (validate BEFORE adding to list)
        name = getattr(classobj, '_provider_name', None)
        if name is None:
            raise ValueError(
                f'{classobj.__name__} must define a _provider_name class attribute'
            )

        SoundLoader._classes.append(classobj)
        SoundLoader._loaders_by_name[name.lower()] = classobj

    @staticmethod
    def available_providers():
        '''Return a list of available audio provider names.

        The returned names can be used with the ``audio_provider`` parameter.

        .. versionadded:: 3.0.0

        :returns: List of provider name strings (e.g., ['sdl3', 'ffpyplayer'])
        '''
        return list(SoundLoader._loaders_by_name.keys())

    @staticmethod
    def load(filename, audio_output_provider=None) -> "Sound":
        '''Load a sound, and return a Sound() instance.

        :param filename: Path to the audio file to load.
        :param audio_output_provider: Optional provider name (e.g., 'sdl3',
            'ffpyplayer'). If specified, only that provider will be used. Use
            :meth:`available_providers` to get a list of available providers.

            .. versionadded:: 3.0.0

        :returns: A Sound instance, or None if no loader could handle the file.
        :raises ValueError: If ``audio_output_provider`` is specified but not
            found or doesn't support the file format (when KIVY_PROVIDER_STRICT=1).
        '''
        rfn = resource_find(filename)
        if rfn is not None:
            filename = rfn
        ext = filename.split('.')[-1].lower()
        if '?' in ext:
            ext = ext.split('?')[0]

        def check_compatibility(provider_class, extension):
            """Check if provider supports the given extension."""
            return extension in provider_class.extensions()

        def try_load(provider_class, fname):
            """Try to load sound with the given provider."""
            try:
                return provider_class(source=fname)
            except Exception:
                return None

        def fallback_load():
            """Load using default provider priority."""
            for classobj in SoundLoader._classes:
                if ext in classobj.extensions():
                    try:
                        return classobj(source=filename)
                    except Exception:
                        continue
            Logger.warning('Audio: Unable to find a loader for <%s>' % filename)
            return None

        return load_with_provider_selection(
            filename=filename,
            extension=ext,
            provider_name=audio_output_provider,
            providers_by_name=SoundLoader._loaders_by_name,
            category_name='Audio',
            check_compatibility=check_compatibility,
            try_load=try_load,
            fallback_load=fallback_load
        )


class Sound(EventDispatcher):
    '''Represents a sound to play. This class is abstract, and cannot be used
    directly.

    Use SoundLoader to load a sound.

    :Events:
        `on_play`: None
            Fired when the sound is played.
        `on_stop`: None
            Fired when the sound is stopped.
    '''

    _provider_name = None
    # Internal provider name used for registration.

    # This must be set by provider implementations. Use
    # :meth:`SoundLoader.available_providers` to query available provider names.

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

    pitch = BoundedNumericProperty(1., min=float_info.epsilon)
    '''Pitch of a sound. 2 is an octave higher, .5 one below. This is only
    implemented for SDL3 audio provider yet.

    .. versionadded:: 1.10.0

    :attr:`pitch` is a :class:`~kivy.properties.NumericProperty` and defaults
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
        '''Go to the <position> (in seconds).

        .. note::
            Most sound providers cannot seek when the audio is stopped.
            Play then seek.
        '''
        pass

    def on_play(self):
        pass

    def on_stop(self):
        pass


# Little trick here, don't activate gstreamer on window
# seem to have lot of crackle or something...

# Build platform-specific list from registry
all_providers = get_provider_modules('audio_output')
audio_libs = []

if platform == 'android':
    audio_libs.append(make_provider_tuple('android', all_providers))
elif platform in ('macosx', 'ios'):
    audio_libs.append(make_provider_tuple('avplayer', all_providers))

try:
    from kivy.lib.gstplayer import GstPlayer  # NOQA
    audio_libs.append(make_provider_tuple('gstplayer', all_providers))
except ImportError:
    pass

audio_libs.append(make_provider_tuple('ffpyplayer', all_providers))

if USE_SDL3:
    audio_libs.append(make_provider_tuple('sdl3', all_providers))

libs_loaded = core_register_libs('audio_output', audio_libs)
