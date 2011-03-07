'''
Video
=====

You can play video files using Video widget. Depending of your Video core
provider, you may be able to play differents formats. For example, pygame video
provider allow only MPEG1 on Linux and OSX. GStreamer is more versatile, and can
play many other video format, as MKV, OGV, AVI, MOV, FLV... depending of the
gstreamer plugins installed.

The video loading is also asynchronous. Many properties are not available until
the video is loaded. The video is loaded when the texture is created. ::

    def on_position_change(instance, value):
        print 'The initial position in the video is', value
    def on_duration_change(instance, value):
        print 'The duration of the video is', video
    video = Video(source='PandaSneezes.avi')
    video.bind(position=on_position_change,
               duration=on_duration_change)

'''

__all__ = ('Video', )

from kivy.uix.image import Image
from kivy.core.video import Video as CoreVideo
from kivy.resources import resource_find
from kivy.properties import BooleanProperty, NumericProperty


class Video(Image):
    '''Video class. See module documentation for more informations.
    '''

    play = BooleanProperty(False)
    '''Boolean indicate if the video is playing.
    You can start/stop the video by setting this property. ::

        # start the video playing at creation
        video = Video(source='movie.mkv', play=True)

        # create the video, and start later
        video = Video(source='movie.mkv')
        # and later
        video.play = True

    :data:`play` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    eos = BooleanProperty(False)
    '''Boolean indicate if the video is done playing through the end.

    :data:`eos` is a :class:`~kivy.properties.BooleanProperty`, default to
    False.
    '''

    position = NumericProperty(-1)
    '''Position of the video between 0 and :data:`duration`. The position is
    default to -1, and set to real position when the video is loaded.

    :data:`position` is a :class:`~kivy.properties.NumericProperty`, default to
    -1.
    '''

    duration = NumericProperty(-1)
    '''Duration of the video. The duration is default to -1, and set to real
    duration when the video is loaded.

    :data:`duration` is a :class:`~kivy.properties.NumericProperty`, default to
    -1.
    '''

    volume = NumericProperty(1.)
    '''Volume of the video, in the range 0-1. 1 mean full volume, 0 mean mute.

    :data:`volume` is a :class:`~kivy.properties.NumericProperty`, default to
    1.
    '''

    def __init__(self, **kwargs):
        self._video = None
        super(Video, self).__init__(**kwargs)

    def on_source(self, instance, value):
        if self._video:
            self._video.stop()
        if not value:
            self._video = None
            self.texture = None
        else:
            filename = resource_find(value)
            self._video = CoreVideo(filename=filename)
            self._video.bind(on_load=self._on_video_frame,
                             on_frame=self._on_video_frame,
                             on_eos=self._on_eos)
            if self.play:
                self._video.play()
            self.duration = 1.
            self.position = 0.

    def on_play(self, instance, value):
        if not self._video:
            return
        if value:
            if self.eos:
                self._video.stop()
                self._video.position = 0.
                self._video.eos = False
            self._video.play()
        else:
            self._video.stop()

    def _on_video_frame(self, *largs):
        self.duration = self._video.duration
        self.position = self._video.position
        self.texture = self._video.texture
        self.canvas.ask_update()

    def _on_eos(self, *largs):
        self.eos = True

    def on_volume(self, instance, value):
        if self._video:
            self._video.volume = max(value, .0000001)
