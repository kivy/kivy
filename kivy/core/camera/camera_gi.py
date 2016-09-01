'''
Gi Camera
=========

Implement CameraBase with Gi / Gstreamer, working on both Python 2 and 3
'''

__all__ = ('CameraGi', )

from gi.repository import Gst
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase
from kivy.support import install_gobject_iteration
from kivy.logger import Logger
from ctypes import Structure, c_void_p, c_int, string_at
from weakref import ref
import atexit

# initialize the camera/gi. if the older version is used, don't use camera_gi.
Gst.init(None)
version = Gst.version()
if version < (1, 0, 0, 0):
    raise Exception('Cannot use camera_gi, Gstreamer < 1.0 is not supported.')
Logger.info('CameraGi: Using Gstreamer {}'.format(
    '.'.join(['{}'.format(x) for x in Gst.version()])))
install_gobject_iteration()


class _MapInfo(Structure):
    _fields_ = [
        ('memory', c_void_p),
        ('flags', c_int),
        ('data', c_void_p)]
        # we don't care about the rest


def _on_cameragi_unref(obj):
    if obj in CameraGi._instances:
        CameraGi._instances.remove(obj)


class CameraGi(CameraBase):
    '''Implementation of CameraBase using GStreamer

    :Parameters:
        `video_src`: str, default is 'v4l2src'
            Other tested options are: 'dc1394src' for firewire
            dc camera (e.g. firefly MV). Any gstreamer video source
            should potentially work.
            Theoretically a longer string using "!" can be used
            describing the first part of a gstreamer pipeline.
    '''

    _instances = []

    def __init__(self, **kwargs):
        self._pipeline = None
        self._camerasink = None
        self._decodebin = None
        self._texturesize = None
        self._video_src = kwargs.get('video_src', 'v4l2src')
        wk = ref(self, _on_cameragi_unref)
        CameraGi._instances.append(wk)
        super(CameraGi, self).__init__(**kwargs)

    def init_camera(self):
        # TODO: This doesn't work when camera resolution is resized at runtime.
        # There must be some other way to release the camera?
        if self._pipeline:
            self._pipeline = None

        video_src = self._video_src
        if video_src == 'v4l2src':
            video_src += ' device=/dev/video%d' % self._index
        elif video_src == 'dc1394src':
            video_src += ' camera-number=%d' % self._index

        if Gst.version() < (1, 0, 0, 0):
            caps = ('video/x-raw-rgb,red_mask=(int)0xff0000,'
                    'green_mask=(int)0x00ff00,blue_mask=(int)0x0000ff')
            pl = ('{} ! decodebin name=decoder ! ffmpegcolorspace ! '
                  'appsink name=camerasink emit-signals=True caps={}')
        else:
            caps = 'video/x-raw,format=RGB'
            pl = '{} ! decodebin name=decoder ! videoconvert ! appsink ' + \
                 'name=camerasink emit-signals=True caps={}'

        self._pipeline = Gst.parse_launch(pl.format(video_src, caps))
        self._camerasink = self._pipeline.get_by_name('camerasink')
        self._camerasink.connect('new-sample', self._gst_new_sample)
        self._decodebin = self._pipeline.get_by_name('decoder')

        if self._camerasink and not self.stopped:
            self.start()

    def _gst_new_sample(self, *largs):
        sample = self._camerasink.emit('pull-sample')
        if sample is None:
            return False

        self._sample = sample

        if self._texturesize is None:
            # try to get the camera image size
            for pad in self._decodebin.srcpads:
                s = pad.get_current_caps().get_structure(0)
                self._texturesize = (
                    s.get_value('width'),
                    s.get_value('height'))
                Clock.schedule_once(self._update)
                return False

        Clock.schedule_once(self._update)
        return False

    def start(self):
        super(CameraGi, self).start()
        self._pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        super(CameraGi, self).stop()
        self._pipeline.set_state(Gst.State.PAUSED)

    def unload(self):
        self._pipeline.set_state(Gst.State.NULL)

    def _update(self, dt):
        sample, self._sample = self._sample, None
        if sample is None:
            return

        if self._texture is None and self._texturesize is not None:
            self._texture = Texture.create(
                size=self._texturesize, colorfmt='rgb')
            self._texture.flip_vertical()
            self.dispatch('on_load')

        # decode sample
        # read the data from the buffer memory
        try:
            buf = sample.get_buffer()
            result, mapinfo = buf.map(Gst.MapFlags.READ)

            # We cannot get the data out of mapinfo, using Gst 1.0.6 + Gi 3.8.0
            # related bug report:
            # https://bugzilla.gnome.org/show_bug.cgi?id=6t8663
            # ie: mapinfo.data is normally a char*, but here, we have an int
            # So right now, we use ctypes instead to read the mapinfo ourself.
            addr = mapinfo.__hash__()
            c_mapinfo = _MapInfo.from_address(addr)

            # now get the memory
            self._buffer = string_at(c_mapinfo.data, mapinfo.size)
            self._copy_to_gpu()
        finally:
            if mapinfo is not None:
                buf.unmap(mapinfo)


@atexit.register
def camera_gi_clean():
    # if we leave the python process with some video running, we can hit a
    # segfault. This is forcing the stop/unload of all remaining videos before
    # exiting the python process.
    for weakcamera in CameraGi._instances:
        camera = weakcamera()
        if isinstance(camera, CameraGi):
            camera.stop()
            camera.unload()
