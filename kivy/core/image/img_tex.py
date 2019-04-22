'''
Tex: Compressed texture
'''

__all__ = ('ImageLoaderTex', )

import json
from struct import unpack
from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader


class ImageLoaderTex(ImageLoaderBase):

    @staticmethod
    def extensions():
        return ('tex', )

    def load(self, filename):
        try:
            fd = open(filename, 'rb')
            if fd.read(4) != 'KTEX':
                raise Exception('Invalid tex identifier')

            headersize = unpack('I', fd.read(4))[0]
            header = fd.read(headersize)
            if len(header) != headersize:
                raise Exception('Truncated tex header')

            info = json.loads(header)
            data = fd.read()
            if len(data) != info['datalen']:
                raise Exception('Truncated tex data')

        except:
            Logger.warning('Image: Image <%s> is corrupted' % filename)
            raise

        width, height = info['image_size']
        tw, th = info['texture_size']

        images = [data]
        im = ImageData(width, height, str(info['format']), images[0],
                       source=filename)
        '''
        if len(dds.images) > 1:
            images = dds.images
            images_size = dds.images_size
            for index in range(1, len(dds.images)):
                w, h = images_size[index]
                data = images[index]
                im.add_mipmap(index, w, h, data)
        '''
        return [im]


# register
ImageLoader.register(ImageLoaderTex)
