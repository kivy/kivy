'''
Camera
======

This widget can be used to capture and display the camera on the screen.
Once the widget is created, the texture inside the widget will be automatically
updated. ::

    cam = Camera()

The actual implementation use our :class:`~kivy.core.camera.CameraBase`
implementation. The camera used is the first one found on your system. If you
want to test another camera, you can select another index. ::

    cam = Camera(index=1)

You can also select the camera resolution. ::

    cam = Camera(resolution=(320, 240))

.. warning::

    The camera texture is not updated as soon as you have created the object.
    The camera initialization is asynchronous, it may take a little bit before
    the texture is created.

'''

__all__ = ('Camera', )

from kivy.uix.image import Image
from kivy.core.camera import Camera as CoreCamera
from kivy.properties import NumericProperty, ObjectProperty, \
        ListProperty


class Camera(Image):
    '''Camera class. See module documentation for more informations.
    '''

    index = NumericProperty(-1)
    '''Index of the used camera, starting from 0.

    :data:`index` is a :class:`~kivy.properties.NumericProperty`, default to -1
    to allow auto selection.
    '''

    resolution = ListProperty([-1, -1])
    '''Prefered resolution to use when invoking the camera. If you are using
    [-1, -1], the resolution will be the default one. ::

        # create a camera object with the best image available
        cam = Camera()

        # create a camera object with an image of 320x240 if possible
        cam = Camera(resolution=(320, 240))

    .. warning::

        Depending of the implementation, the camera may not respect this
        property.

    :data:`resolution` is a :class:`~kivy.properties.ListProperty`, default to
    [-1, -1]
    '''

    texture = ObjectProperty(None, allownone=True)
    '''Texture object of the camera.

    Depending of the texture creation, the value will be a
    :class:`~kivy.graphics.texture.Texture` or
    :class:`~kivy.graphics.texture.TextureRegion` object.

    :data:`texture` is a :class:`~kivy.properties.ObjectProperty`, default to
    None.
    '''

    texture_size = ListProperty([0, 0])
    '''Texture size of the camera.

    :data:`texture_size` is a :class:`~kivy.properties.ListProperty`, default to
    [0, 0]
    '''

    def __init__(self, **kwargs):
        self._camera = None
        super(Camera, self).__init__(**kwargs)
        if self.index == -1:
            self.index = 0
        self.bind(index=self._on_index,
                  resolution=self._on_index)
        self._on_index()

    def _on_index(self, *largs):
        self._camera = None
        if self.index < 0:
            return
        self._camera = CoreCamera(index=self.index, resolution=self.resolution)
        self._camera.bind(on_load=self._camera_loaded)

    def _camera_loaded(self, *largs):
        self.texture = self._camera.texture
        self.texture_size = list(self.texture.size)

    def start(self):
        '''Start to acquire the camera.

        .. note::

            The camera is loaded at __init__. You don't need to use it, except
            if you have currently stopped the camera with :func:`Camera.stop`.
        '''
        self._camera.start()

    def stop(self):
        '''Stop the camera
        '''
        self._camera.stop()


