'''
Rgb: raw loader that use mmap
'''

__all__ = ('ImageLoaderRgb', )

import os
import json
from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader


class ImageLoaderRgb(ImageLoaderBase):

    @staticmethod
    def extensions():
        return ('rgb', 'rgba', )

    def load(self, filename):
        try:
            info_fn = '{}.json'.format(filename)
            with open(info_fn, 'r') as fd:
                info = json.load(fd)
        except:
            Logger.warning(
                'ImageRgb: Unable to find associated json for {}'.format(
                    filename))
            raise

        width, height = info['image_size']
        fmt = info['format']

        from kivy.graphics.texture import Mmap
        data = Mmap(filename, os.stat(filename).st_size)
        im = ImageData(width, height, str(fmt),
                data, source=filename)

        return [im]

    @staticmethod
    def can_save():
        return True

    @staticmethod
    def save(filename, width, height, fmt, pixels, flipped):
        # write informations
        info = {'image_size': [width, height], 'format': fmt}
        info_fn = '{}.json'.format(filename)
        with open(info_fn, 'wb') as fd:
            json.dump(info, fd)

        # write pixels
        with open(filename, 'wb') as fd:
            fd.write(pixels)

        return True

# register
ImageLoader.register(ImageLoaderRgb)
