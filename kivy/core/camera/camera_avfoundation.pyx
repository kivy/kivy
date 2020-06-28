'''
AVFoundation Camera
===================

Camera implementation using AVFoundation framework for OSX / iOS
'''

__all__ = ['CameraAVFoundation']

cdef extern from "camera_avfoundation_implem.h":
    ctypedef void *camera_t
    camera_t avf_camera_init(int index, int width, int height)
    void avf_camera_deinit(camera_t camera)
    void avf_camera_update(camera_t camera)
    void avf_camera_start(camera_t camera)
    void avf_camera_stop(camera_t camera)
    void avf_camera_get_image(camera_t camera, int *width, int *height, int *rowsize, char **data)
    bint avf_camera_attempt_framerate_selection(camera_t camera, int fps)
    bint avf_camera_attempt_capture_preset(camera_t camera, char* preset)
    bint avf_camera_attempt_start_metadata_analysis(camera_t camera)
    void avf_camera_get_metadata(camera_t camera, char **metatype, char **data)
    bint avf_camera_have_new_metadata(camera_t camera);


from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase
from kivy.utils import platform


cdef class _AVStorage:
    cdef camera_t camera

    def __cinit__(self):
        self.camera = NULL


class CameraAVFoundation(CameraBase):
    '''Implementation of CameraBase using AVFoundation
    '''

    def __init__(self, **kwargs):
        self._storage = _AVStorage()
        self._update_ev = None
        self._metadata_callback = None
        super(CameraAVFoundation, self).__init__(**kwargs)

    def init_camera(self):
        cdef _AVStorage storage = <_AVStorage>self._storage
        storage.camera = avf_camera_init(
            self._index, self.resolution[0], self.resolution[1])

    def _update(self, dt):
        cdef _AVStorage storage = <_AVStorage>self._storage
        cdef int width, height, rowsize
        cdef char *data
        cdef char *metadata_type
        cdef char *metadata_data

        if self.stopped:
            return

        avf_camera_update(storage.camera)
        avf_camera_get_image(storage.camera,
            &width, &height, &rowsize, &data)

        if data == NULL:
            return

        self._resolution = (width, height)
        
        if self._texture is None or self._texture.size != self._resolution:
            if platform == 'ios':
                self._texture = Texture.create(self._resolution, colorfmt='bgra')
            else:
                self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self.dispatch('on_load')

        self._buffer = <bytes>data[:rowsize * height]
        self._format = 'bgra'
        self._copy_to_gpu()
        if self._metadata_callback:
            if avf_camera_have_new_metadata(storage.camera):
                avf_camera_get_metadata(storage.camera, &metadata_type, &metadata_data)
                self._metadata_callback(metadata_type, metadata_data)

    def start(self):
        cdef _AVStorage storage = <_AVStorage>self._storage
        super(CameraAVFoundation, self).start()
        if self._update_ev is not None:
            self._update_ev.cancel()
        self._update_ev = Clock.schedule_interval(self._update, 1 / 30.)
        avf_camera_start(storage.camera)

    def stop(self):
        cdef _AVStorage storage = <_AVStorage>self._storage
        super(CameraAVFoundation, self).stop()
        if self._update_ev is not None:
            self._update_ev.cancel()
            self._update_ev = None
        avf_camera_stop(storage.camera)

    def set_framerate(self, framerate):
        cdef _AVStorage storage = <_AVStorage>self._storage
        avf_camera_attempt_framerate_selection(storage.camera, framerate)

    def set_preset(self, preset):
        cdef _AVStorage storage = <_AVStorage>self._storage
        avf_camera_attempt_capture_preset(storage.camera, preset)

    def start_metadata_analysis(self, callback=None):
        cdef _AVStorage storage = <_AVStorage>self._storage
        self._metadata_callback = callback
        avf_camera_attempt_start_metadata_analysis(storage.camera)