#-*- coding: utf-8 -*-
import unittest


class FontTestCase(unittest.TestCase):

    def setUp(self):
        import os
        self.font_name = os.path.join(os.path.dirname(__file__), u'कीवी.ttf')
        if not os.path.exists(self.font_name):
            from zipfile import ZipFile
            with ZipFile(os.path.join(os.path.dirname(__file__),
                                      'unicode_font.zip'), 'r') as myzip:
                myzip.extractall(path=os.path.dirname(__file__))
        print(self.font_name)

    def test_unicode_name(self):
        from kivy.core.text import Label
        lbl = Label(font_name=self.font_name)
        lbl.refresh()
        self.assertNotEqual(lbl.get_extents(''), None)

    def tearDown(self):
        import os
        if os.path.exists(self.font_name):
            try:
                os.unlink(self.font_name)
            except:
                pass

