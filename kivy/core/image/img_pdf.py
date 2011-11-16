#-*- coding: utf-8 -*-
#
#    this program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    this program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#   The Graphics Interchange Format(c) is the Copyright property of
#   CompuServe Incorporated. GIF(sm) is a Service Mark property of
#   CompuServe Incorporated.
#
# The unisys/lzw patent has expired, yes. If anyone puts another patent
# over this code, you must *burn* this file.


#TODO issues to fix
#optimize for speed  #partially done#  a lot of room for improvementd
import struct
from array import array
import math

from kivy.logger import Logger
from . import ImageLoaderBase, ImageData, ImageLoader

Debug = False

import io
from pyPdf import PdfFileWriter, PdfFileReader

class ImageLoaderPDF(ImageLoaderBase):
    '''Image loader for PDF'''

    def __init__(self, page=0, **kwargs):
        self.page = page
        super(ImageLoaderPDF, self).__init__(**kwargs)

    @staticmethod
    def extensions():
        '''Return accepted extension for this loader'''
        return ('pdf', )

    def load(self, filename):
        try:
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
