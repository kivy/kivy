'''
android VLC MediaPlayer integration
=======================

The goal of this widget is to integrate VLC MediaPlayer widget

'''
__all__ = ('VlcVideoView', 'VlcOptions')

from nativeholder import AndroidSurfaceWidget

from kivy.clock import Clock
from android.runnable import run_on_ui_thread
from jnius import autoclass, cast, PythonJavaClass, java_method
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty, OptionProperty, NumericProperty, ReferenceListProperty
from kivy.logger import Logger

jLibVLC               = autoclass('org.videolan.libvlc.LibVLC')
jVlcUtil              = autoclass('org.videolan.libvlc.util.VLCUtil')
jVlcVOut              = autoclass('org.videolan.libvlc.IVLCVout')
jVlcMediaPlayer       = autoclass('org.videolan.libvlc.MediaPlayer')
jVlcMediaPlayerEvent  = autoclass('org.videolan.libvlc.MediaPlayer$Event')
jVlcMedia             = autoclass('org.videolan.libvlc.Media')
jVlcMediaEvent        = autoclass('org.videolan.libvlc.Media$Event')
jVlcMediaMeta         = autoclass('org.videolan.libvlc.Media$Meta')
jVlcMediaList         = autoclass('org.videolan.libvlc.MediaList')
jArrayList            = autoclass('java.util.ArrayList')
jTextUtils            = autoclass('android.text.TextUtils')
jString               = autoclass('java.lang.String')
jUri                  = autoclass('android.net.Uri')

########################
#
#   event listeners
#
########################

class VlcHardwareAccelerationError(PythonJavaClass):
	__javainterfaces__ = ['org/videolan/libvlc/LibVLC$HardwareAccelerationError']
	__javacontext__ = 'app'

	def __init__(self):
		self._hosts = []
		super(VlcHardwareAccelerationError, self).__init__()

	def add_observer(self, host):
		self._hosts.append(host)
	def remove_observer(self, host):
		self._hosts.remove(host)
		
	#abstract void eventHardwareAccelerationError()
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
			jVlcMediaEvent.MetaChanged:         ('meta_changed',        host.on_vlcmedia_meta_changed),
			jVlcMediaEvent.SubItemAdded:        ('sub_item_added',      host.on_vlcmedia_sub_item_added),
			jVlcMediaEvent.DurationChanged:     ('duration_changed',    host.on_vlcmedia_duration_changed),
			jVlcMediaEvent.ParsedChanged:       ('parsed_changed',      host.on_vlcmedia_parsed_changed),
			jVlcMediaEvent.StateChanged:        ('state_changed',       host.on_vlcmedia_state_changed),
			jVlcMediaEvent.SubItemTreeAdded:    ('sub_item_tree_added', host.on_vlcmedia_sub_item_tree_added),
		}
		super(VlcMediaEventsRedirector, self).__init__()
		
	#abstract void onEvent(Media.Event event)
	@java_method('(Lorg/videolan/libvlc/VLCEvent;)V')
	def onEvent(self, event):
		name, redirection = self.eventTypesRedirectionMap.get(event.type, self.defaultRedirection)
		Logger.info("VLC Media event %d %s"%(event.type, name))
		mediaEvent = cast('org/videolan/libvlc/Media$Event', event)
		redirection(mediaEvent)

class VlcMediaPlayerEventsRedirector(PythonJavaClass):
	__javainterfaces__ = ['org/videolan/libvlc/MediaPlayer$EventListener']
	__javacontext__ = 'app'

	def __init__(self, host):
		self.defaultRedirection = ('other', host.on_vlcplayer_event)
		self.eventTypesRedirectionMap = {
			jVlcMediaPlayerEvent.EndReached:       ('end_reached', host.on_vlcplayer_end_reached),
			jVlcMediaPlayerEvent.EncounteredError: ('error',       host.on_vlcplayer_error),
			jVlcMediaPlayerEvent.Opening:          ('opening',     host.on_vlcplayer_opening),
			jVlcMediaPlayerEvent.Playing:          ('playing',     host.on_vlcplayer_playing),
			jVlcMediaPlayerEvent.Paused:           ('paused',      host.on_vlcplayer_paused),
			jVlcMediaPlayerEvent.Stopped:          ('stopped',     host.on_vlcplayer_stopped),
			jVlcMediaPlayerEvent.Vout:             ('vout',        host.on_vlcplayer_vout),
			jVlcMediaPlayerEvent.PositionChanged:  ('position',    host.on_vlcplayer_position),
			jVlcMediaPlayerEvent.TimeChanged:      ('time',        host.on_vlcplayer_time),
			jVlcMediaPlayerEvent.ESAdded:          ('es_added',    host.on_vlcplayer_es_added),
			jVlcMediaPlayerEvent.ESDeleted:        ('es_deleted',  host.on_vlcplayer_es_deleted),
		}
		super(VlcMediaPlayerEventsRedirector, self).__init__()
		

	#abstract void onEvent(MediaPlayer.Event event)
	@java_method('(Lorg/videolan/libvlc/VLCEvent;)V')
	def onEvent(self, event):
		name, redirection = self.eventTypesRedirectionMap.get(event.type, self.defaultRedirection)
		Logger.info("VLC MediaPlayer event %d %s"%(event.type, name))
		mediaPlayerEvent = cast('org/videolan/libvlc/MediaPlayer$Event', event)
		redirection(mediaPlayerEvent)

class VlcVOutEventsRedirector(PythonJavaClass):
	__javainterfaces__ = ['org/videolan/libvlc/IVLCVout$Callback']
	__javacontext__ = 'app'

	def __init__(self, host):
		self._host = host
		super(VlcVOutEventsRedirector, self).__init__()
	#void onNewLayout(IVLCVout vlcVout, int width, int height, int visibleWidth, int visibleHeight, int sarNum, int sarDen)
	@java_method('(Lorg/videolan/libvlc/IVLCVout;IIIIII)V')
	def onNewLayout(self, vlcVout, width, height, visibleWidth, visibleHeight, sarNum, sarDen):
		Logger.info("VLC Vout new layout width={}, height={}, visibleWidth={}, visibleHeight={}, sarNum={}, sarDen={}".format(width, height, visibleWidth, visibleHeight, sarNum, sarDen))
		self._host.on_vlcvout_new_layout(width, height, visibleWidth, visibleHeight, sarNum, sarDen)
	#void onSurfacesCreated(IVLCVout vlcVout)
	@java_method('(Lorg/videolan/libvlc/IVLCVout;)V')
	def onSurfacesCreated(self, vlcVout):
		Logger.info("VLC Vout surface created")
		self._host.on_vlcvout_surface_created()
	#void onSurfacesDestroyed(IVLCVout vlcVout)
	@java_method('(Lorg/videolan/libvlc/IVLCVout;)V')
	def onSurfacesDestroyed(self, vlcVout):
		Logger.info("VLC Vout surface destroyed")
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
		position - Position of the video between 0 and duration. The position defaults
		           to -1 and is set to a real position when the video is loaded
		eos      - Boolean, indicates whether the video has finished playing or not
		           (reached the end of the stream)
		state    - indicates whether to play, pause, or stop the video
	'''
	loaded = BooleanProperty(False)
	source = StringProperty()
	options = ObjectProperty()
	state = OptionProperty('stop', options=['stop', 'play', 'pause'])
	actual_state = OptionProperty('stop', options=['stop', 'opening', 'play', 'pause', 'error'])
	duration = NumericProperty(-1)
	position = NumericProperty(-1)
	position_normalized = NumericProperty(0.0)
	eos = BooleanProperty(False)
	aspect_ratio = NumericProperty(0)
	source_options = ReferenceListProperty(source, options)
	libVLC = None
	_hardwareAccelerationError = VlcHardwareAccelerationError()
	VlcLibOptions = ['--noaudio']

	def __init__(self, **kwargs):
		if VlcVideoView.libVLC is None:
			# Create global LibVLC instance
			optionsArray = jArrayList()
			for o in VlcVideoView.VlcLibOptions: optionsArray.add(o)
# 			dlm = jString(', ')
# 			msg = jTextUtils.join(dlm, optionsArray)
# 			Logger.info("libVLC options: {}".format(msg))
			VlcVideoView.libVLC = jLibVLC(optionsArray)
			VlcVideoView.libVLC.setOnHardwareAccelerationError(VlcVideoView._hardwareAccelerationError)
		self._mediaObj = None															   
		self._mediaPlayer = None															   
		self._vlcMediaEventsRedirector = VlcMediaEventsRedirector(self)
		self._mediaPlayerEventsRedirector = VlcMediaPlayerEventsRedirector(self)
		self._vOutCallbacks = VlcVOutEventsRedirector(self)

		self._init_vlclib()
		self._create_player()

		super(VlcVideoView, self).__init__(**kwargs)

	def populate_surface_view(self, surfaceView, context):
		Logger.info('VlcVideoView: creating video view %s (%s)'%(self.source, self.state))															

		cpuOk = jVlcUtil.hasCompatibleCPU(context)
		Logger.info("VlcVideoView: cpu compatible %s"%str(cpuOk))

		Logger.info('VlcVideoView: populate done %s (%s)'%(self.source, self.state))															

	def _init_vlclib(self):
		VlcVideoView._hardwareAccelerationError.add_observer(self)
	def _finit_vlclib(self):
		VlcVideoView._hardwareAccelerationError.remove_observer(self)

	def _create_player(self):
# 		// Create a VLC Media Player
		self._mediaPlayer = mediaPlayer = jVlcMediaPlayer(VlcVideoView.libVLC)
		mediaPlayer.setEventListener(self._mediaPlayerEventsRedirector)
	def _unload_player(self):
		if not self._mediaPlayer is None:
			Logger.info('VlcVideoView: destroying %s (%s)'%(self.source, self.state))
			self._mediaPlayer.stop()
			self._mediaPlayer.setEventListener(None)
			self._mediaPlayer.release()
			self._mediaPlayer = None

	def _create_media(self):
		# Create a VLC Media object
		if any(self.source.startswith(prefix) for prefix in ['rtsp://', 'http://', 'https://', 'file://']):
			uri = jUri.parse(self.source)
			self._mediaObj = jVlcMedia(VlcVideoView.libVLC, uri)
			Logger.info('VlcVideoView: uri %s (%s)'%(self.source, self.state))
		else:
			self._mediaObj = jVlcMedia(VlcVideoView.libVLC, self.source)
			Logger.info('VlcVideoView: path %s (%s)'%(self.source, self.state))
		self._mediaObj.setHWDecoderEnabled(True, False)
		if self.options:
			for n,v in self.options.items():
				s = ':{}={}'.format(n, v) if v else ':{}'.format(n)
				Logger.info("Media option: {}".format(s))
				self._mediaObj.addOption(s)
		self._mediaObj.setEventListener(self._vlcMediaEventsRedirector);
	def _unload_media(self):
		if self._mediaObj is not None:
			Logger.info('VlcVideoView: clearing previous source (%s)'%self.state)															
			self._mediaObj.setEventListener(None)
			self._mediaPlayer.setMedia(None)
			self._mediaObj = None
			self.loaded = False
			self.duration = -1
			self.position = -1
			self.position_normalized = 0.0
			self.eos = False
			self.actual_state = 'stop'
			
	def _create_vout(self, surface, surfaceHolder):
		vlcVOut = self._mediaPlayer.getVLCVout()
		vlcVOut.setVideoSurface(surface, surfaceHolder)
		vlcVOut.addCallback(self._vOutCallbacks)
		vlcVOut.attachViews()
	def _unload_vout(self):
		vlcVOut = self._mediaPlayer.getVLCVout()
		vlcVOut.dettachViews()
		vlcVOut.removeCallback(self._vOutCallbacks)

	@run_on_ui_thread																		   
	def _apply_aspect_ratio(self):
		aspect_ratio = self.aspect_ratio
		if not self.surfaceView or not aspect_ratio: return
		width, height = self.size
		left, top = self.get_native_pos()
		Logger.info('VlcVideoView: aspect_ratio %.2f, sv_pos %d,%d  size %d,%d'%(aspect_ratio, left, top, width, height))
		adjusted_width = int(height * aspect_ratio)
		adjusted_height = int(width / aspect_ratio)
		if adjusted_width < width:
			left = int((width - adjusted_width) / 2)
			top = 0
			width = adjusted_width
			Logger.info('VlcVideoView: aspect_ratio %.2f, decrease width to %d, changed left to %d'%(aspect_ratio, width, left))
		elif adjusted_height < height:
			left = 0
			top = int((height - adjusted_height) / 2)
			height = adjusted_height
			Logger.info('VlcVideoView: aspect_ratio %.2f, decrease height to %d, changed top to %d'%(aspect_ratio, adjusted_height, top))
		else:
			Logger.info('VlcVideoView: aspect_ratio %.2f, ignored %d %d to %d %d'%(aspect_ratio, width, left, adjusted_width, adjusted_height))
			return
		self.set_native_pos((left, top))
		self.set_native_size((width, height))

	def _apply_video_player_state(self):
		if not self._mediaPlayer:
			Logger.info('VlcVideoView: waiting for Mediaplayer %s (%s)'%(self.source, self.state))
		elif not self._mediaPlayer.getVLCVout().areViewsAttached():
			Logger.info('VlcVideoView: waiting for Vout %s (%s)'%(self.source, self.state))
			self._mediaPlayer.stop()
		elif self.state == 'play':
			Logger.info('VlcVideoView: starting %s (%s)'%(self.source, self.state))
			self._mediaPlayer.play()
		elif self.state == 'pause':
			Logger.info('VlcVideoView: pausing %s (%s)'%(self.source, self.state))
			self._mediaPlayer.pause()
		else:
			Logger.info('VlcVideoView: stopping %s (%s)'%(self.source, self.state))
			self._mediaPlayer.stop()
		
	def unload(self):
		Logger.info('VlcVideoView: unload %s'%self.source)
		self._unload_media()															
		self._unload_player()
	def seek(self, position_normalized):
		Logger.info('VlcVideoView: seek {} for {}'.format(position_normalized, self.source))
		self._mediaPlayer.setPosition(position_normalized)

	def on_source_options(self, instance, value):
		Logger.info('VlcVideoView: on_source_options %s'%self.source)															
		self._unload_media()
		self._create_media()
		self._mediaPlayer.setMedia(self._mediaObj)

	def on_state(self, instance, state):
		Logger.info('VlcVideoView: on_state {} for {}'.format(state, self.source))															
		self._apply_video_player_state()

	def on_size(self, instance, size):
		Logger.info('VlcVideoView: on_size {} for {}'.format(size, self.source))															
		self._apply_aspect_ratio()

	def on_aspect_ratio(self, instance, aspect_ratio):
		Logger.info('VlcVideoView: on_aspect_ratio {} for {}'.format(aspect_ratio, self.source))															
		self._apply_aspect_ratio()

	#
	# surface callbacks
	#
	def on_surface_created(self, surfaceHolder):
		Logger.info('VlcVideoView: on_surface_created %s (%s)'%(self.source, self.state))
		self._create_vout(surfaceHolder.getSurface(), surfaceHolder)
		self._apply_video_player_state()
	def on_surface_changed(self, surfaceHolder, fmt, width, height):
		# internal, called when the android SurfaceView is ready
		Logger.info('VlcVideoView: on_surface_changed (%d, %d) for %s (%s)'%(width, height, self.source, self.state))
		self._apply_aspect_ratio()
	def on_surface_destroyed(self, surfaceHolder):
		Logger.info('VlcVideoView: on_surface_destroyed %s (%s)'%(self.source, self.state))
		self._unload_vout()
		self._apply_video_player_state()

	#
	# vlc callbacks
	#
	def on_vlc_hw_error(self, mediaPlayerEvent):
		errorMessage = jVlcUtil.getErrorMsg()
		Logger.info('VlcVideoView: on_vlc_hw_error {} for {}'.format(errorMessage, self.source))
		self.actual_state='error'
	def on_vlcplayer_event(self):
		pass
	def on_vlcplayer_end_reached(self, mediaPlayerEvent):
		self.eos = True
		Logger.info('VlcVideoView: on_vlcplayer_end_reached for {}'.format(self.source))
	def on_vlcplayer_error(self, mediaPlayerEvent):
		errorMessage = jVlcUtil.getErrorMsg()
		Logger.info('VlcVideoView: on_vlcplayer_error {} for {}'.format(errorMessage, self.source))
		self.actual_state = 'error'
	def on_vlcplayer_opening(self, mediaPlayerEvent):
		self.actual_state = 'opening'
	def on_vlcplayer_playing(self, mediaPlayerEvent):
		self.actual_state = 'play'
		self.eos = False
	def on_vlcplayer_paused(self, mediaPlayerEvent):
		self.actual_state = 'pause'
	def on_vlcplayer_stopped(self, mediaPlayerEvent):
		self.actual_state = 'stop'
	def on_vlcplayer_vout(self, mediaPlayerEvent):
		pass
	def on_vlcplayer_position(self, mediaPlayerEvent):
		self.position_normalized = mediaPlayerEvent.getPositionChanged()
		Logger.info('VlcVideoView: on_vlc_position {} for {} ({})'.format(self.position_normalized, self.source, self.state))
	def on_vlcplayer_time(self, mediaPlayerEvent):
		self.position = mediaPlayerEvent.getTimeChanged()
		Logger.info('VlcVideoView: on_vlc_time {}(ms) of {}(ms) for {} ({})'.format(self.position, self.duration, self.source, self.state))
	def on_vlcplayer_es_added(self, mediaPlayerEvent):
		self._log_media_info()
	def on_vlcplayer_es_deleted(self, mediaPlayerEvent):
		self._log_media_info()

	def on_vlcmedia_event(self, mediaEvent):
		pass
	def on_vlcmedia_meta_changed(self, mediaEvent):
		self._log_media_info()
	def on_vlcmedia_sub_item_added(self, mediaEvent):
		self._log_media_info()
	def on_vlcmedia_duration_changed(self, mediaEvent):
		self.duration=self._mediaObj.getDuration()
		Logger.info('VlcVideoView: on_vlcmedia_duration_changed {} for {}'.format(self.duration, self.source))
		self._log_media_info()
	def on_vlcmedia_parsed_changed(self, mediaEvent):
		Logger.info('VlcVideoView: on_vlcmedia_parsed_changed %s'%self.source)
		self.duration=self._mediaObj.getDuration()
		self.loaded = bool(self._mediaObj.isParsed())
		self._log_media_info()
	def on_vlcmedia_state_changed(self, mediaEvent):
		state = self._mediaObj.getState()
		Logger.info('VlcVideoView: on_vlcmedia_state_changed {} {}'.format(state, self.MediaStateNames.get(state, '?')))
		self._log_media_info()
	def on_vlcmedia_sub_item_tree_added(self, mediaEvent):
		Logger.info('VlcVideoView: on_vlc_media_sub_item_tree_added %s'%self.source)

	def on_vlcvout_new_layout(self, width, height, visibleWidth, visibleHeight, sarNum, sarDen):
		self.aspect_ratio = float(width) / float(height)
	def on_vlcvout_surface_created(self):
		pass
	def on_vlcvout_surface_destroyed(self):
		pass

	MediaStateNames = {
		0: 'NothingSpecial',
		1: 'Opening',
		2: 'Buffering',
		3: 'Playing',
		4: 'Paused',
		5: 'Stopped',
		6: 'Ended',
		7: 'Error',
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
		-1: 'Unknown',
		0: 'Audio',
		1: 'Video',
		2: 'Text',
	}

	def _log_media_info(self):
		Logger.info('VlcVideoView: MediaInfo for %s'%self.source)
		Logger.info('VlcVideoView:  State: {} ({})'.format(self.MediaStateNames.get(self._mediaObj.getState(), ''), self._mediaObj.getState()))
		Logger.info('VlcVideoView:  Type: {} ({})'.format(self.MediaTypeNames.get(self._mediaObj.getType(), ''), self._mediaObj.getType()))
		Logger.info('VlcVideoView:  Parsed: {}'.format(self._mediaObj.isParsed()))
		Logger.info('VlcVideoView:  Duration: {}'.format(self._mediaObj.getDuration()))
		Logger.info('VlcVideoView:  Tracks: {}'.format(self._mediaObj.getTrackCount()))
		for trackN in xrange(0, self._mediaObj.getTrackCount()):
			track = self._mediaObj.getTrack(trackN)
			Logger.info('VlcVideoView:  Track[{}].type: {} ({}), id: {}, codec: {}, bitrate: {}, lang: {}, descr: {}'.format(
						trackN, self.TrackTypeNames.get(track.type, '?'), track.type,
						track.id, track.codec, track.bitrate, track.language, track.description
			))
		for name, meta_id in [
						('Title',  jVlcMediaMeta.Title),
						('Artist', jVlcMediaMeta.Artist),
						('Descr',  jVlcMediaMeta.Description),
						('Data',   jVlcMediaMeta.Date),
		]:
			meta = self._mediaObj.getMeta(meta_id)
			if meta is not None:
				Logger.info('VlcVideoView: Media: Meta.{}: {}'.format(name, meta))