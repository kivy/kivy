from jnius import autoclass, PythonJavaClass, java_method
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase


Camera = autoclass('android.hardware.Camera')
SurfaceTexture = autoclass('android.graphics.SurfaceTexture')
ImageFormat = autoclass('android.graphics.ImageFormat')


class PreviewCallback(PythonJavaClass):
    """
    Interface used to get back the preview frame of the Android Camera
    """
    __javainterfaces__ = ('android.hardware.Camera$PreviewCallback', )

    def __init__(self, callback):
        super(PreviewCallback, self).__init__()
        self.callback = callback

    @java_method('([BLandroid/hardware/Camera;)V')
    def onPreviewFrame(self, data, camera):
        self.callback(data, camera)


class CameraAndroid(CameraBase):
    """
    Implementation of CameraBase using Android API
    """

    def __init__(self, **kwargs):
        self._android_camera = None
        self._surface_texture = SurfaceTexture(-1)
        self._preview_cb = PreviewCallback(self._on_preview_frame)
        super(CameraAndroid, self).__init__(**kwargs)

    def init_camera(self):
        self._android_camera = Camera.open(self._index)
        params = self._android_camera.getParameters()
        width, height = self._resolution
        params.setPreviewSize(width, height)
        self._android_camera.setParameters(params)
        #self._android_camera.setDisplayOrientation()

        pf = params.getPreviewFormat()
        assert(pf == ImageFormat.NV21)  # default format is NV21
        bpp = ImageFormat.getBitsPerPixel(pf) / 8.
        for k in range(2):  # double buffer
            buf = '\x00' * int(width * height * bpp)
            self._android_camera.addCallbackBuffer(buf)

        self._android_camera.setPreviewTexture(self._surface_texture)
        self._android_camera.setPreviewCallbackWithBuffer(self._preview_cb)

    def _on_preview_frame(self, data, camera):
        import numpy as np
        import cv2

        buf = data.tostring()
        self._android_camera.addCallbackBuffer(data)  # add buffer back for reuse
        w, h = self._resolution
        buf = np.fromstring(buf, 'uint8').reshape((h+h/2, w))
        self._buffer = cv2.cvtColor(buf, 92).tostring()  # NV21 -> RGB
        Clock.schedule_once(self._update)

    def start(self):
        super(CameraAndroid, self).start()
        self._android_camera.startPreview()

    def stop(self):
        self._android_camera.stopPreview()
        super(CameraAndroid, self).stop()

    def _update(self, dt):
        if self._buffer is None:
            return
        if self._texture is None:
            self._texture = Texture.create(size=self._resolution, colorfmt=self._format)
            self._texture.flip_vertical()
            self.dispatch('on_load')
        self._copy_to_gpu()

