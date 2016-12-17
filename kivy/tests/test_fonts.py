# -*- coding: utf-8 -*-
import unittest


class FontTestCase(unittest.TestCase):

    def setUp(self):
        import os
        import tempfile
        from os.path import join, dirname, exists

        fdir = dirname(__file__)
        self.temp_dir = join(tempfile.gettempdir(), 'kivy_test_fonts')

        if not exists(self.temp_dir):
            os.mkdir(self.temp_dir)

        self.font_name = join(self.temp_dir, u'कीवी.ttf')
        if not exists(self.font_name):
            from zipfile import ZipFile
            with ZipFile(join(fdir, 'unicode_font.zip'), 'r') as myzip:
                myzip.extractall(path=self.temp_dir)

        print(self.font_name)

    def test_unicode_name(self):
        from kivy.core.text import Label
        lbl = Label(font_name=self.font_name)
        lbl.refresh()
        self.assertNotEqual(lbl.get_extents(''), None)

    def tearDown(self):
        import shutil
        from os.path import exists

        if exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
