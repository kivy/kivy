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
    bint avf_camera_update(camera_t camera)
    void avf_camera_start(camera_t camera)
    void avf_camera_stop(camera_t camera)
    void avf_camera_get_image(camera_t camera, int *width, int *height, int *rowsize, char **data)
    bint avf_camera_attempt_framerate_selection(camera_t camera, int fps)
    bint avf_camera_attempt_capture_preset(camera_t camera, char* preset)
    bint avf_camera_attempt_start_metadata_analysis(camera_t camera)
    void avf_camera_get_metadata(camera_t camera, char **metatype, char **data)
    bint avf_camera_have_new_metadata(camera_t camera);
    bint avf_camera_set_video_orientation(camera_t camera, int orientation)
    int avf_camera_get_device_orientation()
    void avf_camera_change_input(camera_t camera, int _cameraNum)
    void avf_camera_zoom_level(camera_t camera, float zoomLevel)
    char *avf_camera_documents_directory()
    void avf_camera_save_pixels(camera_t camera, unsigned char *pixels, int width, int height, char *path, float quality)


from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase
from kivy.utils import platform
from cython cimport view as cyview


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
        self._framerate = 30
        super(CameraAVFoundation, self).__init__(**kwargs)

    def __del__(self):
        self._release_camera()

    def init_camera(self):
        cdef _AVStorage storage = <_AVStorage>self._storage
        storage.camera = avf_camera_init(
            self._index, self.resolution[0], self.resolution[1])

    def _release_camera(self):
        cdef _AVStorage storage = <_AVStorage>self._storage
        if storage.camera != NULL:
            avf_camera_deinit(storage.camera)
            storage.camera = NULL

    @property
    def _scheduled_rate(self):
        # We're going 4 times faster the framerate to avoid frame skipping.
        return 1 / (self._framerate * 4)

    def _update(self, dt):
        cdef _AVStorage storage = <_AVStorage>self._storage
        cdef int width, height, rowsize
        cdef char *data
        cdef char *metadata_type
        cdef char *metadata_data
        cdef cyview.array cyarr

        if self.stopped:
            return

        if not avf_camera_update(storage.camera):
            return

        avf_camera_get_image(storage.camera,
            &width, &height, &rowsize, &data)

        if data == NULL:
            return

        cyarr = cyview.array(
            shape=(rowsize * height,),
            itemsize=sizeof(char),
            format="B",
            mode="c",
            allocate_buffer=False,
        )
        cyarr.data = data

        self._resolution = (width, height)
        
        if self._texture is None or self._texture.size != self._resolution:
            if platform == 'ios':
                self._texture = Texture.create(self._resolution, colorfmt='bgra')
            else:
                self._texture = Texture.create(self._resolution)
            self._texture.flip_vertical()
            self.dispatch('on_load')

        self._format = 'bgra'
        self._texture.blit_buffer(cyarr, colorfmt=self._format)
        self._copy_to_gpu()
        if self._metadata_callback:
            if avf_camera_have_new_metadata(storage.camera):
                avf_camera_get_metadata(storage.camera, &metadata_type, &metadata_data)
                self._metadata_callback(metadata_type, metadata_data)
    
    def _copy_to_gpu(self):
        self.dispatch('on_texture')

    def start(self):
        cdef _AVStorage storage = <_AVStorage>self._storage
        super(CameraAVFoundation, self).start()
        if self._update_ev is not None:
            self._update_ev.cancel()
        self._update_ev = Clock.schedule_interval(self._update, self._scheduled_rate)
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
        if avf_camera_attempt_framerate_selection(storage.camera, framerate):
            if self._update_ev is not None:
                self._update_ev.cancel()
            self._framerate = framerate
            self._update_ev = Clock.schedule_interval(self._update, self._scheduled_rate)

    def set_preset(self, preset):
        cdef _AVStorage storage = <_AVStorage>self._storage
        avf_camera_attempt_capture_preset(storage.camera, preset)

    def set_video_orientation(self, orientation):
        cdef _AVStorage storage = <_AVStorage>self._storage
        avf_camera_set_video_orientation(storage.camera, orientation)

    def start_metadata_analysis(self, callback=None):
        cdef _AVStorage storage = <_AVStorage>self._storage
        self._metadata_callback = callback
        avf_camera_attempt_start_metadata_analysis(storage.camera)
        
    def get_device_orientation(self):
        # iOS only
        return avf_camera_get_device_orientation()

    def change_camera_input(self, index):
        # iOS only
        cdef _AVStorage storage = <_AVStorage>self._storage
        avf_camera_change_input(storage.camera, index)

    def zoom_level(self, level):
        # iOS only
        cdef _AVStorage storage = <_AVStorage>self._storage
        avf_camera_zoom_level(storage.camera, level)

    def get_app_documents_directory(self):
        # iOS only
        return str(avf_camera_documents_directory().decode('utf-8'))

    def save_texture(self, texture, filepath = '', quality = 0.9):
        # iOS only
        # With texture argument only: Save texture to iOS Photos App
        # With texture and filepath arguments: Save texture as jpg; filepath root must be app documents directory,
        #     sub-directories in filepath must exist, filepath last element is filename.jpg
        cdef _AVStorage storage = <_AVStorage>self._storage
        avf_camera_save_pixels(storage.camera, bytearray(texture.pixels), int(texture.width), int(texture.height),
                               filepath.encode('utf-8'), quality)
