from kivy.core.text import LabelBase
from kivy.core.image import ImageData

try:
    from Quartz import *
    from Cocoa import *
    from kivy.utils import create_quartz_context, get_context_bitmap_data
except:
    raise


class LabelPyObjCQuartz(LabelBase):
    def __init__(self, **kwargs):
        super(LabelPyObjCQuartz, self).__init__(**kwargs)
        self.ctx = None
        self.font = None

    def get_extents(self, txt):
        size = self.options['font_size'] * 1.333
        s = NSString.stringWithUTF8String_(str(txt))
        font_name = NSString.stringWithUTF8String_("Helvetica")
        font = NSFont.fontWithName_size_(font_name, size)
        attrs = {NSFontAttributeName: font}
        exts = NSAttributedString.alloc().initWithString_attributes_(s, attrs).size()
        return (exts.width, exts.height)

    def _render_begin(self):
        w, h = self._size
        self.ctx = create_quartz_context(w, h)

    def _render_text(self, text, x, y):
        #CGContextSelectFont(self.ctx, self.options['font_name'], self.options['font_size'],
        CGContextSelectFont(self.ctx, 'Helvetica', self.options['font_size'] * 1.333,
            kCGEncodingMacRoman)
        CGContextSetTextDrawingMode(self.ctx, kCGTextFill)

        CGContextSetRGBFillColor(self.ctx, 1, 1, 1, 1)
        # Account for glyphs that go below the baseline
        CGContextShowTextAtPoint(self.ctx, x, y+2.5, str(text), len(text))

    def _render_end(self):
        ret = get_context_bitmap_data(self.ctx)
        return ImageData(*ret)

