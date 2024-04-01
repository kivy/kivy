# distutils: language = c++
'''
AVFoundation Camera
===================

Camera implementation using AVFoundation framework for OSX / iOS
'''

__all__ = ['CameraAVFoundation']


cdef extern from "camera_avfoundation_implem.mm":
    cppclass CameraMetadata:
        char *type
        char *data

    cppclass CameraFrame:
        char * data
        unsigned int datasize
        unsigned int rowsize
        int width
        int height

    cppclass Camera:
        Camera(int cameraNum, int width, int height)
        @staticmethod
        int getDeviceOrientation()
        @staticmethod
        char* getDocumentsDirectory()
        bint grabFrame(double timeOut)
        int startCaptureDevice()
        void stopCaptureDevice()
        CameraFrame* retrieveFrame()
        bint attemptFrameRateSelection(int desiredFrameRate)
        bint attemptCapturePreset(char* preset)
        void setVideoOrientation(int orientation)
        void changeCameraInput(int _cameraNum)
        void zoomLevel(float zoomLevel)
        bint attemptStartMetadataAnalysis()
        bint haveNewMetadata()
        CameraMetadata* retrieveMetadata()
        void savePixelsToFile(unsigned char *pixels, int width, int height, char *path, float quality)


from kivy.logger import Logger
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.camera import CameraBase
from kivy.utils import platform
from cython cimport view as cyview


cdef class _AVStorage:
    cdef Camera* camera

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
        storage.camera = new Camera(
            self._index, self.resolution[0], self.resolution[1]
        )

    def _release_camera(self):
        cdef _AVStorage storage = <_AVStorage>self._storage
        if storage.camera != NULL:
            del storage.camera
            storage.camera = NULL

    @property
    def _scheduled_rate(self):
        # We're going 4 times faster the framerate to avoid frame skipping.
        return 1 / (self._framerate * 4)

    def _update(self, dt):
        cdef _AVStorage storage = <_AVStorage>self._storage
        cdef int width, height, rowsize
        cdef char *data
        cdef CameraFrame* _current_frame
        cdef CameraMetadata* _current_metadata
        cdef cyview.array cyarr

        if self.stopped:
            return

        if not storage.camera.grabFrame(0):
            return

        _current_frame = storage.camera.retrieveFrame()

        if  _current_frame == NULL:
            return

        width = _current_frame.width
        height = _current_frame.height
        rowsize = _current_frame.rowsize
        data = _current_frame.data

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
            if storage.camera.haveNewMetadata():
                _current_metadata = storage.camera.retrieveMetadata()
                self._metadata_callback(_current_metadata.type, _current_metadata.data)
    
    def _copy_to_gpu(self):
        self.dispatch('on_texture')

    def start(self):
        cdef _AVStorage storage = <_AVStorage>self._storage
        super(CameraAVFoundation, self).start()
        if self._update_ev is not None:
            self._update_ev.cancel()
        self._update_ev = Clock.schedule_interval(self._update, self._scheduled_rate)
        storage.camera.startCaptureDevice()

    def stop(self):
        cdef _AVStorage storage = <_AVStorage>self._storage
        super(CameraAVFoundation, self).stop()
        if self._update_ev is not None:
            self._update_ev.cancel()
            self._update_ev = None
        storage.camera.stopCaptureDevice()

    def set_framerate(self, framerate):
        cdef _AVStorage storage = <_AVStorage>self._storage
        if storage.camera.attemptFrameRateSelection(framerate):
            if self._update_ev is not None:
                self._update_ev.cancel()
            self._framerate = framerate
            self._update_ev = Clock.schedule_interval(self._update, self._scheduled_rate)

    def set_preset(self, preset):
        cdef _AVStorage storage = <_AVStorage>self._storage
        storage.camera.attemptCapturePreset(preset)

    def set_video_orientation(self, orientation):
        cdef _AVStorage storage = <_AVStorage>self._storage
        storage.camera.setVideoOrientation(orientation)

    def start_metadata_analysis(self, callback=None):
        cdef _AVStorage storage = <_AVStorage>self._storage
        self._metadata_callback = callback
        storage.camera.attemptStartMetadataAnalysis()
        
    def get_device_orientation(self):
        # iOS only, on macOS this method does nothing
        return Camera.getDeviceOrientation()

    def change_camera_input(self, index):
        # iOS only, on macOS this method does nothing
        cdef _AVStorage storage = <_AVStorage>self._storage
        storage.camera.changeCameraInput(index)

    def zoom_level(self, level):
        # iOS only, on macOS this method does nothing
        cdef _AVStorage storage = <_AVStorage>self._storage
        storage.camera.zoomLevel(level)

    def get_app_documents_directory(self):
        # iOS only, on macOS returns an empty string
        return str(Camera.getDocumentsDirectory().decode('utf-8'))

    def save_texture(self, texture, filepath = '', quality = 0.9):
        # iOS only
        # With texture argument only: Save texture to iOS Photos App
        # With texture and filepath arguments: Save texture as jpg; filepath root must be app documents directory,
        #     sub-directories in filepath must exist, filepath last element is filename.jpg
        cdef _AVStorage storage = <_AVStorage>self._storage
        storage.camera.savePixelsToFile(bytearray(texture.pixels), int(texture.width), int(texture.height),
                                        filepath.encode('utf-8'), quality)