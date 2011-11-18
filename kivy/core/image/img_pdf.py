'''
PDF: PDF image loader
'''

from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageLoader

Debug = False

import io
from pyPdf import PdfFileWriter, PdfFileReader

class ImageLoaderPDF(ImageLoaderBase):
    '''Image loader for PDF'''

    def __init__(self, page=0, filename=None, **kwargs):
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
            w = PdfFileWriter()
            w.addPage(p2)
            f = io.BytesIO()
            w.write(f)
            f.seek(0)

            # then convert the one page pdf filebuffer to an image
            blob = pm.Blob(f.read())
            blobpng = pm.Blob()
            pm.Image(blob).write(blobpng,'jpg')
            #blobpng.data

            im = PILImage.frombuffer('rgb', len(blobpng.data), blobpng.data)

        except:
            Logger.warning('Image: Unable to load image <%s>' % filename)
            raise

        return list(self._img_read(im))

ImageLoader.register(ImageLoaderPDF)
print "PDF loader registered!"
