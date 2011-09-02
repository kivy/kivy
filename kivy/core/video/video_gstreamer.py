'''
VideoGStreamer: implementation of VideoBase with GStreamer
'''

# XXX Why using weakref ?
# Cause connect() will refer to self, that represent VideoGStreamer.
# For example, you'll have a cyclic ref: VideoGstreamer ->
# discoverer object -> _discovered -> VideoGstreamer
# For unknown reason, this cyclic is never freed.

try:
    import pygst
    if not hasattr(pygst, '_gst_already_checked'):
        pygst.require('0.10')
        pygst._gst_already_checked = True
    import gst
except:
    raise

from threading import Lock
from . import VideoBase
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from gst.extend import discoverer
from functools import partial
from weakref import ref

# install the gobject iteration
from kivy.support import install_gobject_iteration
install_gobject_iteration()


def _discovered(obj, d, is_media):
    obj = obj()
    if not obj:
        return
    obj._is_audio = d.is_audio
    obj._is_video = d.is_video
    obj._do_load = True
    obj._discoverer.disconnect(obj._discoverer_sid)
    obj._discoverer.set_state(gst.STATE_NULL)
    obj._discoverer = None


def _on_gst_message(obj, bus, message):
    obj = obj()
    if not obj:
        return
    if message.type == gst.MESSAGE_ASYNC_DONE:
        obj._pipeline_canplay = True
    elif message.type == gst.MESSAGE_EOS:
        obj._do_eos()


def _gst_new_pad(obj, dbin, pad, *largs):
    obj = obj()
    if not obj:
        return
    # a new pad from decoder ?
    # if it's a video, connect decoder -> colorspace
    c = pad.get_caps().to_string()
    try:
        if c.startswith('video'):
            dbin.link(obj._colorspace)
        elif c.startswith('audio'):
            if obj._is_audio is False:
                obj._is_audio = True
                obj._pipeline.add(obj._audiosink, obj._volumesink)
                gst.element_link_many(obj._volumesink, obj._audiosink)
            dbin.link(obj._volumesink)
    except:
        pass


def _gst_new_buffer(obj, appsink):
    obj = obj()
    if not obj:
        return
    # new buffer is comming, pull it.
    with obj._buffer_lock:
        obj._buffer = appsink.emit('pull-buffer')


class VideoGStreamer(VideoBase):
    '''VideoBase implementation using GStreamer
       See: (http://gstreamer.freedesktop.org/)
    '''

    __slots__ = ('_pipeline', '_decoder', '_videosink', '_colorspace',
                 '_videosize', '_buffer_lock', '_audiosink', '_volumesink',
                 '_is_audio', '_is_video', '_do_load', '_pipeline_canplay',
                 '_discoverer', '_discoverer_sid', '_colorfmt',
                 '_exception_position')

    def __init__(self, **kwargs):
        self._pipeline = None
        self._decoder = None
        self._videosink = None
        self._colorspace = None
        self._audiosink = None
        self._volumesink = None
        self._is_audio = None
        self._is_video = None
        self._do_load = None
        self._colorfmt = kwargs.get('colorfmt', None)
        self._pipeline_canplay = False
        self._buffer_lock = Lock()
        self._videosize = (0, 0)
        self._exception_position = False
        super(VideoGStreamer, self).__init__(**kwargs)

    def _do_eos(self):
        # reset to start for next play
        self._pipeline.seek_simple(
            gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, 0)
        self.dispatch('on_eos')
        super(VideoGStreamer, self)._do_eos()

    def stop(self):
        self._wantplay = False
        if self._pipeline is None:
            return
        self._pipeline.set_state(gst.STATE_PAUSED)
        self._state = ''
        super(VideoGStreamer, self).stop()

    def play(self):
        self._wantplay = True
        if self._pipeline is None:
            return
        self._pipeline.set_state(gst.STATE_PAUSED)
        super(VideoGStreamer, self).play()
        self._state = ''

    def unload(self):
        if self._pipeline is None:
            return
        self._pipeline.set_state(gst.STATE_NULL)
        self._pipeline.get_state() # block until the null is ok
        self._pipeline = None
        self._decoder = None
        self._videosink = None
        self._texture = None
        self._audiosink = None
        self._volumesink = None
        self._is_audio = None
        self._is_video = None
        self._do_load = None
        self._pipeline_canplay = False
        self._state = ''

    def _is_remote(self, fn):
        return fn.split(':')[0] in ('http', 'https')

    def load(self):
        # ensure that nothing is loaded before.
        self.unload()

        # discover the media
        if self._is_remote(self._filename):
            self._is_audio = False
            self._is_video = True
            self._do_load = True
        else:
            self._discoverer = discoverer.Discoverer(self._filename)
            self._discoverer_sid = self._discoverer.connect('discovered',
                           partial(_discovered, ref(self)))
            self._discoverer.discover()

    def _really_load(self):
        # create the pipeline
        self._pipeline = gst.Pipeline()

        # create bus
        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect('message', partial(_on_gst_message, ref(self)))

        # hardcoded to check which decoder is better
        if self._filename.split(':')[0] in ('http', 'https', 'file'):
            # network decoder
            self._decoder = gst.element_factory_make('uridecodebin', 'decoder')
            self._decoder.set_property('use-buffering', True)
            self._decoder.set_property('uri', self._filename)
            self._decoder.connect('pad-added', partial(_gst_new_pad, ref(self)))
            self._pipeline.add(self._decoder)
        else:
            # local decoder
            filesrc = gst.element_factory_make('filesrc')
            filesrc.set_property('location', self._filename)
            self._decoder = gst.element_factory_make('decodebin', 'decoder')
            self._decoder.connect('new-decoded-pad',
                                  partial(_gst_new_pad, ref(self)))
            self._pipeline.add(filesrc, self._decoder)
            gst.element_link_many(filesrc, self._decoder)

        # create colospace information
        self._colorspace = gst.element_factory_make('ffmpegcolorspace')

        # will extract video/audio
        self._videosink = gst.element_factory_make('appsink', 'videosink')
        self._videosink.set_property('emit-signals', True)
        if not self._colorfmt:
            self._colorfmt = 'rgb'
            caps_str = ('video/x-raw-rgb,red_mask=(int)0xff0000,'
                        'green_mask=(int)0x00ff00,blue_mask=(int)0x0000ff')
            caps = gst.Caps(caps_str)
            self._videosink.set_property('caps', caps)
        self._videosink.set_property('drop', True)
        #self._videosink.set_property('render-delay', 1000000000)
        #self._videosink.set_property('max-lateness', 1000000000)
        self._videosink.connect('new-buffer',
                                partial(_gst_new_buffer, ref(self)))
        self._audiosink = gst.element_factory_make('autoaudiosink', 'audiosink')
        self._volumesink = gst.element_factory_make('volume', 'volume')

        # connect colorspace -> appsink
        if self._is_video:
            self._pipeline.add(self._colorspace, self._videosink)
            gst.element_link_many(self._colorspace, self._videosink)

        if self._is_audio:
            self._pipeline.add(self._audiosink, self._volumesink)
            gst.element_link_many(self._volumesink, self._audiosink)

        # set to paused, for loading the file, and get the size information.
        self._pipeline.set_state(gst.STATE_PAUSED)

        # be sync if asked
        if not self._async:
            self._pipeline.get_state()

    def seek(self, percent):
        if not self._pipeline:
            return
        self._pipeline.seek_simple(
            gst.FORMAT_PERCENT,
            gst.SEEK_FLAG_FLUSH,
            percent)

    def _get_position(self):
        if self._videosink is None:
            return 0
        try:
            # I don't understand, on ubuntu, the FORMAT_TIME is laggy, and we
            # have a delay of 1 second. In addition, the FORMAT_BYTES return
            # time, not bytes...
            # I've also tryed:
            #   vs = self._videosink
            #   bduration = vs.query_duration(gst.FORMAT_BYTES)[0]
            #   bposition = vs.query_position(gst.FORMAT_BYTES)[0]
            #   return (bposition / float(bduration)) * self._get_duration()
            # But query_duration failed with FORMAT_BYTES.
            # Using FORMAT_DEFAULT result to have different information in
            # duration and position. Unexplained right now.

            # Even more weird, we ask for BYTES, but it can return TIME...
            value, fmt = self._videosink.query_position(gst.FORMAT_BYTES)
            if fmt is gst.FORMAT_BYTES:
                return value / 10e9
            elif fmt is gst.FORMAT_TIME:
                return value / 10e8
        except Exception:
            # Sometime, video query failed when asking FORMAT_BYTES.
            # so retry with FORMAT_TIME, even if it's laggy
            try:
                value, fmt = self._videosink.query_position(gst.FORMAT_TIME)
                return value / 10e8
            except Exception:
                if not self._exception_position:
                    Logger.warning(
                        'Failed to query position in video %s' % self._filename)
                    self._exception_position = True
                return 0

    def _get_duration(self):
        if self._videosink is None:
            return 0
        try:
            return self._videosink.query_duration(gst.FORMAT_TIME)[0] / 10e8
        except:
            return 0

    def _get_volume(self):
        if self._audiosink is not None:
            self._volume = self._volumesink.get_property('volume')
        else:
            self._volume = 1.
        return self._volume

    def _set_volume(self, volume):
        if self._audiosink is not None:
            self._volumesink.set_property('volume', volume)
            self._volume = max(volume, .0000001)

    def _update(self, dt):
        if self._do_load:
            self._really_load()
            self._do_load = False

        # no video sink ?
        if self._videosink is None:
            return

        # get size information first to create the texture
        if self._texture is None:
            try:
                for i in self._decoder.src_pads():
                    cap = i.get_caps()[0]
                    structure_name = cap.get_name()
                    if structure_name.startswith('video') and \
                            'width' in cap.keys():
                        self._videosize = (cap['width'], cap['height'])
                        self._texture = Texture.create(
                            size=self._videosize, colorfmt=self._colorfmt)
                        self._texture.flip_vertical()
                        self.dispatch('on_load')
            except TypeError:
                # mostly resync, we'll redo it later.
                pass

        # no texture again ?
        if self._texture is None:
            return

        # ok, we got a texture, user want play ?
        if self._wantplay and self._pipeline_canplay:
            self._pipeline.set_state(gst.STATE_READY)
            self._state = 'ready'
            self._wantplay = False

        if self._state == 'ready':
            state = self._pipeline.get_state(0)
            if state[1] == gst.STATE_READY:
                self._pipeline.set_state(gst.STATE_PLAYING)
                self._state = 'playing'

        # update needed ?
        with self._buffer_lock:
            if self._buffer is not None:
                self._texture.blit_buffer(
                    self._buffer.data, size=self._videosize,
                    colorfmt=self._colorfmt)
                self._buffer = None
                self.dispatch('on_frame')
