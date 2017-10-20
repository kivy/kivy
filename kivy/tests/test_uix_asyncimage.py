from kivy.tests.common import GraphicUnitTest

from kivy.uix.image import AsyncImage
from kivy.config import Config


class AsyncImageTestCase(GraphicUnitTest):
    def test_remote_zipsequence(self):
        # cube ZIP has 63 PNGs used for animation
        ZIP = (
            'https://github.com/kivy/kivy/'
            'raw/master/examples/widgets/'
            'sequenced_images/data/images/cube.zip'
        )

        # !!! try to open the file and check
        # textures manually (stronger test)
        ZIP_pngs = 63

        # keep running the test until loaded (or timeout)
        maxfps = Config.getint('graphics', 'maxfps')
        timeout = 30 * maxfps

        # load *remote* ZIP with images
        # (named 000.png, 001.png, ...)
        image = AsyncImage(
            source=ZIP,
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
        self.assertEqual(len(proxyimg.image.textures), ZIP_pngs)

        # pure delay * fps isn't enough and
        # just +1 isn't either (index collisions)
        self.assertTrue(self.check_sequence_frames(
            proxyimg,
            int(proxyimg.anim_delay * maxfps + 3)
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
