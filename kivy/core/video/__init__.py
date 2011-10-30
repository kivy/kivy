'''
Video
=====

Core class for reading video file and manage the
:class:`kivy.graphics.texture.Texture` video.

.. note::

    Recording is not supported.
'''

__all__ = ('VideoBase', 'Video')

from kivy.clock import Clock
from kivy.core import core_select_lib
from kivy.event import EventDispatcher


class VideoBase(EventDispatcher):
    '''VideoBase, a class to implement a video reader.

    :Parameters:
        `filename` : str
            Filename of the video. Can be a file or an URI.
        `eos` : str, default to 'pause'
            Action to do when EOS is hit. Can be one of 'pause' or 'loop'
        `async` : bool, default to True
            Asynchronous loading (may be not supported by all providers)
        `autoplay` : bool, default to False
            Auto play the video at init

    :Events:
        `on_eos`
            Fired when EOS is hit
        `on_load`
            Fired when the video is loaded, texture is available
        `on_frame`
            Fired when a new frame is written on texture
    '''

    __slots__ = ('_wantplay', '_buffer', '_filename', '_texture',
                 '_volume', 'eos', '_state', '_async', '_autoplay',
                 '__weakref__')

    def __init__(self, **kwargs):
        kwargs.setdefault('filename', None)
        kwargs.setdefault('eos', 'pause')
        kwargs.setdefault('async', True)
        kwargs.setdefault('autoplay', False)

        self.register_event_type('on_eos')
        self.register_event_type('on_load')
        self.register_event_type('on_frame')

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
            doc='Get/set the filename/uri of current video')

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

    def _do_eos(self):
        if self.eos == 'pause':
            self.stop()
        elif self.eos == 'loop':
            self.stop()
            self.play()

    def _update(self):
        '''Update the video content to texture.
        '''
        pass

    def seek(self, percent):
        '''Move on percent position'''
        pass

    def stop(self):
        '''Stop the video playing'''
        self._state = ''

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
Video = core_select_lib('video', (
    ('gstreamer', 'video_gstreamer', 'VideoGStreamer'),
    ('ffmpeg', 'video_ffmpeg', 'VideoFFMpeg'),
    ('pyglet', 'video_pyglet', 'VideoPyglet'),
))

