import unittest


class ClipboardTestCase(unittest.TestCase):

    def setUp(self):
        from kivy.core.clipboard import Clipboard
        self._clippy = Clipboard
        clippy_types = Clipboard.get_types()
        cliptype = clippy_types[0]
        if 'UTF8_STRING' in clippy_types:
            cliptype = 'UTF8_STRING'
        self._cliptype = cliptype

    def test_clipboard_not_dummy(self):
        clippy = self._clippy
        if clippy.__class__.__name__ == 'ClipboardDummy':
            self.fail('Something went wrong "dummy" clipboard is being used')

    def test_clipboard_paste(self):
        clippy = self._clippy
        try:
            clippy.paste()
        except:
            self.fail(
                'Can not get data from clipboard')

    def test_clipboard_copy(self):
        clippy = self._clippy
        try:
            clippy.copy(u"Hello World")
        except:
            self.fail(
                'Can not get put data to clipboard')
