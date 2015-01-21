'''
Video GI
========

Implementation of VideoBase with using pygi / gstreamer. Pygi is both
compatible with Python 2 and 3.
'''

#
# Important notes: you must take care of glib event + python. If you connect()
# directly an event to a python object method, the object will be ref, and will
# be never unref.
# To prevent memory leak, you must connect() to a func, and you might want to
# pass the referenced object with weakref()
#

from gi.repository import Gst
from functools import partial
from os.path import realpath
from threading import Lock
from weakref import ref
from kivy.compat import PY2
from kivy.core.video import VideoBase
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from kivy.support import install_gobject_iteration
from ctypes import Structure, c_void_p, c_int, string_at
import atexit

if PY2:
    from urllib import pathname2url
else:
    from urllib.request import pathname2url

# initialize the video/gi. if the older version is used, don't use video_gi.
Gst.init(None)
version = Gst.version()
if version < (1, 0, 0, 0):
    raise Exception('Cannot use video_gi, Gstreamer < 1.0 is not supported.')
Logger.info('VideoGi: Using Gstreamer {}'.format(
    '.'.join(['{}'.format(x) for x in Gst.version()])))
install_gobject_iteration()


class _MapInfo(Structure):
    _fields_ = [
        ('memory', c_void_p),
        ('flags', c_int),
        ('data', c_void_p)]
        # we don't care about the rest


def _gst_new_buffer(obj, appsink):
    obj = obj()
    if not obj:
        return
    with obj._buffer_lock:
        obj._buffer = obj._appsink.emit('pull-sample')
    return False


def _on_gst_message(bus, message):
    Logger.trace('VideoGi: (bus) {}'.format(message))
    # log all error messages
    if message.type == Gst.MessageType.ERROR:
        error, debug = list(map(str, message.parse_error()))
        Logger.error('VideoGi: {}'.format(error))
        Logger.debug('VideoGi: {}'.format(debug))


def _on_gst_eos(obj, *largs):
    obj = obj()
    if not obj:
        return
    obj._do_eos()


def _on_videogi_unref(obj):
    if obj in VideoGi._instances:
        VideoGi._instances.remove(obj)


class VideoGi(VideoBase):

    _instances = []

    def __init__(self, **kwargs):
        self._buffer_lock = Lock()
        self._buffer = None
        self._texture = None
        self._gst_init()
        wk = ref(self, _on_videogi_unref)
        VideoGi._instances.append(wk)
        super(VideoGi, self).__init__(**kwargs)

    def _gst_init(self):
        # self._appsink will receive the buffers so we can upload them to GPU
        self._appsink = Gst.ElementFactory.make('appsink', '')
        self._appsink.props.caps = Gst.caps_from_string(
            'video/x-raw,format=RGB')

        self._appsink.props.async = True
        self._appsink.props.drop = True
        self._appsink.props.qos = True
        self._appsink.props.emit_signals = True
        self._appsink.connect('new-sample', partial(
            _gst_new_buffer, ref(self)))

        # playbin, takes care of all, loading, playing, etc.
        self._playbin = Gst.ElementFactory.make('playbin', 'playbin')
        self._playbin.props.video_sink = self._appsink

        # gstreamer bus, to attach and listen to gst messages
        self._bus = self._playbin.get_bus()
        self._bus.add_signal_watch()
        self._bus.connect('message', _on_gst_message)
        self._bus.connect('message::eos', partial(
            _on_gst_eos, ref(self)))

    def _update_texture(self, sample):
        # texture will be updated with newest buffer/frame

        # read the data from the buffer memory
        mapinfo = data = None
        try:
            buf = sample.get_buffer()
            result, mapinfo = buf.map(Gst.MapFlags.READ)

            # We cannot get the data out of mapinfo, using Gst 1.0.6 + Gi 3.8.0
            # related bug report:
            #     https://bugzilla.gnome.org/show_bug.cgi?id=678663
            # ie: mapinfo.data is normally a char*, but here, we have an int
            # So right now, we use ctypes instead to read the mapinfo ourself.
            addr = mapinfo.__hash__()
            c_mapinfo = _MapInfo.from_address(addr)

            # now get the memory
            data = string_at(c_mapinfo.data, mapinfo.size)
        finally:
            if mapinfo is not None:
                buf.unmap(mapinfo)

        # upload the data to the GPU
        info = sample.get_caps().get_structure(0)
        size = info.get_value('width'), info.get_value('height')

        # texture is not allocated yet, create it first
        if not self._texture:
            self._texture = Texture.create(size=size, colorfmt='rgb')
            self._texture.flip_vertical()
            self.dispatch('on_load')

        if self._texture:
            self._texture.blit_buffer(data, size=size, colorfmt='rgb')

    def _update(self, dt):
        buf = None
        with self._buffer_lock:
            buf = self._buffer
            self._buffer = None
        if buf is not None:
            self._update_texture(buf)
            self.dispatch('on_frame')

    def unload(self):
        self._playbin.set_state(Gst.State.NULL)
        self._buffer = None
        self._texture = None

    def load(self):
        Logger.debug('VideoGi: Load <{}>'.format(self._filename))
        self._playbin.set_state(Gst.State.NULL)
        self._playbin.props.uri = self._get_uri()
        self._playbin.set_state(Gst.State.READY)

    def stop(self):
        self._state = ''
        self._playbin.set_state(Gst.State.PAUSED)

    def pause(self):
        self._state = 'paused'
        self._playbin.set_state(Gst.State.PAUSED)

    def play(self):
        self._state = 'playing'
        self._playbin.set_state(Gst.State.PLAYING)

    def seek(self, percent):
        seek_t = percent * self._get_duration() * 10e8
        seek_format = Gst.Format.TIME
        seek_flags = Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT
        self._playbin.seek_simple(seek_format, seek_flags, seek_t)

        #if pipeline is not playing, we need to pull pre-roll to update frame
        if not self._state == 'playing':
            with self._buffer_lock:
                self._buffer = self._appsink.emit('pull-preroll')

    def _get_uri(self):
        uri = self.filename
        if not uri:
            return
        if not '://' in uri:
            uri = 'file:' + pathname2url(realpath(uri))
        return uri

    def _get_position(self):
        try:
            ret, value = self._appsink.query_position(Gst.Format.TIME)
            if ret:
                return value / float(Gst.SECOND)
        except:
            pass
        return -1

    def _get_duration(self):
        try:
            ret, value = self._playbin.query_duration(Gst.Format.TIME)
            if ret:
                return value / float(Gst.SECOND)
        except:
            pass
        return -1

    def _get_volume(self):
        self._volume = self._playbin.props.volume
        return self._volume

    def _set_volume(self, volume):
        self._playbin.props.volume = volume
        self._volume = volume


@atexit.register
def video_gi_clean():
    # if we leave the python process with some video running, we can hit a
    # segfault. This is forcing the stop/unload of all remaining videos before
    # exiting the python process.
    for weakvideo in VideoGi._instances:
        video = weakvideo()
        if video:
            video.stop()
            video.unload()
