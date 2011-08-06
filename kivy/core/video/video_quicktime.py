from kivy.core.video import VideoBase
from kivy.graphics.texture import Texture


try:
    import QTKit
except:
    raise


class QTMovieWrapper(object):
    '''
    Apparently QTKit does frame grabbing and audio playback in the same thread,
    as I get severe stuttering if I play a QTMovie and then periodically access
    its frames. There also seems to be no way to split that into two threads.
    Behind the scenes, however, at least one extra thread is created per QTMovie
    object. That's why this workaround simply creates two QTMovie objects: one
    for frame grabbing, the other for audio playback. It's not ideal, but it
    works.
    '''
    def __init__(self, filename, async):
        self.filename = filename
        self.async = async
        self._video = self._open_movie()
        self._audio = self._open_movie()

    def seek(self, percent):
        d = self._video.duration()
        d = (d[0] * percent, d[1], d[2])
        self._audio.setCurrentTime_(d)

    def _open_movie(self):
        attrs = {
            'QTMovieFileNameAttribute': unicode(self.filename),
            'QTMovieOpenAsyncOKAttribute': self.async,
            'QTMovieApertureModeAttribute': QTKit.QTMovieApertureModeClean,
            'QTMovieIsActiveAttribute': True,
            }

        movie, error = QTKit.QTMovie.alloc().initWithAttributes_error_(attrs, None)
        if movie is None:
            print error
            raise RuntimeError('Could not load video: %s' % self.filename)
        return movie

    def stop(self):
        self._audio.stop()

    def play(self):
        self._audio.play()

    def current_frame(self):
        time = self._audio.currentTime()
        img = self._video.frameImageAtTime_(time)
        return img


class VideoQuickTime(VideoBase):
    def __init__(self, **kwargs):
        self._video = None
        self._colorfmt = 'rgba'
        super(VideoQuickTime, self).__init__(**kwargs)

    def _update(self, dt):
        '''Update the video content to texture.
        '''
        img = self._video.current_frame()
        size = img.size()

        if self._texture is None:
            self._texture = Texture.create(
                size=size, colorfmt=self._colorfmt)
            self._texture.flip_vertical()
            self.dispatch('on_load')

        bmp = img.representations()[0]
        data = bmp.bitmapData().tobytes()
        self._texture.blit_buffer(
            data, size=size,
            colorfmt=self._colorfmt)
        self.dispatch('on_frame')

    def seek(self, percent):
        self._video.seek(percent)

    def stop(self):
        self._state = ''
        self._video.stop()

    def play(self):
        self._state = 'playing'
        self._video.play()

    def load(self):
        self._video = QTMovieWrapper(self.filename, self._async)

    def unload(self):
        self._state = ''
        self._video = None
