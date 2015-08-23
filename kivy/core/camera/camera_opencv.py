"""
OpenCV Camera: Implement CameraBase with OpenCV (cv2 module)

Author: Hugo Geoffroy "pistache" <h.geoffroy@eden-3d.org>

"""
# Tasks
# ----
# - TODO: use threads or multiprocessing instead of rescheduling


# Imports
# -------
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase

from cv2 import (
    VideoCapture,
    CAP_PROP_FRAME_WIDTH as FRAME_WIDTH,
    CAP_PROP_FRAME_HEIGHT as FRAME_HEIGHT,
    CAP_PROP_FPS as FPS,
)

# Constants
# ---------
IMAGE_FORMAT = 'bgr'  # OpenCV image format


# Exports
# -------
__all__ = ['IMAGE_FORMAT', 'CaptureError', 'CameraOpenCV', ]


# Exception classes
# -----------------
class CaptureError(RuntimeError):
    """Raised by the Camera methods & scheduled routines. Should be catched and
    translated to a proper kivy logged exception, if it's possible to recover
    and continue.

    """
    def __init__(self, message, camera):
        """Initialize capture error exception. Store the camera as exception
        attributes.

        """
        self.camera = camera

        super().__init__(message)


# Camera provider class
# ---------------------
class CameraOpenCV(CameraBase):
    """Implementation of CameraBase using OpenCV

    Uses the :mod:`cv2` module, and its :class:`cv2.VideoCapture` class.

    """

    def __init__(self, **kwargs):
        """Initialize OpenCV Camera provider"""
        self.capture = VideoCapture()

        if __debug__:
            Logger.debug(
                "initializing capture ({})'"
                "".format(self.capture)
            )

        try:
            super(CameraOpenCV, self).__init__(**kwargs)
        except CaptureError as ex:
            Logger.exception(
                "Exception while initializing camera : {}"
                "".format(ex)
            )

    def init_camera(self):
        """Acquire camera and initialize capture

        """
        image_format = self._format = IMAGE_FORMAT
        index = self._index
        width, height = self._resolution

        if __debug__:
            Logger.debug(
                "initializing camera (index: {}, image format: {}), "
                "asking for size {}x{}"
                "".format(index, image_format, width, height)
            )

        self.capture.open(index)

        if __debug__:
            Logger.debug("opened camera, setting resolution")

        self.capture.set(FRAME_WIDTH, width)
        self.capture.set(FRAME_HEIGHT, height)

        if __debug__:
            Logger.debug("resolution set, grab & read...")

        self.capture.grab()

        ok, frame = self.capture.read()

        if not ok:
            raise CaptureError(
                "Could not read image from camera", self.capture
            )

        frame_height = len(frame)
        frame_width = len(frame[0])

        if __debug__:
            Logger.debug(
                "first frame size: {}x{}"
                "".format(frame_width, frame_height)
            )

        if width != frame_width or height != frame_height:
            if __debug__:
                Logger.debug(
                    "size corrected by camera : {}x{}"
                    "".format(frame_width, frame_height)
                )
            self._resolution = frame_width, frame_height

        self.fps = self.capture.get(FPS)

        # needed because FPS determines rescheduling rate
        if self.fps <= 0:
            Logger.warning(
                "invalid FPS ('{}') returned by camera, using 30 as default"
                "".format(self.fps)
            )
            self.fps = 1 / 30.0

        if not self.stopped:
            if __debug__:
                Logger.debug("starting camera (initializing)")
            self.start()

    def _release(self):
        """Release camera.

        This method unschedules frame update routines, then closes the capture
        the device and releases the camera.

        """
        if __debug__:
            Logger.debug("releasing camera...")

        if not self.stopped:
            self.stop()

        if __debug__:
            Logger.debug("scheduled stop of camera update tasks")

        self.capture.release()

        if __debug__:
            Logger.debug("released camera")

    def _update_frame(self, delta):
        """Update GPU buffer with camera image data.

        """
        if __debug__:
            Logger.debug("updating GPU buffer... (delta: {})".format(delta))

        if self.stopped:
            # Don't update it camere stopped
            if __debug__:
                Logger.debug(
                    "frame update skipped as camera is stopped"
                )
            return

        if self._texture is None:
            if __debug__:
                Logger.debug(
                    "creating initial texture"
                )
            # Create the initial texture
            self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self.dispatch('on_load')
        try:
            # Read buffer
            ok, frame = self.capture.read()

            # ok: boolean indicating whether frame reading was successfull
            # frame: numpy matrix of pixel color values

            if not ok:
                raise CaptureError("Could not read image from camera", self)

        except Exception as ex:
            Logger.exception(
                "Error while reading frame from camera : {}"
                .format(ex)
            )
        else:
            self._buffer = frame.tostring()

            if __debug__:
                Logger.debug(
                    "got new frame from camera (size: {})"
                    "".format(len(self._buffer))
                )

            # this copies the image data to the OpenGL buffer
            #
            # (using Texture._blit_buffer)
            #
            self._copy_to_gpu()

            if __debug__:
                Logger.debug(
                    "GPU buffer updated"
                )

    def start(self):
        """Start frame updating.

        This method is not blocking, the update routine is just scheduled in
        Kivy's clock."""

        if not self.capture.isOpened():
            Logger.exception(
                "Camera is not open, cannot schedule frame updates",
            )
            return

        if __debug__:
            Logger.debug("starting capture...")

        super(CameraOpenCV, self).start()

        if __debug__:
            Logger.debug(
                "unschedule update & reschedule with current FPS ({})"
                "".format(self.fps)
            )

        Clock.unschedule(self._update_frame)
        Clock.schedule_interval(self._update_frame, 1 / self.fps)

        if __debug__:
            Logger.debug("capture started")

    def stop(self):
        """Stop frame updating. This does not release the camera.

        This method is not blocking, the update routine is just unscheduled
        from Kivy's clock.

        """
        if __debug__:
            Logger.debug("stopping capture...")

        super(CameraOpenCV, self).stop()

        if __debug__:
            Logger.debug("unschedule next update")

        Clock.unschedule(self._update_frame)

        if __debug__:
            Logger.debug("capture stopped")
