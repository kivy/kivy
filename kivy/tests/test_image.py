import unittest


class ImageTestCase(unittest.TestCase):

    def setUp(self):
        from kivy.core.image import Image
        import os
        self.cls = Image
        self.image = os.path.join(os.path.dirname(__file__), 'test_button.png')
        print(self.image)
        self.root = Image(self.image)

    def test_keep_data(self):
        root = self.root
        texture = root.texture
        self.assertEqual(root._image._data[0].data, None)
        i1 = self.cls(self.image, keep_data=True)
        if not i1._image._data[0].data:
            self.fail('Image has no data even with keep_data = True')
