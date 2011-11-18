'''
PDF: PDF image loader
'''

try:
    from PIL import Image as PILImage
except:
    raise

from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageLoader

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
            print "load pdf!"
            # first extract the page from the pdf
            pdf = PdfFileReader(open(filename, 'rb'))
            p2 = pdf.getPage(self.page)
            size = p2.cropBox[2:]
            w = PdfFileWriter()
            w.addPage(p2)
            f = io.BytesIO()
            w.write(f)
            f.seek(0)

            # then convert the one page pdf filebuffer to an image
            blob = pm.Blob(f.read())
            blobjpg = pm.Blob()
            pm.Image(blob).write(blobjpg,'rgb')
            #blobpng.data

            im = PILImage.frombuffer('RGB', size, blobjpg.data)

        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise

        return list(self._img_read(im))

ImageLoader.register(ImageLoaderPDF)
print "PDF loader registered!"
