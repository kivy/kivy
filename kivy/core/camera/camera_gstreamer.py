'''
GStreamer Camera: Implement CameraBase with GStreamer
'''

__all__ = ('CameraGStreamer', )

from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase

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
        self._pipeline = None
        self._camerasink = None
        self._decodebin = None
        self._texturesize = None
        self._video_src = kwargs.get('video_src', 'v4l2src')
        super(CameraGStreamer, self).__init__(**kwargs)

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

        GL_CAPS = 'video/x-raw-rgb,red_mask=(int)0xff0000,' + \
                  'green_mask=(int)0x00ff00,blue_mask=(int)0x0000ff'
        pl = '%s ! decodebin name=decoder ! ffmpegcolorspace ! appsink ' + \
             'name=camerasink emit-signals=True caps=%s'
        self._pipeline = gst.parse_launch(pl % (video_src, GL_CAPS))
        self._camerasink = self._pipeline.get_by_name('camerasink')
        self._camerasink.connect('new-buffer', self._gst_new_buffer)
        self._decodebin = self._pipeline.get_by_name('decoder')

        if self._camerasink and not self.stopped:
            self.start()

    def _gst_new_buffer(self, *largs):
        self._format = 'rgb'
        frame = self._camerasink.emit('pull-buffer')
        if frame is None:
            return
        self._buffer = frame.data
        if self._texturesize is None:
            # try to get the camera image size
            for x in self._decodebin.src_pads():
                for cap in x.get_caps():
                    self._texturesize = (cap['width'], cap['height'])
                    Clock.schedule_once(self._update)
                    return
        Clock.schedule_once(self._update)

    def start(self):
        super(CameraGStreamer, self).start()
        self._pipeline.set_state(gst.STATE_PLAYING)

    def stop(self):
        super(CameraGStreamer, self).stop()
        self._pipeline.set_state(gst.STATE_PAUSED)

    def _update(self, dt):
        if self._buffer is None:
            return
        if self._texture is None and self._texturesize is not None:
            self._texture = Texture.create(
                size=self._texturesize, colorfmt='rgb')
            self._texture.flip_vertical()
            self.dispatch('on_load')
        self._copy_to_gpu()
