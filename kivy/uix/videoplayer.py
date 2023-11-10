'''
Video player
============

.. versionadded:: 1.2.0

The video player widget can be used to play video and let the user control the
play/pausing, volume and position. The widget cannot be customized much because
of the complex assembly of numerous base widgets.

.. image:: images/videoplayer.jpg
    :align: center

Annotations
-----------

If you want to display text at a specific time and for a certain duration,
consider annotations. An annotation file has a ".jsa" extension. The player
will automatically load the associated annotation file if it exists.

An annotation file is JSON-based, providing a list of label dictionary items.
The key and value must match one of the :class:`VideoPlayerAnnotation` items.
For example, here is a short version of a jsa file that you can find in
`examples/widgets/cityCC0.jsa`::


    [
        {"start": 0, "duration": 2,
        "text": "This is an example of annotation"},
        {"start": 2, "duration": 2,
        "bgcolor": [0.5, 0.2, 0.4, 0.5],
        "text": "You can change the background color"}
    ]

For our cityCC0.mpg example, the result will be:

.. image:: images/videoplayer-annotation.jpg
    :align: center

If you want to experiment with annotation files, test with::

    python -m kivy.uix.videoplayer examples/widgets/cityCC0.mpg

Fullscreen
----------

The video player can play the video in fullscreen, if
:attr:`VideoPlayer.allow_fullscreen` is activated by a double-tap on
the video. By default, if the video is smaller than the Window, it will be not
stretched.

You can allow stretching by passing custom options to a
:class:`VideoPlayer` instance::

    player = VideoPlayer(source='myvideo.avi', state='play',
        options={'fit_mode': 'contain'})

End-of-stream behavior
----------------------

You can specify what happens when the video has finished playing by passing an
`eos` (end of stream) directive to the underlying
:class:`~kivy.core.video.VideoBase` class. `eos` can be one of 'stop', 'pause'
or 'loop' and defaults to 'stop'. For example, in order to loop the video::

    player = VideoPlayer(source='myvideo.avi', state='play',
        options={'eos': 'loop'})

.. note::

    The `eos` property of the VideoBase class is a string specifying the
    end-of-stream behavior. This property differs from the `eos`
    properties of the :class:`VideoPlayer` and
    :class:`~kivy.uix.video.Video` classes, whose `eos`
    property is simply a boolean indicating that the end of the file has
    been reached.

'''

__all__ = ('VideoPlayer', 'VideoPlayerAnnotation')

from json import load
from os.path import exists
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty, \
    NumericProperty, DictProperty, OptionProperty
from kivy.animation import Animation
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.label import Label
from kivy.uix.video import Video
from kivy.uix.video import Image
from kivy.factory import Factory
from kivy.logger import Logger
from kivy.clock import Clock


class VideoPlayerVolume(Image):
    video = ObjectProperty(None)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        touch.grab(self)
        # save the current volume and delta to it
        touch.ud[self.uid] = [self.video.volume, 0]
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return
        # calculate delta
        dy = abs(touch.y - touch.oy)
        if dy > 10:
            dy = min(dy - 10, 100)
            touch.ud[self.uid][1] = dy
            self.video.volume = dy / 100.
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        dy = abs(touch.y - touch.oy)
        if dy < 10:
            if self.video.volume > 0:
                self.video.volume = 0
            else:
                self.video.volume = 1.


class VideoPlayerPlayPause(Image):
    video = ObjectProperty(None)

    def on_touch_down(self, touch):
        '''.. versionchanged:: 1.4.0'''
        if self.collide_point(*touch.pos):
            if self.video.state == 'play':
                self.video.state = 'pause'
            else:
                self.video.state = 'play'
            return True


class VideoPlayerStop(Image):
    video = ObjectProperty(None)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.video.state = 'stop'
            self.video.position = 0
            return True


class VideoPlayerProgressBar(ProgressBar):
    video = ObjectProperty(None)
    seek = NumericProperty(None, allownone=True)
    alpha = NumericProperty(1.)

    def __init__(self, **kwargs):
        super(VideoPlayerProgressBar, self).__init__(**kwargs)
        self.bubble = Factory.Bubble(size=(50, 44))
        self.bubble_label = Factory.Label(text='0:00')
        self.bubble.add_widget(self.bubble_label)
        self.add_widget(self.bubble)

        update = self._update_bubble
        fbind = self.fbind
        fbind('pos', update)
        fbind('size', update)
        fbind('seek', update)

    def on_video(self, instance, value):
        self.video.bind(position=self._update_bubble,
                        state=self._showhide_bubble)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return
        self._show_bubble()
        touch.grab(self)
        self._update_seek(touch.x)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return
        self._update_seek(touch.x)
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return
        touch.ungrab(self)
        if self.seek:
            self.video.seek(self.seek)
        self.seek = None
        self._hide_bubble()
        return True

    def _update_seek(self, x):
        if self.width == 0:
            return
        x = max(self.x, min(self.right, x)) - self.x
        self.seek = x / float(self.width)

    def _show_bubble(self):
        self.alpha = 1
        Animation.stop_all(self, 'alpha')

    def _hide_bubble(self):
        self.alpha = 1.
        Animation(alpha=0, d=4, t='in_out_expo').start(self)

    def on_alpha(self, instance, value):
        self.bubble.background_color = (1, 1, 1, value)
        self.bubble_label.color = (1, 1, 1, value)

    def _update_bubble(self, *l):
        seek = self.seek
        if self.seek is None:
            if self.video.duration == 0:
                seek = 0
            else:
                seek = self.video.position / self.video.duration
        # convert to minutes:seconds
        d = self.video.duration * seek
        minutes = int(d / 60)
        seconds = int(d - (minutes * 60))
        # fix bubble label & position
        self.bubble_label.text = '%d:%02d' % (minutes, seconds)
        self.bubble.center_x = self.x + seek * self.width
        self.bubble.y = self.top

    def _showhide_bubble(self, instance, value):
        if value == 'play':
            self._hide_bubble()
        else:
            self._show_bubble()


class VideoPlayerPreview(FloatLayout):
    source = ObjectProperty(None)
    video = ObjectProperty(None)
    click_done = BooleanProperty(False)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.click_done:
            self.click_done = True
            self.video.state = 'play'
        return True


class VideoPlayerAnnotation(Label):
    '''Annotation class used for creating annotation labels.

    Additional keys are available:

    * bgcolor: [r, g, b, a] - background color of the text box
    * bgsource: 'filename' - background image used for the background text box
    * border: (n, e, s, w) - border used for the background image

    '''
    start = NumericProperty(0)
    '''Start time of the annotation.

    :attr:`start` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 0.
    '''

    duration = NumericProperty(1)
    '''Duration of the annotation.

    :attr:`duration` is a :class:`~kivy.properties.NumericProperty` and
    defaults to 1.
    '''

    annotation = DictProperty({})

    def on_annotation(self, instance, ann):
        for key, value in ann.items():
            setattr(self, key, value)


class VideoPlayer(GridLayout):
    '''VideoPlayer class. See module documentation for more information.
    '''

    source = StringProperty('')
    '''Source of the video to read.

    :attr:`source` is a :class:`~kivy.properties.StringProperty` and
    defaults to ''.

    .. versionchanged:: 1.4.0
    '''

    thumbnail = StringProperty('')
    '''Thumbnail of the video to show. If None, VideoPlayer will try to find
    the thumbnail from the :attr:`source` + '.png'.

    :attr:`thumbnail` a :class:`~kivy.properties.StringProperty` and defaults
    to ''.

    .. versionchanged:: 1.4.0
    '''

    duration = NumericProperty(-1)
    '''Duration of the video. The duration defaults to -1 and is set to the
    real duration when the video is loaded.

    :attr:`duration` is a :class:`~kivy.properties.NumericProperty` and
    defaults to -1.
    '''

    position = NumericProperty(0)
    '''Position of the video between 0 and :attr:`duration`. The position
    defaults to -1 and is set to the real position when the video is loaded.

    :attr:`position` is a :class:`~kivy.properties.NumericProperty` and
    defaults to -1.
    '''

    volume = NumericProperty(1.0)
    '''Volume of the video in the range 0-1. 1 means full volume and 0 means
    mute.

    :attr:`volume` is a :class:`~kivy.properties.NumericProperty` and defaults
    to 1.
    '''

    state = OptionProperty('stop', options=('play', 'pause', 'stop'))
    '''String, indicates whether to play, pause, or stop the video::

        # start playing the video at creation
        video = VideoPlayer(source='movie.mkv', state='play')

        # create the video, and start later
        video = VideoPlayer(source='movie.mkv')
        # and later
        video.state = 'play'

    :attr:`state` is an :class:`~kivy.properties.OptionProperty` and defaults
    to 'stop'.
    '''

    play = BooleanProperty(False, deprecated=True)
    '''
    .. deprecated:: 1.4.0
        Use :attr:`state` instead.

    Boolean, indicates whether the video is playing or not. You can start/stop
    the video by setting this property::

        # start playing the video at creation
        video = VideoPlayer(source='movie.mkv', play=True)

        # create the video, and start later
        video = VideoPlayer(source='movie.mkv')
        # and later
        video.play = True

    :attr:`play` is a :class:`~kivy.properties.BooleanProperty` and defaults
    to False.
    '''

    image_overlay_play = StringProperty(
        'atlas://data/images/defaulttheme/player-play-overlay')
    '''Image filename used to show a "play" overlay when the video has not yet
    started.

    :attr:`image_overlay_play` is a
    :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/player-play-overlay'.

    '''

    image_loading = StringProperty('data/images/image-loading.zip')
    '''Image filename used when the video is loading.

    :attr:`image_loading` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'data/images/image-loading.zip'.
    '''

    image_play = StringProperty(
        'atlas://data/images/defaulttheme/media-playback-start')
    '''Image filename used for the "Play" button.

    :attr:`image_play` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/media-playback-start'.
    '''

    image_stop = StringProperty(
        'atlas://data/images/defaulttheme/media-playback-stop')
    '''Image filename used for the "Stop" button.

    :attr:`image_stop` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/media-playback-stop'.
    '''

    image_pause = StringProperty(
        'atlas://data/images/defaulttheme/media-playback-pause')
    '''Image filename used for the "Pause" button.

    :attr:`image_pause` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/media-playback-pause'.
    '''

    image_volumehigh = StringProperty(
        'atlas://data/images/defaulttheme/audio-volume-high')
    '''Image filename used for the volume icon when the volume is high.

    :attr:`image_volumehigh` is a :class:`~kivy.properties.StringProperty` and
    defaults to 'atlas://data/images/defaulttheme/audio-volume-high'.
    '''

    image_volumemedium = StringProperty(
        'atlas://data/images/defaulttheme/audio-volume-medium')
    '''Image filename used for the volume icon when the volume is medium.

    :attr:`image_volumemedium` is a :class:`~kivy.properties.StringProperty`
    and defaults to 'atlas://data/images/defaulttheme/audio-volume-medium'.
    '''

    image_volumelow = StringProperty(
        'atlas://data/images/defaulttheme/audio-volume-low')
    '''Image filename used for the volume icon when the volume is low.

    :attr:`image_volumelow` is a :class:`~kivy.properties.StringProperty`
    and defaults to 'atlas://data/images/defaulttheme/audio-volume-low'.
    '''

    image_volumemuted = StringProperty(
        'atlas://data/images/defaulttheme/audio-volume-muted')
    '''Image filename used for the volume icon when the volume is muted.

    :attr:`image_volumemuted` is a :class:`~kivy.properties.StringProperty`
    and defaults to 'atlas://data/images/defaulttheme/audio-volume-muted'.
    '''

    annotations = StringProperty('')
    '''If set, it will be used for reading annotations box.

    :attr:`annotations` is a :class:`~kivy.properties.StringProperty`
    and defaults to ''.
    '''

    fullscreen = BooleanProperty(False)
    '''Switch to fullscreen view. This should be used with care. When
    activated, the widget will remove itself from its parent, remove all
    children from the window and will add itself to it. When fullscreen is
    unset, all the previous children are restored and the widget is restored to
    its previous parent.

    .. warning::

        The re-add operation doesn't care about the index position of its
        children within the parent.

    :attr:`fullscreen` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to False.
    '''

    allow_fullscreen = BooleanProperty(True)
    '''By default, you can double-tap on the video to make it fullscreen. Set
    this property to False to prevent this behavior.

    :attr:`allow_fullscreen` is a :class:`~kivy.properties.BooleanProperty`
    defaults to True.
    '''

    options = DictProperty({})
    '''Optional parameters can be passed to a :class:`~kivy.uix.video.Video`
    instance with this property.

    :attr:`options` a :class:`~kivy.properties.DictProperty` and
    defaults to {}.
    '''

    # internals
    container = ObjectProperty(None)

    _video_load_ev = None

    def __init__(self, **kwargs):
        self._video = None
        self._image = None
        self._annotations = ''
        self._annotations_labels = []
        super(VideoPlayer, self).__init__(**kwargs)
        update_thumbnail = self._update_thumbnail
        update_annotations = self._update_annotations
        fbind = self.fbind
        fbind('thumbnail', update_thumbnail)
        fbind('annotations', update_annotations)

        if self.source:
            self._trigger_video_load()

    def _trigger_video_load(self, *largs):
        ev = self._video_load_ev
        if ev is None:
            ev = self._video_load_ev = Clock.schedule_once(self._do_video_load,
                                                           -1)
        ev()

    def _try_load_default_thumbnail(self, *largs):
        if not self.thumbnail:
            filename = self.source.rsplit('.', 1)
            thumbnail = filename[0] + '.png'
            if exists(thumbnail):
                self._load_thumbnail(thumbnail)

    def _try_load_default_annotations(self, *largs):
        if not self.annotations:
            filename = self.source.rsplit('.', 1)
            annotations = filename[0] + '.jsa'
            if exists(annotations):
                self._load_annotations(annotations)

    def on_source(self, instance, value):
        # By default, VideoPlayer should look for thumbnail and annotations
        # with the same filename (except extension) of the source (video) file.
        Clock.schedule_once(self._try_load_default_thumbnail, -1)
        Clock.schedule_once(self._try_load_default_annotations, -1)
        if self._video is not None:
            self._video.unload()
            self._video = None
        if value:
            self._trigger_video_load()

    def _update_thumbnail(self, *largs):
        self._load_thumbnail(self.thumbnail)

    def _update_annotations(self, *largs):
        self._load_annotations(self.annotations)

    def on_image_overlay_play(self, instance, value):
        self._image.image_overlay_play = value

    def on_image_loading(self, instance, value):
        self._image.image_loading = value

    def _load_thumbnail(self, thumbnail):
        if not self.container:
            return
        self.container.clear_widgets()
        if thumbnail:
            self._image = VideoPlayerPreview(source=thumbnail, video=self)
            self.container.add_widget(self._image)

    def _load_annotations(self, annotations):
        if not self.container:
            return
        self._annotations_labels = []
        if annotations:
            with open(annotations, 'r') as fd:
                self._annotations = load(fd)
            if self._annotations:
                for ann in self._annotations:
                    self._annotations_labels.append(
                        VideoPlayerAnnotation(annotation=ann))

    def on_state(self, instance, value):
        if self._video is not None:
            self._video.state = value

    def _set_state(self, instance, value):
        self.state = value

    def _do_video_load(self, *largs):
        self._video = Video(source=self.source, state=self.state,
                            volume=self.volume, pos_hint={'x': 0, 'y': 0},
                            **self.options)
        self._video.bind(texture=self._play_started,
                         duration=self.setter('duration'),
                         position=self.setter('position'),
                         volume=self.setter('volume'),
                         state=self._set_state)

    def on_play(self, instance, value):
        value = 'play' if value else 'stop'
        return self.on_state(instance, value)

    def on_volume(self, instance, value):
        if not self._video:
            return
        self._video.volume = value

    def on_position(self, instance, value):
        labels = self._annotations_labels
        if not labels:
            return
        for label in labels:
            start = label.start
            duration = label.duration
            if start > value or (start + duration) < value:
                if label.parent:
                    label.parent.remove_widget(label)
            elif label.parent is None:
                self.container.add_widget(label)

    def seek(self, percent, precise=True):
        '''Change the position to a percentage (strictly, a proportion)
           of duration.

        :Parameters:
            `percent`: float or int
                Position to seek as a proportion of total duration, must
                be between 0-1.
            `precise`: bool, defaults to True
                Precise seeking is slower, but seeks to exact requested
                percent.

        .. warning::
            Calling seek() before the video is loaded has no effect.

        .. versionadded:: 1.2.0

        .. versionchanged:: 1.10.1
            The `precise` keyword argument has been added.
        '''
        if not self._video:
            return
        self._video.seek(percent, precise=precise)

    def _play_started(self, instance, value):
        self.container.clear_widgets()
        self.container.add_widget(self._video)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        if touch.is_double_tap and self.allow_fullscreen:
            self.fullscreen = not self.fullscreen
            return True
        return super(VideoPlayer, self).on_touch_down(touch)

    def on_fullscreen(self, instance, value):
        window = self.get_parent_window()
        if not window:
            Logger.warning('VideoPlayer: Cannot switch to fullscreen, '
                           'window not found.')
            if value:
                self.fullscreen = False
            return
        if not self.parent:
            Logger.warning('VideoPlayer: Cannot switch to fullscreen, '
                           'no parent.')
            if value:
                self.fullscreen = False
            return

        if value:
            self._fullscreen_state = state = {
                'parent': self.parent,
                'pos': self.pos,
                'size': self.size,
                'pos_hint': self.pos_hint,
                'size_hint': self.size_hint,
                'window_children': window.children[:]}

            # remove all window children
            for child in window.children[:]:
                window.remove_widget(child)

            # put the video in fullscreen
            if state['parent'] is not window:
                state['parent'].remove_widget(self)
            window.add_widget(self)

            # ensure the video widget is in 0, 0, and the size will be
            # readjusted
            self.pos = (0, 0)
            self.size = (100, 100)
            self.pos_hint = {}
            self.size_hint = (1, 1)
        else:
            state = self._fullscreen_state
            window.remove_widget(self)
            for child in state['window_children']:
                window.add_widget(child)
            self.pos_hint = state['pos_hint']
            self.size_hint = state['size_hint']
            self.pos = state['pos']
            self.size = state['size']
            if state['parent'] is not window:
                state['parent'].add_widget(self)


if __name__ == '__main__':
    import sys
    from kivy.base import runTouchApp
    player = VideoPlayer(source=sys.argv[1])
    runTouchApp(player)
    if player:
        player.state = 'stop'
