# -*- coding: utf-8 -*-
# XXX: please be careful to only save this file with an utf-8 editor

from os import remove, rmdir, mkdir
from os.path import join, dirname, isdir
import unittest
from zipfile import ZipFile

import pytest

from kivy.clock import Clock
from kivy.uix.filechooser import FileChooserListView
from kivy.utils import platform

unicode_char = chr


class FileChooserUnicodeTestCase(unittest.TestCase):
    def setUp(self):
        basepath = dirname(__file__)
        subdir = join(basepath, "filechooser_files")
        self.subdir = subdir

        ufiles = [
            "कीवीtestu",
            "कीवीtestu" + unicode_char(0xEEEE),
            "कीवीtestu" + unicode_char(0xEEEE - 1),
            "कीवीtestu" + unicode_char(0xEE),
        ]
        self.files = [join(subdir, f) for f in ufiles]
        if not isdir(subdir):
            mkdir(subdir)
        for f in self.files:
            open(f, "wb").close()

        # existing files
        existfiles = [
            "à¤•à¥€à¤µà¥€test",
            "à¤•à¥€à¤’µà¥€test",
            "Ã Â¤â€¢Ã Â¥â‚¬Ã Â¤ÂµÃ Â¥â‚¬test",
            "testl\ufffe",
            "testl\uffff",
        ]
        self.existfiles = [join(subdir, f) for f in existfiles]
        with ZipFile(join(basepath, "unicode_files.zip"), "r") as myzip:
            myzip.extractall(path=subdir)
        for f in self.existfiles:
            open(f, "rb").close()

    @pytest.fixture(autouse=True)
    def set_clock(self, kivy_clock):
        self.kivy_clock = kivy_clock

    @pytest.mark.skipif(
        platform == "macosx" or platform == "ios",
        reason="Unicode files unpredictable on MacOS and iOS",
    )
    # On macOS and iOS, files ending in \uffff etc. are changed.
    # We cannot predict the filenames that will be created.
    # If it works on Window and Linux, we can safely assume it also works
    # on macOS and iOS.
    def test_filechooserlistview_unicode(self):

        wid = FileChooserListView(path=self.subdir)
        Clock.tick()
        files = [join(self.subdir, f) for f in wid.files]
        for f in self.files:
            self.assertIn(f, files)

        for f in self.existfiles:
            self.assertIn(f, files)

    def tearDown(self):
        for f in self.files + self.existfiles:
            try:
                remove(f)
            except (OSError, FileNotFoundError):
                pass
        try:
            rmdir(self.subdir)
        except (OSError, FileNotFoundError):
            pass
