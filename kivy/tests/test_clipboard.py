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

    def test_clipboard_get(self):
        clippy = self._clippy
        try:
            clippy.get(self._cliptype)
        except:
            self.fail(
                'Can not get data from clipboard of type {}'.format(cliptype))

    def test_clipboard_put(self):
        clippy = self._clippy
        try:
            clippy.put(u"Hello World", self._cliptype)
        except:
            self.fail(
                'Can not get put data to clipboard of type {}'.format(cliptype))
