'''
FFPyPlayer: FFmpeg based image loader
'''

__all__ = ('ImageLoaderFFPy', )

import ffpyplayer
from ffpyplayer.pic import ImageLoader as ffImageLoader, SWScale
from ffpyplayer.tools import set_log_callback, get_log_callback

from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader


Logger.info('ImageLoaderFFPy: Using ffpyplayer {}'.format(ffpyplayer.version))


logger_func = {'quiet': Logger.critical, 'panic': Logger.critical,
               'fatal': Logger.critical, 'error': Logger.error,
               'warning': Logger.warning, 'info': Logger.info,
               'verbose': Logger.debug, 'debug': Logger.debug}


def _log_callback(message, level):
    message = message.strip()
    if message:
        logger_func[level]('ffpyplayer: {}'.format(message))

if not get_log_callback():
    set_log_callback(_log_callback)


class ImageLoaderFFPy(ImageLoaderBase):
    '''Image loader based on the ffpyplayer library.

    .. versionadded:: 1.9.0

    .. note:
        This provider may support more formats than what is listed in
        :meth:`extensions`.
    '''

    @staticmethod
    def extensions():
        '''Return accepted extensions for this loader'''
        # See https://www.ffmpeg.org/general.html#Image-Formats
        return ('bmp', 'dpx', 'exr', 'gif', 'ico', 'jpeg', 'jpg2000', 'jpg',
                'jls', 'pam', 'pbm', 'pcx', 'pgm', 'pgmyuv', 'pic', 'png',
                'ppm', 'ptx', 'sgi', 'ras', 'tga', 'tiff', 'webp', 'xbm',
                'xface', 'xwd')

    def load(self, filename):
        try:
            loader = ffImageLoader(filename)
        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise

        # update internals
        self.filename = filename
        images = []

        while True:
            frame, t = loader.next_frame()
            if frame is None:
                break
            images.append(frame)
        if not len(images):
            raise Exception('No image found in {}'.format(filename))

        w, h = images[0].get_size()
        ifmt = images[0].get_pixel_format()
        if ifmt != 'rgba' and ifmt != 'rgb24':
            fmt = 'rgba'
            sws = SWScale(w, h, ifmt, ofmt=fmt)
            for i, image in enumerate(images):
                images[i] = sws.scale(image)
        else:
            fmt = ifmt if ifmt == 'rgba' else 'rgb'

        return [ImageData(w, h, fmt, img.to_memoryview()[0], source_image=img)
                for img in images]


# register
ImageLoader.register(ImageLoaderFFPy)
