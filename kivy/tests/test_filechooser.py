import logging
from os import environ
from os.path import expanduser, exists
from sys import version_info
import unittest

from kivy.tests.common import GraphicUnitTest
from kivy.uix.filechooser import FileChooserListView, FileChooserIconView


class FileChooserTestCase(GraphicUnitTest):
    def test_filechooserlistview(self):
        r = self.render
        widget = FileChooserListView(path=expanduser("~"))
        r(widget, 2)

    def test_filechoosericonview(self):
        r = self.render
        widget = FileChooserIconView(path=expanduser("~"), show_hidden=True)
        r(widget, 2)

    @unittest.skipIf(
        ("SystemDrive" not in environ) or
        (not exists(environ["SystemDrive"] + "\\pagefile.sys")),
        "Only runs on Windows with example system file present",
    )
    @unittest.skipIf(
        version_info < (3, 10), "assertNoLogs requires in Python 3.10"
    )
    def test_filechooser_files_in_use_5873(self):
        # Per Kivy Issue #5873, initially viewing C:\ on Windows would
        # crash.
        # Later versions, it merely logged warnings.
        # The cause was hidden system files which could not be interrogated to
        # find out if they were hidden, because they were in use by the system.

        # This variant always worked, because there was no call to is_hidden.
        with self.assertNoLogs(logging.getLogger("kivy"), logging.WARNING):
            widget = FileChooserListView(
                path=environ["SystemDrive"] + "/", show_hidden=True
            )
            self.render(widget, 1)

        # This used to fail, because the call to is_hidden logged errors.
        with self.assertNoLogs(logging.getLogger("kivy"), logging.WARNING):
            widget = FileChooserListView(path=environ["SystemDrive"] + "/")
            self.render(widget, 1)
