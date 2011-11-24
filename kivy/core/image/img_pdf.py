'''
PDF: PDF image loader
'''

try:
    from PIL import Image as PILImage
except:
    raise

from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader

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

ImageLoader.register(ImageLoaderPDF)
