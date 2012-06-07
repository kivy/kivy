import unittest


class ImageTestCase(unittest.TestCase):

    def setUp(self):
        from kivy.core.image import Image
        self.cls = Image
        self.root = Image('test_button.png')

    def test_keep_data(self):
        root = self.root
        self.assertEqual(root._image._data[0].data, None)
        i1 = self.cls('test_button.png', keep_data = True)
        if not i1._image._data[0].data:
            self.fail('Image has no data even with keep_data = True')
