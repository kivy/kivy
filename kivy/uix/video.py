'''
Video
=====

The :class:`Video` widget is used to display video files and streams. Depending
on your Video core provider, platform, and plugins, you will be able to play
different formats. For example, the pygame video provider only supports MPEG1 on
Linux and OSX. GStreamer is more versatile, and can read many video containers
and codecs such as MKV, OGV, AVI, MOV, FLV (if the correct gstreamer plugins
are installed). Our :class:`~kivy.core.video.VideoBase` implementation is used
under the hood.

Video loading is asynchronous - many properties are not available until
the video is loaded (when the texture is created)::

    def on_position_change(instance, value):
        print('The position in the video is', value)
    def on_duration_change(instance, value):
        print('The duration of the video is', video)
    video = Video(source='PandaSneezes.avi')
    video.bind(position=on_position_change,
               duration=on_duration_change)

'''

__all__ = ('Video', )

from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.core.video import Video as CoreVideo
from kivy.resources import resource_find
from kivy.properties import (BooleanProperty, NumericProperty, ObjectProperty,
        OptionProperty)


class Video(Image):
    '''Video class. See module documentation for more information.
    '''

    state = OptionProperty('stop', options=('play', 'pause', 'stop'))
    '''String, indicates whether to play, pause, or stop the video::

        # start playing the video at creation
        video = Video(source='movie.mkv', state='play')

        # create the video, and start later
        video = Video(source='movie.mkv')
        # and later
        video.state = 'play'

    :data:`state` is a :class:`~kivy.properties.OptionProperty`, default to
    'play'.
    '''

    play = BooleanProperty(False)
    '''
    .. deprecated:: 1.4.0
        Use :data:`state` instead.

    Boolean, indicates if the video is playing.
    You can start/stop the video by setting this property::

        # start playing the video at creation
        video = Video(source='movie.mkv', play=True)

        # create the video, and start later
        video = Video(source='movie.mkv')
        # and later
        video.play = True

    :data:`play` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.

    .. deprecated:: 1.4.0
        Use :data:`state` instead.
    '''

    eos = BooleanProperty(False)
    '''Boolean, indicates if the video is done playing (reached end of stream).

    :data:`eos` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    loaded = BooleanProperty(False)
    '''Boolean, indicates if the video is loaded and ready for playback.

    .. versionadded:: 1.6.0

    :data:`loaded` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    position = NumericProperty(-1)
    '''Position of the video between 0 and :data:`duration`. The position
    defaults to -1, and is set to a real position when the video is loaded.

    :data:`position` is a :class:`~kivy.properties.NumericProperty`, default to
    -1.
    '''

    duration = NumericProperty(-1)
    '''Duration of the video. The duration defaults to -1, and is set to a real
    duration when the video is loaded.

    :data:`duration` is a :class:`~kivy.properties.NumericProperty`, default to
    -1.
    '''

    volume = NumericProperty(1.)
    '''Volume of the video, in the range 0-1. 1 means full volume, 0 means mute.

    :data:`volume` is a :class:`~kivy.properties.NumericProperty`, default to
    1.
    '''

    options = ObjectProperty({})
    '''Options to pass at Video core object creation.

    .. versionadded:: 1.0.4

    :data:`options` is a :class:`kivy.properties.ObjectProperty`, default to {}.
    '''

    def __init__(self, **kwargs):
        self._video = None
        super(Image, self).__init__(**kwargs)
        self.bind(source=self._trigger_video_load)

        if self.source:
            self._trigger_video_load()

    def seek(self, percent):
        '''Change the position to a percentage of duration. Percentage must be a
        value between 0-1.

        .. warning::

            Calling seek() before video is loaded has no impact.

        .. versionadded:: 1.2.0
        '''
        if self._video is None:
            raise Exception('Video not loaded.')
        self._video.seek(percent)

    def _trigger_video_load(self, *largs):
        Clock.unschedule(self._do_video_load)
        Clock.schedule_once(self._do_video_load, -1)

    def _do_video_load(self, *largs):
        if CoreVideo is None:
            return
        if self._video:
            self._video.stop()
        if not self.source:
            self._video = None
            self.texture = None
        else:
            filename = self.source
            # Check if filename is not url
            if not '://' in filename:
                filename = resource_find(filename)
            self._video = CoreVideo(filename=filename, **self.options)
            self._video.volume = self.volume
            self._video.bind(on_load=self._on_load,
                             on_frame=self._on_video_frame,
                             on_eos=self._on_eos)
            if self.state == 'play' or self.play:
                self._video.play()
            self.duration = 1.
            self.position = 0.

    def on_play(self, instance, value):
        value = 'play' if value else 'stop'
        return self.on_state(instance, value)

    def on_state(self, instance, value):
        if not self._video:
            return
        if value == 'play':
            if self.eos:
                self._video.stop()
                self._video.position = 0.
                self._video.eos = False
            self.eos = False
            self._video.play()
        elif value == 'pause':
            self._video.pause()
        else:
            self._video.stop()
            self._video.position = 0
            self._video.eos = False

    def _on_video_frame(self, *largs):
        self.duration = self._video.duration
        self.position = self._video.position
        self.texture = self._video.texture
        self.canvas.ask_update()

    def _on_eos(self, *largs):
        if self._video.eos != 'loop':
            self.state = 'stop'
            self.eos = True

    def _on_load(self, *largs):
        self.loaded = True
        self._on_video_frame(largs)

    def on_volume(self, instance, value):
        if self._video:
            self._video.volume = value

if __name__ == '__main__':
    from kivy.app import App
    import sys

    if len(sys.argv) != 2:
        print("usage: %s file" % sys.argv[0])
        sys.exit(1)

    class VideoApp(App):
        def build(self):
            self.v = Video(source=sys.argv[1], state='play')
            self.v.bind(state=self.replay)
            return self.v

        def replay(self, *args):
            if self.v.state == 'stop':
                self.v.state = 'play'

    VideoApp().run()
