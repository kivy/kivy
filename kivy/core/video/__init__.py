'''
Video
=====

Core class for reading video files and managing the
:class:`kivy.graphics.texture.Texture` video.

.. versionchanged:: 1.8.0
    There is now 2 distinct Gstreamer implementation: one using Gi/Gst
    working for both Python 2+3 with Gstreamer 1.0, and one using PyGST
    working only for Python 2 + Gstreamer 0.10.

.. note::

    Recording is not supported.
'''

__all__ = ('VideoBase', 'Video')

from kivy.clock import Clock
from kivy.core import core_select_lib
from kivy.event import EventDispatcher
from kivy.logger import Logger
from kivy.compat import PY2


class VideoBase(EventDispatcher):
    '''VideoBase, a class used to implement a video reader.

    :Parameters:
        `filename`: str
            Filename of the video. Can be a file or an URI.
        `eos`: str, defaults to 'pause'
            Action to take when EOS is hit. Can be one of 'pause', 'stop' or
            'loop'.

            .. versionchanged:: unknown
                added 'pause'

        `async`: bool, defaults to True
            Load the video asynchronously (may be not supported by all
            providers).
        `autoplay`: bool, defaults to False
            Auto play the video on init.

    :Events:
        `on_eos`
            Fired when EOS is hit.
        `on_load`
            Fired when the video is loaded and the texture is available.
        `on_frame`
            Fired when a new frame is written to the texture.
    '''

    __slots__ = ('_wantplay', '_buffer', '_filename', '_texture',
                 '_volume', 'eos', '_state', '_async', '_autoplay')

    __events__ = ('on_eos', 'on_load', 'on_frame')

    def __init__(self, **kwargs):
        kwargs.setdefault('filename', None)
        kwargs.setdefault('eos', 'stop')
        kwargs.setdefault('async', True)
        kwargs.setdefault('autoplay', False)

        super(VideoBase, self).__init__()

        self._wantplay = False
        self._buffer = None
        self._filename = None
        self._texture = None
        self._volume = 1.
        self._state = ''

        self._autoplay = kwargs.get('autoplay')
        self._async = kwargs.get('async')
        self.eos = kwargs.get('eos')
        if self.eos == 'pause':
            Logger.warning("'pause' is deprecated. Use 'stop' instead.")
            self.eos = 'stop'
        self.filename = kwargs.get('filename')

        Clock.schedule_interval(self._update, 1 / 30.)

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

    def seek(self, percent):
        '''Move on percent position'''
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


# Load the appropriate provider
video_providers = []
try:
    from kivy.lib.gstplayer import GstPlayer  # NOQA
    video_providers += [('gstplayer', 'video_gstplayer', 'VideoGstplayer')]
except ImportError:
    #video_providers += [('gi', 'video_gi', 'VideoGi')]
    if PY2:
        # if peoples do not have gi, fallback on pygst, only for python2
        video_providers += [
            ('pygst', 'video_pygst', 'VideoPyGst')]
video_providers += [
    ('ffmpeg', 'video_ffmpeg', 'VideoFFMpeg'),
    ('ffpyplayer', 'video_ffpyplayer', 'VideoFFPy'),
    ('pyglet', 'video_pyglet', 'VideoPyglet'),
    ('null', 'video_null', 'VideoNull')]


Video = core_select_lib('video', video_providers)
