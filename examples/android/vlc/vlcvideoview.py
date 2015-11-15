'''
android VLC MediaPlayer integration
=======================

The goal of this widget is to integrate VLC MediaPlayer widget

'''
__all__ = ('VlcVideoView', 'VlcOptions')

from nativeholder import AndroidSurfaceWidget, run_on_ui_thread

from kivy.clock import Clock
from kivy.properties import (BooleanProperty, StringProperty,
        OptionProperty, NumericProperty, DictProperty, ReferenceListProperty)
from kivy.logger import Logger

from jnius import autoclass, cast, PythonJavaClass, java_method

jLibVLC = autoclass('org.videolan.libvlc.LibVLC')
jVlcUtil = autoclass('org.videolan.libvlc.util.VLCUtil')
jVlcVOut = autoclass('org.videolan.libvlc.IVLCVout')
jVlcMediaPlayer = autoclass('org.videolan.libvlc.MediaPlayer')
jVlcMediaPlayerEvent = autoclass('org.videolan.libvlc.MediaPlayer$Event')
jVlcMedia = autoclass('org.videolan.libvlc.Media')
jVlcMediaEvent = autoclass('org.videolan.libvlc.Media$Event')
jVlcMediaMeta = autoclass('org.videolan.libvlc.Media$Meta')
jVlcMediaList = autoclass('org.videolan.libvlc.MediaList')
jArrayList = autoclass('java.util.ArrayList')
jTextUtils = autoclass('android.text.TextUtils')
jString = autoclass('java.lang.String')
jUri = autoclass('android.net.Uri')

########################
#
#   event listeners
#
########################


class VlcHardwareAccelerationError(PythonJavaClass):
    __javainterfaces__ = [
        'org/videolan/libvlc/LibVLC$HardwareAccelerationError']
    __javacontext__ = 'app'

    def __init__(self):
        self._hosts = []
        super(VlcHardwareAccelerationError, self).__init__()

    def add_observer(self, host):
        self._hosts.append(host)

    def remove_observer(self, host):
        self._hosts.remove(host)

    # abstract void eventHardwareAccelerationError()
    @java_method('()V')
    def eventHardwareAccelerationError(self):
        for host in self._hosts:
            host.on_vlc_hw_error()


class VlcMediaEventsRedirector(PythonJavaClass):
    __javainterfaces__ = ['org/videolan/libvlc/Media$EventListener']
    __javacontext__ = 'app'

    def __init__(self, host):
        self.defaultRedirection = ('other', host.on_vlcmedia_event)
        self.eventTypesRedirectionMap = {
            jVlcMediaEvent.MetaChanged:
                    ('meta_changed',
                     host.on_vlcmedia_meta_changed),
            jVlcMediaEvent.SubItemAdded:
                    ('sub_item_added',
                     host.on_vlcmedia_sub_item_added),
            jVlcMediaEvent.DurationChanged:
                    ('duration_changed',
                     host.on_vlcmedia_duration_changed),
            jVlcMediaEvent.ParsedChanged:
                    ('parsed_changed',
                     host.on_vlcmedia_parsed_changed),
            jVlcMediaEvent.StateChanged:
                    ('state_changed',
                     host.on_vlcmedia_state_changed),
            jVlcMediaEvent.SubItemTreeAdded:
                    ('sub_item_tree_added',
                     host.on_vlcmedia_sub_item_tree_added),
        }
        super(VlcMediaEventsRedirector, self).__init__()

    # abstract void onEvent(Media.Event event)
    @java_method('(Lorg/videolan/libvlc/VLCEvent;)V')
    def onEvent(self, event):
        name, redirection = self.eventTypesRedirectionMap.get(
            event.type, self.defaultRedirection)
        Logger.info("VlcVideoView: Media event %d %s" % (event.type, name))
        mediaEvent = cast('org/videolan/libvlc/Media$Event', event)
        redirection(mediaEvent)


class VlcMediaPlayerEventsRedirector(PythonJavaClass):
    __javainterfaces__ = ['org/videolan/libvlc/MediaPlayer$EventListener']
    __javacontext__ = 'app'

    def __init__(self, host):
        self.defaultRedirection = ('other', host.on_vlcplayer_event)
        self.eventTypesRedirectionMap = {
            jVlcMediaPlayerEvent.Opening:
                    ('opening', host.on_vlcplayer_opening),
            # jVlcMediaPlayerEvent.Buffering: 
            #         ('buffering', host.on_vlcplayer_buffering),
            jVlcMediaPlayerEvent.Playing:
                    ('playing', host.on_vlcplayer_playing),
            jVlcMediaPlayerEvent.Paused:
                    ('paused', host.on_vlcplayer_paused),
            jVlcMediaPlayerEvent.Stopped:
                    ('stopped', host.on_vlcplayer_stopped),
            # jVlcMediaPlayerEvent.Forward:
            #         ('forward', host.on_vlcplayer_forward),
            # jVlcMediaPlayerEvent.Backward:
            #         ('backward', host.on_vlcplayer_backward),
            jVlcMediaPlayerEvent.EndReached:
                    ('end_reached',
                     host.on_vlcplayer_end_reached),
            jVlcMediaPlayerEvent.EncounteredError:
                    ('error', host.on_vlcplayer_error),
            jVlcMediaPlayerEvent.TimeChanged:
                    ('time', host.on_vlcplayer_time),
            jVlcMediaPlayerEvent.PositionChanged:
                    ('position', host.on_vlcplayer_position),
            jVlcMediaPlayerEvent.SeekableChanged:
                    ('seekable', host.on_vlcplayer_seekable),
            jVlcMediaPlayerEvent.PausableChanged:
                    ('pausable', host.on_vlcplayer_pausable),
            # jVlcMediaPlayerEvent.TitleChanged:
            #         ('title', host.on_vlcplayer_title),
            # jVlcMediaPlayerEvent.SnapshotTaken:
            #         ('snapshot', host.on_vlcplayer_snapshot),
            # jVlcMediaPlayerEvent.LengthChanged:
            #         ('length', host.on_vlcplayer_length),
            jVlcMediaPlayerEvent.Vout:
                    ('vout', host.on_vlcplayer_vout),
            # jVlcMediaPlayerEvent.ScrambleChanged:
            #         ('scramble', host.on_vlcplayer_scramble),
            jVlcMediaPlayerEvent.ESAdded:
                    ('es_added', host.on_vlcplayer_es_added),
            jVlcMediaPlayerEvent.ESDeleted:
                    ('es_deleted', host.on_vlcplayer_es_deleted),
            # jVlcMediaPlayerEvent.ESSelected:
            #         ('es_selected', host.on_vlcplayer_es_selected),
        }
        super(VlcMediaPlayerEventsRedirector, self).__init__()

    # abstract void onEvent(MediaPlayer.Event event)
    @java_method('(Lorg/videolan/libvlc/VLCEvent;)V')
    def onEvent(self, event):
        name, redirection = self.eventTypesRedirectionMap.get(
            event.type, self.defaultRedirection)
        Logger.info("VlcVideoView: Player event %d %s" % (event.type, name))
        mediaPlayerEvent = cast('org/videolan/libvlc/MediaPlayer$Event', event)
        redirection(mediaPlayerEvent)


class VlcVOutEventsRedirector(PythonJavaClass):
    __javainterfaces__ = ['org/videolan/libvlc/IVLCVout$Callback']
    __javacontext__ = 'app'

    def __init__(self, host):
        self._host = host
        super(VlcVOutEventsRedirector, self).__init__()
    # void onNewLayout(IVLCVout vlcVout, int width, int height, int
    # visibleWidth, int visibleHeight, int sarNum, int sarDen)

    @java_method('(Lorg/videolan/libvlc/IVLCVout;IIIIII)V')
    def onNewLayout(self, vlcVout, width, height, visibleWidth, visibleHeight,
            sarNum, sarDen):
        Logger.info("VlcVideoView: Vout new layout width={}, height={}, "
            "visibleWidth={}, visibleHeight={}, sarNum={}, sarDen={}".format(
            width, height, visibleWidth, visibleHeight, sarNum, sarDen))
        self._host.on_vlcvout_new_layout(
            width, height, visibleWidth, visibleHeight, sarNum, sarDen)
    # void onSurfacesCreated(IVLCVout vlcVout)

    @java_method('(Lorg/videolan/libvlc/IVLCVout;)V')
    def onSurfacesCreated(self, vlcVout):
        Logger.info("VlcVideoView: Vout surface created")
        self._host.on_vlcvout_surface_created()
    # void onSurfacesDestroyed(IVLCVout vlcVout)

    @java_method('(Lorg/videolan/libvlc/IVLCVout;)V')
    def onSurfacesDestroyed(self, vlcVout):
        Logger.info("VlcVideoView: Vout surface destroyed")
        self._host.on_vlcvout_surface_destroyed()

########################
#
#  VlcVideoView
#
########################


class VlcVideoView(AndroidSurfaceWidget):

    '''android vlc VideoView widget
    args:
        source  -  path or uri to video data
        options -  extra options 
        state   - 'play', 'stop', 'pause'
    props:
        loaded   - media file is loaded and ready to go
        duration - duration of the video. The duration defaults to -1, and is
                   set to a real duration when the video is loaded
        position - Position of the video between 0 and duration. The position
                   defaults to -1 and is set to a real position when the video
                   is loaded
        eos      - Boolean, indicates whether the video has finished playing
                   or not (reached the end of the stream)
        state    - indicates whether to play, pause, or stop the video
        player_state - indicates whether to play, pause, or stop the video
        media_state  - indicates whether to play, pause, or stop the video
    '''
    loaded = BooleanProperty(False)
    source = StringProperty()
    options = DictProperty()
    source_options = ReferenceListProperty(source, options)
    state = OptionProperty('stop', options=['stop', 'play', 'pause'])
    player_state = OptionProperty(
        'stop', options=['stop', 'opening', 'play', 'pause', 'error'])
    media_state = OptionProperty('nothing', options=[
                                 'nothing', 'opening', 'buffering', 'playing',
                                 'paused', 'stopped', 'ended', 'error'])
    duration = NumericProperty(-1)
    position = NumericProperty(-1)
    position_normalized = NumericProperty(0.0)
    eos = BooleanProperty(False)
    seekable = BooleanProperty(False)
    pausable = BooleanProperty(False)
    aspect_ratio = NumericProperty(0)
    libVLC = None
    _hardwareAccelerationError = VlcHardwareAccelerationError()
    VlcLibOptions = ['--noaudio']

    def __init__(self, **kwargs):
        if VlcVideoView.libVLC is None:
            # Create singleton global LibVLC instance
            optionsArray = jArrayList()
            for o in VlcVideoView.VlcLibOptions:
                optionsArray.add(o)
            VlcVideoView.libVLC = jLibVLC(optionsArray)
            VlcVideoView.libVLC.setOnHardwareAccelerationError(
                VlcVideoView._hardwareAccelerationError)
        self._mediaObj = None
        self._mediaPlayer = None
        self._vlcMediaEventsRedirector = VlcMediaEventsRedirector(self)
        self._mediaPlayerEventsRedirector = VlcMediaPlayerEventsRedirector(
            self)
        self._vOutCallbacks = VlcVOutEventsRedirector(self)

        self._create_player()

        super(VlcVideoView, self).__init__(**kwargs)
        self.bind(parent=lambda s,v:
                  VlcVideoView._hardwareAccelerationError.add_observer(self) if v
                  else VlcVideoView._hardwareAccelerationError.remove_observer(self))

    def populate_surface_view(self, surfaceView, context):
        Logger.info('VlcVideoView: creating video view %s (%s)' %
                    (self.source, self.state))

        cpuOk = jVlcUtil.hasCompatibleCPU(context)
        Logger.info("VlcVideoView: cpu compatible %s" % str(cpuOk))

        Logger.info('VlcVideoView: populate done %s (%s)' %
                    (self.source, self.state))

    def _create_player(self):
        #         // Create a VLC Media Player
        self._mediaPlayer = mediaPlayer = jVlcMediaPlayer(VlcVideoView.libVLC)
        mediaPlayer.setEventListener(self._mediaPlayerEventsRedirector)

    def _unload_player(self):
        if not self._mediaPlayer is None:
            Logger.info('VlcVideoView: destroying %s (%s)' %
                        (self.source, self.state))
            self._mediaPlayer.stop()
            self._mediaPlayer.setEventListener(None)
            self._mediaPlayer.release()
            self._mediaPlayer = None

    def _create_media(self):
        # Create a VLC Media object
        if any(self.source.startswith(prefix) for prefix in [
                    'rtsp://', 'http://', 'https://', 'file://']):
            uri = jUri.parse(self.source)
            self._mediaObj = jVlcMedia(VlcVideoView.libVLC, uri)
            Logger.info('VlcVideoView: uri %s (%s)' %
                        (self.source, self.state))
        else:
            self._mediaObj = jVlcMedia(VlcVideoView.libVLC, self.source)
            Logger.info('VlcVideoView: path %s (%s)' %
                        (self.source, self.state))
        if self.options:
            if self.options.has_key('network-caching'):
                self._mediaObj.setHWDecoderEnabled(True, False)
                Logger.info(
                    "VlcVideoView: HWDecoder enabled by network-caching")
            for n, v in self.options.items():
                if n == 'hw-decoder':
                    hw_enable = (v in ['force', 'enable', '1', 'True'])
                    hw_force = v in ['force']
                    self._mediaObj.setHWDecoderEnabled(hw_enable, hw_force)
                    Logger.info(
                        "VlcVideoView: HWDecoder enabled {}, forced {}".format(
                        hw_enable, hw_force))
                else:
                    s = ':{}={}'.format(n, v) if v else ':{}'.format(n)
                    Logger.info("VlcVideoView: Media option {}".format(s))
                    self._mediaObj.addOption(s)
        self._mediaObj.setEventListener(self._vlcMediaEventsRedirector)

    def _unload_media(self):
        if self._mediaObj is not None:
            Logger.info(
                'VlcVideoView: clearing previous source (%s)' % self.state)
            self._mediaObj.setEventListener(None)
            self._mediaPlayer.setMedia(None)
            self._mediaObj = None
            self.loaded = False
            self.duration = -1
            self.position = -1
            self.position_normalized = 0.0
            self.eos = False
            self.seekable = False
            self.pausable = False
            self.player_state = 'stop'

    def _attach_vout(self, surface, surfaceHolder):
        vlcVOut = self._mediaPlayer.getVLCVout()
        vlcVOut.setVideoSurface(surface, surfaceHolder)
        vlcVOut.addCallback(self._vOutCallbacks)
        vlcVOut.attachViews()

    def _detach_vout(self):
        vlcVOut = self._mediaPlayer.getVLCVout()
        vlcVOut.dettachViews()
        vlcVOut.removeCallback(self._vOutCallbacks)
#         self._mediaPlayer.setVideoTrack(-1);

    @run_on_ui_thread
    def _apply_aspect_ratio(self):
        aspect_ratio = self.aspect_ratio
        if not self.surfaceView or not aspect_ratio:
            return
        width, height = self.size
        left, top = self.get_native_pos()
        Logger.info('VlcVideoView: aspect_ratio %.2f, sv_pos %d,%d '
                ' size %d,%d' % (aspect_ratio, left, top, width, height))
        adjusted_width = int(height * aspect_ratio)
        adjusted_height = int(width / aspect_ratio)
        if adjusted_width < width:
            left = int((width - adjusted_width) / 2)
            top = 0
            width = adjusted_width
            Logger.info('VlcVideoView: aspect ratio %.2f, '
                'decrease width to %d, changed left to %d' % (
                aspect_ratio, width, left))
        elif adjusted_height < height:
            left = 0
            top = int((height - adjusted_height) / 2)
            height = adjusted_height
            Logger.info('VlcVideoView: aspect ratio %.2f, '
                'decrease height to %d, changed top to %d' % (
                aspect_ratio, adjusted_height, top))
        else:
            Logger.info('VlcVideoView: aspect ratio %.2f, '
                'ignored %d %d to %d %d' % (
                aspect_ratio, width, left, adjusted_width, adjusted_height))
            return
        self.set_native_pos((left, top))
        self.set_native_size((width, height))

    def _apply_video_player_state(self):
        if not self._mediaPlayer:
            Logger.info(
                'VlcVideoView: waiting for Mediaplayer %s (%s)' % (
                self.source, self.state))
        elif not self._mediaPlayer.getVLCVout().areViewsAttached():
            Logger.info('VlcVideoView: waiting for Vout %s (%s)' %
                        (self.source, self.state))
            self._mediaPlayer.stop()
#             self._mediaPlayer.setVideoTrack(-1);
        elif self.state == 'play':
            self._select_videotrack()
            Logger.info('VlcVideoView: starting %s (%s)' %
                        (self.source, self.state))
            self._mediaPlayer.play()
        elif self.state == 'pause':
            Logger.info('VlcVideoView: pausing %s (%s)' %
                        (self.source, self.state))
            self._mediaPlayer.pause()
        else:
            Logger.info('VlcVideoView: stopping %s (%s)' %
                        (self.source, self.state))
            self._mediaPlayer.stop()

    def _select_videotrack(self):
        videoTrack = self.options.get('video-track', '')
        if videoTrack:
            res = self._mediaPlayer.setVideoTrack(int(videoTrack))
            Logger.info('VlcVideoView: selecting track %d for %s - %s' %
                        (int(videoTrack), self.source, str(res)))

    def unload(self):
        Logger.info('VlcVideoView: unload %s' % self.source)
        self._unload_media()
        self._unload_player()

    def seek(self, position_normalized):
        Logger.info('VlcVideoView: seek {} for {}'.format(
            position_normalized, self.source))
        self._mediaPlayer.setPosition(position_normalized)

    def on_source_options(self, instance, value):
        Logger.info('VlcVideoView: on_source_options {}'.format(value))
        self._unload_media()
        self._create_media()
        self._mediaPlayer.setMedia(self._mediaObj)

    def on_state(self, instance, state):
        Logger.info(
            'VlcVideoView: on_state {} for {}'.format(state, self.source))
        self._apply_video_player_state()

    def on_size(self, instance, size):
        Logger.info(
            'VlcVideoView: on_size {} for {}'.format(size, self.source))
        self._apply_aspect_ratio()

    def on_aspect_ratio(self, instance, aspect_ratio):
        Logger.info(
            'VlcVideoView: on_aspect_ratio {} for {}'.format(
            aspect_ratio, self.source))
        self._apply_aspect_ratio()

    #
    # surface callbacks
    #
    def on_surface_created(self, surfaceHolder):
        Logger.info('VlcVideoView: on_surface_created %s (%s)' %
                    (self.source, self.state))
        self._attach_vout(surfaceHolder.getSurface(), surfaceHolder)
        self._apply_video_player_state()

    def on_surface_changed(self, surfaceHolder, fmt, width, height):
        # internal, called when the android SurfaceView is ready
        Logger.info('VlcVideoView: on_surface_changed (%d, %d) for %s (%s)' % (
            width, height, self.source, self.state))
        self._apply_aspect_ratio()

    def on_surface_destroyed(self, surfaceHolder):
        Logger.info('VlcVideoView: on_surface_destroyed %s (%s)' %
                    (self.source, self.state))
        self._detach_vout()
        self._apply_video_player_state()

    #
    # vlc callbacks
    #
    def on_vlc_hw_error(self, mediaPlayerEvent):
        errorMessage = jVlcUtil.getErrorMsg()
        Logger.info(
            'VlcVideoView: on_vlc_hw_error {} for {}'.format(
            errorMessage, self.source))
        self.player_state = 'error'

    def on_vlcplayer_event(self, mediaPlayerEvent):
        pass

    def on_vlcplayer_opening(self, mediaPlayerEvent):
        self.player_state = 'opening'

    def on_vlcplayer_playing(self, mediaPlayerEvent):
        self.player_state = 'play'
        self.eos = False

    def on_vlcplayer_paused(self, mediaPlayerEvent):
        self.player_state = 'pause'

    def on_vlcplayer_stopped(self, mediaPlayerEvent):
        self.player_state = 'stop'

    def on_vlcplayer_end_reached(self, mediaPlayerEvent):
        self.eos = True
        Logger.info('VlcVideoView: on_vlcplayer_end_reached for {}'.format(
            self.source))

    def on_vlcplayer_error(self, mediaPlayerEvent):
        errorMessage = jVlcUtil.getErrorMsg()
        Logger.info(
            'VlcVideoView: on_vlcplayer_error {} for {}'.format(
            errorMessage, self.source))
        self.player_state = 'error'
        self.eos = True

    def on_vlcplayer_vout(self, mediaPlayerEvent):
        c = mediaPlayerEvent.getVoutCount()
        Logger.info(
            'VlcVideoView: on_vlcplayer_vout {} for {}'.format(c, self.source))

    def on_vlcplayer_time(self, mediaPlayerEvent):
        self.position = mediaPlayerEvent.getTimeChanged()
        Logger.info('VlcVideoView: on_vlcplayer_time {}(ms) of {}(ms) for {}'.format(
            self.position, self.duration, self.source))

    def on_vlcplayer_position(self, mediaPlayerEvent):
        self.position_normalized = mediaPlayerEvent.getPositionChanged()
        Logger.info('VlcVideoView: on_vlcplayer_position {} for {}'.format(
            self.position_normalized, self.source))

    def on_vlcplayer_seekable(self, mediaPlayerEvent):
        self.seekable = mediaPlayerEvent.getSeekable()
        Logger.info('VlcVideoView: on_vlcplayer_seekable {} for {}'.format(
            self.position_normalized, self.source))

    def on_vlcplayer_pausable(self, mediaPlayerEvent):
        self.pausable = mediaPlayerEvent.getPausable()
        Logger.info('VlcVideoView: on_vlcplayer_pausable {} for {}'.format(
            self.position_normalized, self.source))

    def on_vlcplayer_es_added(self, mediaPlayerEvent):
        self._select_videotrack()
        self._log_media_tracks()

    def on_vlcplayer_es_deleted(self, mediaPlayerEvent):
        self._log_media_info()

    def on_vlcmedia_event(self, mediaEvent):
        pass

    def on_vlcmedia_meta_changed(self, mediaEvent):
        self._log_media_info()

    def on_vlcmedia_sub_item_added(self, mediaEvent):
        self._log_media_info()

    def on_vlcmedia_duration_changed(self, mediaEvent):
        self.duration = self._mediaObj.getDuration()
        Logger.info('VlcVideoView: on_vlcmedia_duration_changed '
            '{} for {}'.format(self.duration, self.source))
        self._log_media_info()

    def on_vlcmedia_parsed_changed(self, mediaEvent):
        Logger.info('VlcVideoView: on_vlcmedia_parsed_changed %s' %
                    self.source)
        self.duration = self._mediaObj.getDuration()
        self.loaded = bool(self._mediaObj.isParsed())
        self._log_media_info()

    def on_vlcmedia_state_changed(self, mediaEvent):
        state = self._mediaObj.getState()
        self.media_state = self.MediaStates.get(state, 'error')
        Logger.info('VlcVideoView: on_vlcmedia_state_changed {} {}'.format(
            state, self.media_state))

    def on_vlcmedia_sub_item_tree_added(self, mediaEvent):
        Logger.info(
            'VlcVideoView: on_vlc_media_sub_item_tree_added %s' % self.source)

    def on_vlcvout_new_layout(self, width, height, visibleWidth,
            visibleHeight, sarNum, sarDen):
        self.aspect_ratio = float(width) / float(height)

    def on_vlcvout_surface_created(self):
        pass

    def on_vlcvout_surface_destroyed(self):
        pass

    MediaStates = {
        0: 'nothing',
        1: 'opening',
        2: 'buffering',
        3: 'playing',
        4: 'paused',
        5: 'stopped',
        6: 'ended',
        7: 'error',
    }
    MediaTypeNames = {
        0: 'Unknown',
        1: 'File',
        2: 'Directory',
        3: 'Disc',
        4: 'Stream',
        5: 'Playlist',
    }
    TrackTypeNames = {
        - 1: 'Unknown',
        0: 'Audio',
        1: 'Video',
        2: 'Text',
    }

    def _log_media_meta(self):
        for name, meta_id in [
            ('Title', jVlcMediaMeta.Title),
            ('Artist', jVlcMediaMeta.Artist),
            ('Descr', jVlcMediaMeta.Description),
            ('Data', jVlcMediaMeta.Date),
        ]:
            meta = self._mediaObj.getMeta(meta_id)
            if meta is not None:
                Logger.info(
                    'VlcVideoView: Media: Meta.{}: {}'.format(name, meta))

    def _log_media_tracks(self):
        for trackN in xrange(0, self._mediaObj.getTrackCount()):
            track = self._mediaObj.getTrack(trackN)
            Logger.info('VlcVideoView: Track[{}].type: {} ({}), id: {}, '
                     'codec: {}, bitrate: {}, lang: {}, descr: {}'.format(
                     trackN, self.TrackTypeNames.get(track.type, '?'),
                     track.type, track.id, track.codec, track.bitrate,
                     track.language, track.description))

    def _log_media_info(self):
        Logger.info('VlcVideoView: MediaInfo for {} State: {} ({}) Type: {} '
            '({}) Parsed: {} Duration: {} Tracks: {}'.format(
            self.source,
            self.MediaStates.get(
                self._mediaObj.getState(), ''), self._mediaObj.getState(),
            self.MediaTypeNames.get(
                self._mediaObj.getType(), ''), self._mediaObj.getType(),
            self._mediaObj.isParsed(),
            self._mediaObj.getDuration(),
            self._mediaObj.getTrackCount()))
