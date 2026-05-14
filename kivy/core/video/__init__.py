'''
Video
=====

Core class for reading video files and managing the video
:class:`~kivy.graphics.texture.Texture`.

.. versionchanged:: 3.0.0
    Added native AVFoundation provider for macOS / iOS (default on
    Darwin builds) and extended :class:`VideoBase` with:

      - :meth:`VideoBase.generate_thumbnail` classmethod for creating a
        :class:`~kivy.graphics.texture.Texture` from a frame at a
        given timestamp without instantiating / playing the video.
      - :attr:`VideoBase.buffering` observable boolean that is True
        while playback is delayed/stalled while trying to satisfy
        ``state='play'``, and the :attr:`VideoBase.on_buffering`
        event that fires whenever it changes.
      - :attr:`VideoBase.options` provider-specific options dict so apps
        can pass opaque configuration through to the backend
        implementation. Each provider documents the keys it honors;
        see e.g. :class:`~kivy.core.video.video_avfoundation.VideoAVFoundation`.

.. versionchanged:: 1.10.0
    The pyglet, pygst and gi providers have been removed.

.. versionchanged:: 1.8.0
    There are now 2 distinct Gstreamer implementations: one using Gi/Gst
    working for both Python 2+3 with Gstreamer 1.0, and one using PyGST
    working only for Python 2 + Gstreamer 0.10.

.. note::

    Recording is not supported.
'''

__all__ = ('VideoBase', 'Video')

from kivy.clock import Clock
from kivy.core import core_select_lib, get_provider_modules, make_provider_tuple
from kivy.event import EventDispatcher
from kivy.logger import Logger


class VideoBase(EventDispatcher):
    '''VideoBase, a class used to implement a video reader.

    :Parameters:
        `filename`: str
            Filename of the video. Can be a file or an URI.
        `eos`: str, defaults to 'pause'
            Action to take when EOS is hit. Can be one of 'pause', 'stop' or
            'loop'.

            .. versionchanged:: 1.4.0
                added 'pause'

        `async`: bool, defaults to True
            Load the video asynchronously (may be not supported by all
            providers).
        `autoplay`: bool, defaults to False
            Auto play the video on init.
        `options`: dict, defaults to None
            Provider-specific options forwarded opaquely to the underlying
            implementation. The base class consumes the documented kwargs
            above; any other keys are placed in :attr:`options` for the
            selected provider to consume. Each provider documents the keys
            it honors; for example the AVFoundation provider honors
            ``options={'automatically_waits_to_minimize_stalling': False}``
            for low-latency playback and ``options={'force_cpu_copy': True}``
            to bypass its zero-copy texture path. Keys not recognized by
            the selected provider are typically logged as a warning and
            ignored.

            .. versionadded:: 3.0.0

    :Events:
        `on_eos`
            Fired when EOS is hit.
        `on_load`
            Fired when the video is loaded and the texture is available.
        `on_frame`
            Fired when a new frame is written to the texture.
        `on_buffering`
            Fired when :attr:`buffering` changes. Strictly a transition
            event; the boolean is also readable as a property.

            .. versionadded:: 3.0.0
    '''

    __slots__ = ('_wantplay', '_buffer', '_filename', '_texture',
                 '_volume', 'eos', '_state', '_async', '_autoplay',
                 '_fps', '_options', '_buffering')

    __events__ = ('on_eos', 'on_load', 'on_frame', 'on_buffering')

    def __init__(self, **kwargs):
        kwargs.setdefault('filename', None)
        kwargs.setdefault('eos', 'stop')
        kwargs.setdefault('async', True)
        kwargs.setdefault('autoplay', False)
        kwargs.setdefault('fps', 30)
        kwargs.setdefault('options', None)

        super(VideoBase, self).__init__()

        self._wantplay = False
        self._buffer = None
        self._filename = None
        self._texture = None
        self._volume = 1.
        self._state = ''
        self._buffering = False

        self._autoplay = kwargs.get('autoplay')
        self._async = kwargs.get('async')
        self.eos = kwargs.get('eos')
        self._fps = kwargs.get('fps')
        self._options = dict(kwargs.get('options') or {})
        if self.eos == 'pause':
            Logger.warning("'pause' is deprecated. Use 'stop' instead.")
            self.eos = 'stop'
        self.filename = kwargs.get('filename')

        Clock.schedule_interval(self._update, 1 / self._fps)

        if self._autoplay:
            self.play()

    def __del__(self):
        self.unload()

    def on_eos(self):
        pass

    def on_load(self):
        pass

    def on_frame(self):
        pass

    def on_buffering(self, value):
        '''Fired when :attr:`buffering` transitions.

        `value` is the new buffering state (``True`` or ``False``).

        .. versionadded:: 3.0.0
        '''
        pass

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
                        doc='Get/set the filename/uri of the current video')

    def _get_position(self):
        return 0

    def _set_position(self, pos):
        self.seek(pos)

    position = property(lambda self: self._get_position(),
                        lambda self, x: self._set_position(x),
                        doc='Get/set the position in the video (in seconds)')

    def _get_volume(self):
        return self._volume

    def _set_volume(self, volume):
        self._volume = volume

    volume = property(lambda self: self._get_volume(),
                      lambda self, x: self._set_volume(x),
                      doc='Get/set the volume in the video (1.0 = 100%)')

    def _get_duration(self):
        return 0

    duration = property(lambda self: self._get_duration(),
                        doc='Get the video duration (in seconds)')

    def _get_texture(self):
        return self._texture

    texture = property(lambda self: self._get_texture(),
                       doc='Get the video texture')

    def _get_state(self):
        return self._state

    state = property(lambda self: self._get_state(),
                     doc='Get the video playing status')

    def _get_options(self):
        return self._options

    options = property(lambda self: self._get_options(),
                       doc='Get the provider-specific options dict that was '
                           'passed to the provider at construction time. '
                           'Read-only at the base class level; providers may '
                           'mutate it during their lifetime. '
                           '\n\n.. versionadded:: 3.0.0')

    def _get_buffering(self):
        return self._buffering

    buffering = property(
        lambda self: self._get_buffering(),
        doc='Whether playback is currently delayed/stalled while '
            "trying to satisfy ``state='play'``. Always False while "
            "``state`` is ``'pause'`` or ``'stop'`` (the player is "
            'doing what was asked; there is no delay relative to '
            "intent). ``True`` covers both the initial pre-playback "
            'wait (asset still loading, buffer still filling) and '
            'any mid-stream rebuffer. Providers update this from '
            'their authoritative signal (e.g. AVFoundation\'s '
            '``AVPlayer.timeControlStatus ==`` '
            '``.waitingToPlayAtSpecifiedRate``); providers that '
            'cannot detect stalls leave it ``False``. Apps that '
            'want a loading overlay can use '
            "``not video.loaded or video.buffering`` as the gate."
            '\n\n.. versionadded:: 3.0.0')

    @classmethod
    def generate_thumbnail(cls, filename, time, size=None):
        '''Generate a thumbnail :class:`~kivy.graphics.texture.Texture`
        from the given video file at the given timestamp, without
        requiring playback.

        :Parameters:
            `filename`: str
                Path or URI to the video.
            `time`: float
                Timestamp in seconds at which to grab the thumbnail.
            `size`: tuple of (int, int), optional
                Target ``(width, height)``. When ``None`` the source
                video's native frame size is used.

        :Returns:
            A :class:`~kivy.graphics.texture.Texture` containing the
            decoded frame, or ``None`` if the provider does not support
            thumbnail generation or could not decode the asset at the
            requested time.

        Providers should override this. The default implementation logs
        an informational message and returns ``None``.

        .. versionadded:: 3.0.0
        '''
        Logger.info(
            'VideoBase: generate_thumbnail is not supported by '
            'provider {!r}'.format(cls.__name__))
        return None

    def _do_eos(self, *args):
        '''
        .. versionchanged:: 1.4.0
            Now dispatches the `on_eos` event.
        '''
        if self.eos == 'pause':
            self.pause()
        elif self.eos == 'stop':
            self.stop()
        elif self.eos == 'loop':
            self.position = 0
            self.play()

        self.dispatch('on_eos')

    def _update(self, dt):
        '''Update the video content to texture.
        '''
        pass

    def seek(self, percent, precise=True):
        '''Move to position as percentage (strictly, a proportion from
            0 - 1) of the duration'''
        pass

    def stop(self):
        '''Stop the video playing'''
        self._state = ''

    def pause(self):
        '''Pause the video

        .. versionadded:: 1.4.0
        '''
        self._state = 'paused'

    def play(self):
        '''Play the video'''
        self._state = 'playing'

    def load(self):
        '''Load the video from the current filename'''
        pass

    def unload(self):
        '''Unload the actual video'''
        self._state = ''
        if self._buffering:
            self._buffering = False
            self.dispatch('on_buffering', False)


# Load the appropriate provider
# Build platform-specific list from registry
all_providers = get_provider_modules('video')
video_providers = []

# avfoundation is the default video provider on Darwin (macOS / iOS).
# It is compiled only when c_options['use_avfoundation'] is True in
# setup.py, so the import naturally fails on non-Darwin platforms and
# core_select_lib falls through to gstplayer / ffmpeg / ffpyplayer.
video_providers.append(make_provider_tuple(
    'avfoundation', all_providers, 'VideoAVFoundation'
))

try:
    from kivy.lib.gstplayer import GstPlayer  # NOQA
    video_providers.append(make_provider_tuple(
        'gstplayer', all_providers, 'VideoGstplayer'
    ))
except ImportError:
    pass

video_providers.append(make_provider_tuple('ffmpeg', all_providers, 'VideoFFMpeg'))
video_providers.append(make_provider_tuple('ffpyplayer', all_providers, 'VideoFFPy'))
video_providers.append(make_provider_tuple('null', all_providers, 'VideoNull'))

Video: VideoBase = core_select_lib('video', video_providers)
