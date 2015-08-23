"""
OpenCV Camera: Implement CameraBase with OpenCV (cv2 module)
"""
#
# TODO: use threads or multiprocessing instead of dirty rescheduling
#
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase

import cv2
# TODO: confirm OSX support ?

from cv2 import (
    CAP_PROP_FRAME_WIDTH as FRAME_WIDTH,
    CAP_PROP_FRAME_HEIGHT as FRAME_HEIGHT,
    CAP_PROP_FPS as FPS,
)

__all__ = ['CaptureError', 'CameraOpenCV', ]


class CaptureError(RuntimeError):
    pass


class CameraOpenCV(CameraBase):
    '''Implementation of CameraBase using OpenCV
    '''

    def __init__(self, **kwargs):
        if __debug__:
            Logger.trace("initializing new video capture")

        self._format = 'bgr'
        self.capture = cv2.VideoCapture()

        if __debug__:
            Logger.trace("initialized capture instance")

        super(CameraOpenCV, self).__init__(**kwargs)

    def init_camera(self):
        index = self._index
        width, height = self._resolution

        self.capture.open(index)

        if __debug__:
            Logger.trace("opened cv2.VideoCapture({})".format(index))

        self.capture.set(FRAME_WIDTH, width)
        self.capture.set(FRAME_HEIGHT, height)

        self.capture.grab()

        ok, frame = self.capture.read()

        if not ok:
            Logger.exception('OpenCV: Couldn\'t get initial image from Camera')
        else:
            if __debug__:
                Logger.trace("got initial frame from camera")

        frame_height = len(frame)
        frame_width = len(frame[0])

        if __debug__:
            Logger.trace("frame size: {}x{}".format(frame_height, frame_width))

        self._resolution = frame_height, frame_width

        self.fps = self.capture.get(FPS)
        # needed because FPS determines rescheduling rate
        if self.fps <= 0:
            self.fps = 1 / 30.0

        if not self.stopped:
            if __debug__:
                Logger.trace("starting camera (initializing, and not open)")
            self.start()

    def _update(self, delta):
        if __debug__:
            Logger.trace("updating GPU buffer... (delta: {})".format(delta))

        if self.stopped:
            # Don't update it camere stopped
            if __debug__:
                Logger.trace(
                    "frame update skipped as camera is stopped"
                )
            return
        if self._texture is None:
            if __debug__:
                Logger.trace(
                    "creating initial texture"
                )
            # Create the initial texture
            self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self.dispatch('on_load')
        try:
            # Read buffer
            ok, frame = self.capture.read()
            if not ok:
                raise CaptureError("Could not read image from camera")
        except Exception as ex:
            Logger.exception(
                "Error while reading frame from camera : {}"
                .format(ex)
            )
        else:
            self._buffer = frame.tostring()

            if __debug__:
                Logger.trace("got new frame from camera")

            self._copy_to_gpu()

            if __debug__:
                Logger.trace(
                    "GPU buffer updated"
                )


    def start(self):
        if __debug__:
            Logger.trace("starting capture...")

        super(CameraOpenCV, self).start()

        if __debug__:
            Logger.trace(
                "unschedule update & reschedule with current FPS ({})"
                "".format(self.fps)
            )

        Clock.unschedule(self._update)
        Clock.schedule_interval(self._update, 1 / self.fps)

        if __debug__:
            Logger.trace("capture started")

    def stop(self):
        if __debug__:
            Logger.trace("stopping capture...")

        super(CameraOpenCV, self).stop()

        if __debug__:
            Logger.trace("unschedule next update")

        Clock.unschedule(self._update)

        if __debug__:
            Logger.trace("capture stopped")
