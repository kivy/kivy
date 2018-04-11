'''
Raspberry Pi Camera: Implement CameraBase with Raspberry Pi's MMAL
'''

from kivy.lib.vidcore_lite import bcm, egl


__all__ = ('CameraRaspberryPi')

from picamera import mmal, mmalobj as mo
from kivy.clock import Clock, mainthread
from kivy.graphics.texture import Texture
from kivy.graphics import Fbo, Callback, Rectangle
from kivy.core.camera import CameraBase
from kivy.lib.vidcore_lite import egl
import threading
import ctypes
from queue import Queue
import time


class CameraRaspberryPi(CameraBase):
    """
    Implementation of CameraBase using Raspberry Pi MMAL API
    """

    _update_ev = None
    _current_img = None

    def __init__(self, **kwargs):
        self.lock = threading.Lock()
        self.buffers_queue = Queue(maxsize=2)
        self.fps = 20.
        self._mmal_camera = None
        super(CameraRaspberryPi, self).__init__(**kwargs)

    def __del__(self):
        self._release_camera()

    def _release_camera(self):
        if self._mmal_camera is None:
            return

        self.stop()
        self._mmal_camera.release()
        self._mmal_camera = None

        self._texture = None
        del self._fbo, self._camera_texture

    def stop(self):
        super(CameraRaspberryPi, self).stop()

        if self._mmal_camera is not None:
            self._mmal_camera.outputs[0].disable()

        while not self.buffers_queue.empty():
            buf = self.buffers_queue.get()
            buf.release()


    def init_camera(self):
        self._mmal_camera = mo.MMALCamera()
        width, height = self._resolution

#        self._resolution = (1280, 720)
#        width = 1280
#        height = 720

        camera_config = self._mmal_camera.control.params[mmal.MMAL_PARAMETER_CAMERA_CONFIG]
        cc = camera_config
        cc.max_stills_w = width
        cc.max_stills_h = height
        cc.stills_yuv422 = 0
        cc.one_shot_stills = 0
        cc.max_preview_video_w = width
        cc.max_preview_video_h = height
        cc.num_preview_video_frames = 3
        cc.stills_capture_circular_buffer_height = 0
        cc.fast_preview_resume = 0
        cc.use_stc_timestamp = mmal.MMAL_PARAM_TIMESTAMP_MODE_RESET_STC
        self._mmal_camera.control.params[mmal.MMAL_PARAMETER_CAMERA_CONFIG] = cc


        self._mmal_camera.control.enable()
        self._mmal_camera.outputs[0].format = mmal.MMAL_ENCODING_OPAQUE
        self._mmal_camera.outputs[0].framesize = (width, height)
        self._mmal_camera.outputs[0].framerate = self.fps
        self._mmal_camera.outputs[0].params[mmal.MMAL_PARAMETER_ZERO_COPY] = True

        self._mmal_camera.outputs[0].commit()

        self._camera_texture = Texture(width=width, height=height,
                                target=egl._constants.GL_TEXTURE_EXTERNAL_OES)

        self._fbo = Fbo(size=self._resolution)
        self._fbo.shader.fs = '''
            #extension GL_OES_EGL_image_external : require
            #ifdef GL_ES
                precision highp float;
            #endif

            /* Outputs from the vertex shader */
            varying vec4 frag_color;
            varying vec2 tex_coord0;

            /* uniform texture samplers */
            uniform sampler2D texture0;
            uniform samplerExternalOES texture1;

            void main()
            {
                gl_FragColor = texture2D(texture1, tex_coord0);
            }
        '''
        with self._fbo:
            self._texture_cb = Callback(lambda instr:
                                        self._camera_texture.bind)
            Rectangle(size=self._resolution)

    def start(self):
        super(CameraRaspberryPi, self).start()

        self._update_ev = Clock.schedule_interval(self._update, 1 / self.fps)

        self._mmal_camera.outputs[0].enable(self._new_frame_callback)


    def _refresh_fbo(self):
        self._texture_cb.ask_update()
        self._fbo.draw()


    def _new_frame_callback(self, port, buf):
        if self.buffers_queue.full():
            old_buf = self.buffers_queue.get()
            old_buf.release()
#            self._mmal_camera.outputs[0]._pool.send_buffer(block=True)

        buf.acquire()
        self.buffers_queue.put(buf)

        return False


    @mainthread
    def _update(self, dt):
        if not self.buffers_queue.empty():
            buf = self.buffers_queue.get()

            self._camera_texture.bind()

            if self._current_img is not None:
                egl.DestroyImageKHR (self._current_img)
                _current_img = None

            self._current_img = egl.CreateImageKHR (ctypes.c_void_p.from_buffer(buf._buf[0].data).value)

            egl.ImageTargetTexture2DOES(egl._constants.GL_TEXTURE_EXTERNAL_OES, self._current_img);

            buf.release()
#            self._mmal_camera.outputs[0]._pool.send_buffer(block=True)

            self._refresh_fbo()
            if self._texture is None:
                self._texture = self._fbo.texture
                self.dispatch('on_load')

            self.dispatch('on_texture')
