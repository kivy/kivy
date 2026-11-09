import unittest
import io
from base64 import b64encode
from urllib.parse import quote_from_bytes
import os
import tempfile
from kivy import setupconfig


class DataURITestCase(unittest.TestCase):

    @staticmethod
    def _png_bytes():
        import kivy
        png_path = os.path.join(kivy.kivy_data_dir, 'logo', 'kivy-icon-16.png')
        with open(png_path, 'rb') as f:
            return f.read()

    def test_data_uri_base64(self):
        from kivy.core.image import Image as CoreImage
        png = self._png_bytes()
        img = CoreImage("data:image/png;base64," + b64encode(png).decode("ascii"))
        self.assertEqual(tuple(img.size), (16, 16))

    def test_data_uri_percent_encoded(self):
        from kivy.core.image import Image as CoreImage
        png = self._png_bytes()
        img = CoreImage("data:image/png," + quote_from_bytes(png))
        self.assertEqual(tuple(img.size), (16, 16))


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

    @unittest.skip("Travis on Xenial don't have SDL_image >= 2.0.5")
    def test_save_into_bytesio(self):
        Image = self.cls

        if setupconfig.PLATFORM == "darwin":
            # XXX on OSX CI Builder, img_sdl3 is not used
            # therefore the test below wont work yet with imageio only.
            return

        # load kivy logo
        img = Image.load("data/logo/kivy-icon-512.png")
        self.assertIsNotNone(img)

        # try to save without any format
        with self.assertRaises(Exception) as context:
            bio = io.BytesIO()
            img.save(bio)

        # save it in png
        bio = io.BytesIO()
        # if False, then there is no provider
        self.assertTrue(img.save(bio, fmt="png"))
        pngdata = bio.read()
        self.assertTrue(len(pngdata) > 0)

        # try to save in a filename
        try:
            _, filename = tempfile.mkstemp(suffix=".png")
            self.assertTrue(img.save(filename, fmt="png"))
        finally:
            os.unlink(filename)

        # XXX Test wrote but temporary commented
        # XXX because of the issue #6123 on OSX
        # XXX https://github.com/kivy/kivy/issues/6123
        # with open(filename, "rb") as fd2:
        #     pngdatafile = fd2.read()
        # # check the png file data is the same as bytesio
        # self.assertTrue(pngdata == pngdatafile)

        # save it in jpeg
        bio = io.BytesIO()
        # if False, then there is no provider
        self.assertTrue(img.save(bio, fmt="jpg"))
        self.assertTrue(len(bio.read()) > 0)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as fd:
            self.assertTrue(img.save(fd.name))


class PILAnimatedGifTestCase(unittest.TestCase):

    RED = (255, 0, 0, 255)
    GREEN = (0, 255, 0, 255)
    BLUE = (0, 0, 255, 255)
    CLEAR = (0, 0, 0, 0)

    def _load_gif(self, frames, **save_kwargs):
        from kivy.core.image.img_pil import ImageLoaderPIL

        bio = io.BytesIO()
        frames[0].save(
            bio, format='gif', save_all=True, append_images=frames[1:],
            duration=100, loop=0, **save_kwargs)
        bio.seek(0)
        return ImageLoaderPIL('frames.gif', inline=True, rawdata=bio)._data

    @staticmethod
    def _pixel(frame, x, y):
        bpp = len(frame.fmt)
        offset = (y * frame.width + x) * bpp
        pixel = tuple(frame.data[offset:offset + bpp])
        return pixel if bpp == 4 else pixel + (255, )

    def _frame(self, color, clear_at=None):
        from PIL import Image as PILImage

        frame = PILImage.new('RGBA', (4, 4), color)
        if clear_at is not None:
            frame.putpixel(clear_at, self.CLEAR)
        return frame

    def test_gif_frames_without_transparency(self):
        from PIL import Image as PILImage

        colors = [self.RED, self.GREEN, self.BLUE]
        frames = [PILImage.new('RGB', (4, 4), c[:3]) for c in colors]
        data = self._load_gif(frames)

        self.assertEqual(len(data), len(colors))
        for frame, color in zip(data, colors):
            self.assertEqual(self._pixel(frame, 0, 0), color)

    def test_gif_partial_frames(self):
        from PIL import Image as PILImage

        base = PILImage.new('RGB', (4, 4), self.RED[:3])
        changed = base.copy()
        changed.putpixel((0, 0), self.GREEN[:3])
        data = self._load_gif([base, changed, base])

        self.assertEqual(len(data), 3)
        self.assertEqual(self._pixel(data[1], 0, 0), self.GREEN)
        self.assertEqual(self._pixel(data[1], 1, 0), self.RED)
        self.assertEqual(self._pixel(data[2], 0, 0), self.RED)

    def test_gif_transparency_keeps_previous_frame(self):
        frames = [self._frame(self.RED, clear_at=(1, 0)),
                  self._frame(self.BLUE, clear_at=(0, 0))]
        data = self._load_gif(frames, disposal=1)

        self.assertEqual(self._pixel(data[0], 0, 0), self.RED)
        self.assertEqual(self._pixel(data[0], 1, 0), self.CLEAR)
        self.assertEqual(self._pixel(data[1], 0, 0), self.RED)
        self.assertEqual(self._pixel(data[1], 1, 0), self.BLUE)

    def test_gif_transparency_restores_background(self):
        frames = [self._frame(self.RED, clear_at=(1, 0)),
                  self._frame(self.BLUE, clear_at=(0, 0))]
        data = self._load_gif(frames, disposal=2)

        self.assertEqual(self._pixel(data[1], 0, 0), self.CLEAR)
        self.assertEqual(self._pixel(data[1], 1, 0), self.BLUE)
