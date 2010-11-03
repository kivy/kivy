'''
GStreamer Camera: Implement CameraBase with GStreamer
'''

__all__ = ('CameraGStreamer', )

import kivy
from . import CameraBase
from kivy.core.gl import GL_RGB

try:
    import pygst
    if not hasattr(pygst, '_gst_already_checked'):
        pygst.require('0.10')
        pygst._gst_already_checked = True
    import gst
except:
    raise

# install the gobject iteration
from kivy.support import install_gobject_iteration
install_gobject_iteration()

class CameraGStreamer(CameraBase):
    '''Implementation of CameraBase using GStreamer

    :Parameters:
        `video_src` : str, default is 'v4l2src'
            Other tested options are: 'dc1394src' for firewire
            dc camera (e.g. firefly MV). Any gstreamer video source
            should potentially work.
            Theoretically a longer string using "!" can be used
            describing the first part of a gstreamer pipeline.
    '''

    def __init__(self, **kwargs):
        kwargs.setdefault('video_src', 'v4l2src')
        self._pipeline = None
        self._camerasink = None
        self._decodebin = None
        self._texturesize = None
        super(CameraGStreamer, self).__init__(**kwargs)

    def init_camera(self):
        # TODO: This does not work when camera resolution is resized at runtime...
        # there must be some other way to release the camera?
        if self._pipeline:
            self._pipeline = None

        GL_CAPS = 'video/x-raw-rgb,red_mask=(int)0xff0000,green_mask=(int)0x00ff00,blue_mask=(int)0x0000ff'
        self._pipeline = gst.parse_launch('%s ! decodebin name=decoder ! ffmpegcolorspace ! appsink name=camerasink emit-signals=True caps=%s' % (self.video_src, GL_CAPS) )
        self._camerasink = self._pipeline.get_by_name('camerasink')
        self._camerasink.connect('new-buffer', self._gst_new_buffer)
        self._decodebin = self._pipeline.get_by_name('decoder')

        if self._camerasink and not self.stopped:
            self.start()

    def _gst_new_buffer(self, *largs):
        self._format = GL_RGB
        frame = self._camerasink.emit('pull-buffer')
        if frame is None:
            return
        self._buffer = frame.data
        if self._texturesize is None:
            # try to get the camera image size
            for x in self._decodebin.src_pads():
                for cap in x.get_caps():
                    self._texturesize = (cap['width'], cap['height'])
                    return

    def start(self):
        self.stopped = False
        self._pipeline.set_state(gst.STATE_PLAYING)

    def stop(self):
        self.stopped = True
        self._pipeline.set_state(gst.STATE_PAUSED)

    def update(self):
        if self._buffer is None:
            return
        self._copy_to_gpu()
        if self._texture is None and self._texturesize is not None:
            w, h = self._texturesize
            self._texture = kivy.Texture.create(w, h, format=GL_RGB)
            self._texture.flip_vertical()
