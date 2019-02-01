import unittest
import io
import tempfile


class ImageTestCase(unittest.TestCase):

    def setUp(self):
        from kivy.core.window import Window
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

    def test_save_into_bytesio(self):
        Image = self.cls

        # load kivy logo
        img = Image.load("data/logo/kivy-icon-512.png")
        self.assertIsNotNone(img)

        # try to save with missing format
        try:
            bio = io.BytesIO()
            self.assertTrue(img.save(bio))  # if False, then there is no provider
            self.fail('Image.save() with bytesio')
        except Exception:
            pass

        # save it in png
        bio = io.BytesIO()
        self.assertTrue(img.save(bio, fmt="png"))  # if False, then there is no provider
        self.assertTrue(len(bio.read()) > 0)

        # save it in jpeg
        bio = io.BytesIO()
        self.assertTrue(img.save(bio, fmt="jpg"))  # if False, then there is no provider
        self.assertTrue(len(bio.read()) > 0)

        # try to save in a filename
        with tempfile.NamedTemporaryFile(suffix=".png") as fd:
            self.assertTrue(img.save(fd.name))

        with tempfile.NamedTemporaryFile(suffix=".jpg") as fd:
            self.assertTrue(img.save(fd.name))