from kivy.tests.common import GraphicUnitTest

from kivy.uix.image import AsyncImage
from kivy.config import Config

from zipfile import ZipFile
from os.path import join, dirname, abspath
from os import remove

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve


class AsyncImageTestCase(GraphicUnitTest):
    def setUp(self):
        self.maxfps = Config.getint('graphics', 'maxfps')
        super(AsyncImageTestCase, self).setUp()

    def zip_frames(self, path):
        with ZipFile(path) as zipf:
            return len(zipf.namelist())

    def load_zipimage(self, source, frames):
        # keep running the test until loaded (or timeout)
        maxfps = self.maxfps
        timeout = 30 * maxfps

        # load ZIP with images named: 000.png, 001.png, ...
        image = AsyncImage(
            source=source,
            anim_delay=0.0333333333333333
        )
        image.test_loaded = False
        self.render(image)

        # bind to 'on_load' because there are various
        # steps where the image is (re)loaded, but
        # the event is triggered only at the end
        image.bind(on_load=lambda *_, **__: setattr(
            image, 'test_loaded', True
        ))

        while timeout and not image.test_loaded:
            self.advance_frames(1)
            timeout -= 1

        proxyimg = image._coreimage
        self.assertTrue(proxyimg.anim_available)
        self.assertEqual(len(proxyimg.image.textures), frames)
        return image

    def test_remote_zipsequence(self):
        # cube ZIP has 63 PNGs used for animation
        ZIP = (
            'https://github.com/kivy/kivy/'
            'raw/master/examples/widgets/'
            'sequenced_images/data/images/cube.zip'
        )

        # ref Loader._load_urllib
        tempf, headers = urlretrieve(ZIP)
        ZIP_pngs = self.zip_frames(tempf)
        remove(tempf)

        image = self.load_zipimage(ZIP, ZIP_pngs)
        # pure delay * fps isn't enough and
        # just +1 isn't either (index collisions)
        self.assertTrue(self.check_sequence_frames(
            image._coreimage,
            int(image._coreimage.anim_delay * self.maxfps + 3)
        ))

    def test_local_zipsequence(self):
        # cube ZIP has 63 PNGs used for animation
        ZIP = join(
            # kivy/examples/.../cube.zip
            dirname(dirname(dirname(abspath(__file__)))),
            'examples', 'widgets', 'sequenced_images',
            'data', 'images', 'cube.zip'
        )
        ZIP_pngs = self.zip_frames(ZIP)

        image = self.load_zipimage(ZIP, ZIP_pngs)
        # pure delay * fps isn't enough and
        # just +1 isn't either (index collisions)
        self.assertTrue(self.check_sequence_frames(
            image._coreimage,
            int(image._coreimage.anim_delay * self.maxfps + 3)
        ))

    def check_sequence_frames(self, img, frames, slides=5):
        # check whether it really changes the images
        # in the anim_delay interval
        old = None

        while slides:
            # different frames, sequence is changing
            self.assertNotEqual(img.anim_index, old)

            old = img.anim_index
            self.advance_frames(
                frames
            )
            slides -= 1

        return True


if __name__ == '__main__':
    import unittest
    unittest.main()
