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
from kivy.properties import NumericProperty, ListProperty, \
        BooleanProperty


class Camera(Image):
    '''Camera class. See module documentation for more informations.
    '''

    play = BooleanProperty(False)
    '''Boolean indicate if the camera is playing.
    You can start/stop the camera by setting this property. ::

        # start the camera playing at creation
        video = Camera(source='movie.mkv', play=True)

        # create the camera, and start later
        video = Camera(source='movie.mkv')
        # and later
        video.play = True

    :data:`play` is a :class:`~kivy.properties.BooleanProperty`, default to
    True.
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
        self._camera = CoreCamera(index=self.index,
            resolution=self.resolution, stopped=True)
        self._camera.bind(on_load=self._camera_loaded)
        if self.play:
            self._camera.start()

    def _camera_loaded(self, *largs):
        self.texture = self._camera.texture
        self.texture_size = list(self.texture.size)

    def on_play(self, instance, value):
        if not self._camera:
            return
        if value:
            self._camera.start()
        else:
            self._camera.stop()

