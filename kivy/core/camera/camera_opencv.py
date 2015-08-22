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

__all__ = ['CameraOpenCV', ]


class CameraOpenCV(CameraBase):
    '''Implementation of CameraBase using OpenCV
    '''

    def __init__(self, **kwargs):
        self._format = 'bgr'
        self.capture = cv2.VideoCapture()
        super(CameraOpenCV, self).__init__(**kwargs)

    def init_camera(self):
        index = self._index
        width, height = self._resolution

        self.capture.open(index)
        self.capture.set(FRAME_WIDTH, width)
        self.capture.set(FRAME_HEIGHT, height)

        self.capture.grab()

        ok, frame = self.capture.read()

        if not ok:
            Logger.exception('OpenCV: Couldn\'t get initial image from Camera')

        frame_height = len(frame)
        frame_width = len(frame[0])

        self._resolution = frame_height, frame_width

        self.fps = self.capture.get(FPS)
        # needed because FPS determines rescheduling rate
        if self.fps <= 0:
            self.fps = 1 / 30.0

        if not self.stopped:
            self.start()

    def _update(self, delta):
        if self.stopped:
            # Don't update it camere stopped
            return
        if self._texture is None:
            # Create the initial texture
            self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self.dispatch('on_load')
        try:
            # Read buffer
            ok, frame = self.capture.read()
            self._buffer = frame.tostring()
            self._copy_to_gpu()
        except:
            Logger.exception('OpenCV: Couldn\'t get image from Camera')

    def start(self):
        super(CameraOpenCV, self).start()

        Clock.unschedule(self._update)
        Clock.schedule_interval(self._update, self.fps)

    def stop(self):
        super(CameraOpenCV, self).stop()
        Clock.unschedule(self._update)
