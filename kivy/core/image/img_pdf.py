'''
PDF: PDF image loader
'''

from kivy.cache import Cache
from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader

from kivy.graphics.texture import Texture
Debug = False

import io
from pyPdf import PdfFileWriter, PdfFileReader
import PythonMagick as pm
import pygame


class ImageLoaderPDF(ImageLoaderBase):
    '''Image loader for PDF'''

    def __init__(self, filename, page=0, **kwargs):
        self.page = page
        super(ImageLoaderPDF, self).__init__(filename, **kwargs)

    @staticmethod
    def extensions():
        '''Return accepted extension for this loader'''
        return ('pdf', )

    def load(self, filename):
        try:
            print "load pdf!", self.page

            # first extract the page from the pdf
            with open(filename, 'rb') as fd:
                pdf = PdfFileReader(fd)
                page = pdf.getPage(self.page)

                pfw = PdfFileWriter()
                pfw.addPage(page)
                f = io.BytesIO()
                pfw.write(f)
                f.seek(0)

            # then convert the one page pdf filebuffer to an image
            blob = pm.Blob(f.read())
            blobresult = pm.Blob()

            # export as a png. raw rgb/rgba might output interlaced/depth that
            # we don't want. current PythonMagick bindings don't allow to change
            # it. so rely as a png.
            pmi = pm.Image(blob)
            pmi.write(blobresult, 'png')

            # load the png though pygame
            fd = io.BytesIO()
            fd.write(blobresult.data)
            fd.seek(0)
            im = pygame.image.load(fd, 'bleh.png')
            assert(im.get_bytesize() == 3)

            # update internals
            self.filename = filename
            data = pygame.image.tostring(im, 'RGB', True)

            # result a list of one image available
            return [ImageData(im.get_width(), im.get_height(), 'rgb', data)]

        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise

    def populate(self):
        self._textures = []
        if __debug__:
            Logger.trace('Image: %r, populate to textures (%d)' %
                    (self.filename, len(self._data)))

        # first, check if a texture with the same name already exist in the
        # cache
        uid = '%s|%s|%s' % (
                self.filename,
                self._mipmap,
                hasattr(self, 'page') and self.page or 0)

        texture = Cache.get('kv.texture', uid)

        # if not create it and append to the cache
        if texture is None:
            texture = Texture.create_from_data(
                    self._data[0], mipmap=self._mipmap)
            Cache.append('kv.texture', uid, texture)

        # set as our current texture
        self._textures.append(texture)

        # release data if ask
        if not self.keep_data:
            self._data[0].release_data()

ImageLoader.register(ImageLoaderPDF)
