'''
PDF: PDF image loader
'''

try:
    from PIL import Image as PILImage
except:
    raise

from kivy.cache import Cache
from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader

from kivy.graphics.texture import Texture, TextureRegion
Debug = False

import io
from pyPdf import PdfFileWriter, PdfFileReader
import PythonMagick as pm

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
            pdf = PdfFileReader(open(filename, 'rb'))
            p = pdf.getPage(self.page)
            size = p.mediaBox[2:]
            print p.trimBox, p.mediaBox, p.cropBox, p.bleedBox, p.artBox

            w = PdfFileWriter()
            w.addPage(p)
            f = io.BytesIO()
            w.write(f)
            f.seek(0)

            # then convert the one page pdf filebuffer to an image
            blob = pm.Blob(f.read())
            blobrgb = pm.Blob()
            pm.Image(blob).write(blobrgb,'rgba')
            #blobpng.data

            im = PILImage.frombuffer(
                    'RGBA',
                    (size[0] * 2, size[1]),
                    blobrgb.data).resize(size)

        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise

        return (ImageData(size[0], size[1], 'rgba', im.tostring()),)

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
