'''
Camera
======
'''

__all__ = ('Camera', )

from kivy.uix.widget import Widget
from kivy.core.camera import Camera as CoreCamera
from kivy.properties import NumericProperty, ObjectProperty, \
        ListProperty


class Camera(Widget):

    #: Source
    index = NumericProperty(-1)

    #: Texture of the camera
    texture = ObjectProperty(None, allownone=True)

    #: Texture size of the camera
    texture_size = ListProperty([0, 0])

    def __init__(self, **kwargs):
        self._camera = None
        super(Camera, self).__init__(**kwargs)
        if self.index == -1:
            self.index = 0

    def on_index(self, instance, value):
        self._camera = None
        if value < 0:
            return
        self._camera = CoreCamera(index=value)
        self._camera.bind(on_load=self._camera_loaded)

    def _camera_loaded(self, *largs):
        self.texture = self._camera.texture
        self.texture_size = list(self.texture.size)

