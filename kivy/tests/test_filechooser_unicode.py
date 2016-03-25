# -*- coding: utf-8 -*-
# XXX: please be careful to only save this file with an utf-8 editor
import unittest
from kivy.compat import PY2
from kivy import platform

if PY2:
    unicode_char = unichr
else:
    unicode_char = chr


class FileChooserUnicodeTestCase(unittest.TestCase):

    def setUp(self):
        self.skip_test = platform == 'macosx' or platform == 'ios'
        # on mac, files ending in \uffff etc. simply are changed so don't
        # do any tests because we cannot predict the real filenames that will
        # be created. If it works on win and linux it also works on mac.
        # note filechooser should still work, it's only the test that fail
        # because we have to create file ourselves.
        if self.skip_test:
            return
        import os
        from os.path import join
        from zipfile import ZipFile
        basepath = os.path.dirname(__file__) + u''
        basepathu = join(basepath, u'filechooser_files')
        self.basepathu = basepathu
        basepathb = os.path.dirname(__file__.encode())
        basepathb = join(basepathb, b'filechooser_files')
        self.assertIsInstance(basepathb, bytes)
        self.basepathb = basepathb

        # this will test creating unicode and bytes filesnames
        ufiles = [u'कीवीtestu',
                  u'कीवीtestu' + unicode_char(0xEEEE),
                  u'कीवीtestu' + unicode_char(0xEEEE - 1),
                  u'कीवीtestu' + unicode_char(0xEE)]
        # don't use non-ascii directly because that will test source file
        # text conversion, not path issues :)
        bfiles = [b'\xc3\xa0\xc2\xa4\xe2\x80\xa2\xc3\xa0\xc2\xa5\xe2\x82\xac\
        \xc3\xa0\xc2\xa4\xc2\xb5\xc3\xa0\xc2\xa5\xe2\x82\xactestb',
        b'oor\xff\xff\xff\xff\xee\xfe\xef\x81\x8D\x99testb']
        self.ufiles = [join(basepathu, f) for f in ufiles]
        self.bfiles = [join(basepathb, f) for f in bfiles] if PY2 else []
        if not os.path.isdir(basepathu):
            os.mkdir(basepathu)
        for f in self.ufiles:
            open(f, 'wb').close()
        for f in self.bfiles:
            open(f, 'wb').close()

        # existing files
        existfiles = [u'à¤•à¥€à¤µà¥€test', u'à¤•à¥€à¤’µà¥€test',
                      u'Ã Â¤â€¢Ã Â¥â‚¬Ã Â¤ÂµÃ Â¥â‚¬test', u'testl\ufffe',
                      u'testl\uffff']
        self.exitsfiles = [join(basepathu, f) for f in existfiles]
        with ZipFile(join(basepath, u'unicode_files.zip'), 'r') as myzip:
            myzip.extractall(path=basepathu)
        for f in self.exitsfiles:
            open(f, 'rb').close()

    def test_filechooserlistview_unicode(self):
        if self.skip_test:
            return
        from kivy.uix.filechooser import FileChooserListView
        from kivy.clock import Clock
        from os.path import join

        wid = FileChooserListView(path=self.basepathu)
        for i in range(1):
            Clock.tick()
        files = [join(self.basepathu, f) for f in wid.files]
        for f in self.ufiles:
            self.assertIn(f, files)
        # we cannot test the bfiles because we'd have to know the system
        # unicode encoding to be able to compare to returned unicode
        for f in self.exitsfiles:
            self.assertIn(f, files)

        if PY2:
            wid = FileChooserListView(path=self.basepathb)
            Clock.tick()
            files = [join(self.basepathb, f) for f in wid.files]
            for f in self.bfiles:
                self.assertIn(f, files)

    def tearDown(self):
        if self.skip_test:
            return
        from os import remove, rmdir
        try:
            for f in self.ufiles:
                remove(f)
            for f in self.exitsfiles:
                remove(f)
            for f in self.bfiles:
                remove(f)
            rmdir(self.basepathu)
        except:
            pass
