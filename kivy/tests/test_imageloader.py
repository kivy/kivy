import os
import re
import unittest
from pprint import pprint
from kivy.core.image import ImageLoader

# "make testimages" is required to enable this test
# See kivy/tools/create-testimages.sh for more information

DEBUG = False
ASSETDIR = 'testimages'
LOADERS = {x.__name__: x for x in ImageLoader.loaders}

if 'ImageLoaderPygame' not in LOADERS:
    try:
        from kivy.core.image.img_pygame import ImageLoaderPygame
        LOADERS['ImageLoaderPygame'] = ImageLoaderPygame
    except:
        pass


def asset(*fn):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), *fn))


def has_alpha(fmt):
    return fmt in ('rgba', 'bgra', 'argb', 'abgr')


def bytes_per_pixel(fmt):
    if fmt in ('rgb', 'bgr'):
        return 3
    if fmt in ('rgba', 'bgra', 'argb', 'abgr'):
        return 4
    raise Exception('bytes_per_pixel: unknown format {}'.format(fmt))


# Generate RGBA pixel predictions from pattern + alpha. When testing
# "1x3_rgb_FF" is processed here as pat='rgb' and alpha='FF'. Returns a list
# of bytes objects representing accepted pixel data
def pattern_to_predictions(pat, alpha='FF'):
    assert len(alpha) == 2
    assert len(pat) >= 1
    PIXELS = {
        'w': b'\xFF\xFF\xFF', 'x': b'\x00\x00\x00',  # 't' is below
        'r': b'\xFF\x00\x00', 'g': b'\x00\xFF\x00', 'b': b'\x00\x00\xFF',
        'y': b'\xFF\xFF\x00', 'c': b'\x00\xFF\xFF', 'p': b'\xFF\x00\xFF',
        '0': b'\x00\x00\x00', '1': b'\x11\x11\x11', '2': b'\x22\x22\x22',
        '3': b'\x33\x33\x33', '4': b'\x44\x44\x44', '5': b'\x55\x55\x55',
        '6': b'\x66\x66\x66', '7': b'\x77\x77\x77', '8': b'\x88\x88\x88',
        '9': b'\x99\x99\x99', 'A': b'\xAA\xAA\xAA', 'B': b'\xBB\xBB\xBB',
        'C': b'\xCC\xCC\xCC', 'D': b'\xDD\xDD\xDD', 'E': b'\xEE\xEE\xEE',
        'F': b'\xFF\xFF\xFF'}

    # Some loaders/formats/conversion processes can result in binary
    # transparency represented as white+a00 or black+a00 - we accept
    # both variations for a 't' pixel
    pixelmaps = []
    if 't' in pat:
        pixelmaps = [dict(PIXELS, t=x) for x in (b'\x00' * 3, b'\xFF' * 3)]
    else:
        pixelmaps = [PIXELS]

    alphamap = lambda x: x == 't' and b'\x00' or bytearray.fromhex(alpha)
    out = []
    for pm in pixelmaps:
        out.append(b''.join([bytes(pm.get(p) + alphamap(p)) for p in pat]))
    return out


# Converts (predicted) rgba pixels to the format claimed by image loader
def rgba_to(pix_in, target_fmt, w, h, pitch=None):
    assert w > 0 and h > 0, "Must specify w and h"
    assert len(pix_in) == w * h * 4, "Invalid rgba pixel data"
    assert target_fmt in ('rgba', 'bgra', 'argb', 'abgr', 'rgb', 'bgr')

    if target_fmt == 'rgba':
        return pix_in

    pixels = [pix_in[i:i + 4] for i in range(0, len(pix_in), 4)]
    if target_fmt == 'bgra':
        return b''.join([p[:3][::-1] + p[3:] for p in pixels])
    elif target_fmt == 'abgr':
        return b''.join([p[3:] + p[:3][::-1] for p in pixels])
    elif target_fmt == 'argb':
        return b''.join([p[3:] + p[:3] for p in pixels])

    # rgb/bgr, default to 4 byte alignment
    if pitch is None:
        pitch = ((3 * w) + 3) & ~3
    # Assume pitch 0 == unaligned
    elif pitch == 0:
        pitch = 3 * w

    out = b''
    padding = b'\0' * (pitch - w * 3)
    for row in [pix_in[i:i + w * 4] for i in range(0, len(pix_in), w * 4)]:
        pixelrow = [row[i:i + 4] for i in range(0, len(row), 4)]
        if target_fmt == 'rgb':
            out += b''.join([p[:3] for p in pixelrow])
        elif target_fmt == 'bgr':
            out += b''.join([p[:3][::-1] for p in pixelrow])
        out += padding

    return out


class TestContext(object):
    def __init__(self, loadercls):
        self.loadercls = loadercls
        self._fn = None
        self._ok = 0
        self._skip = 0
        self._fail = 0

    @property
    def results(self):
        return (self._ok, self._skip, self._fail)

    def start(self, fn):
        assert not self._fn, "unexpected ctx.start(), already started"
        self._fn = fn

    def end(self, fn=None):
        assert not fn or self._fn == fn, "unexpected ctx.end(), fn mismatch"
        self._fn = None

    def ok(self, info):
        assert self._fn, "unexpected ctx.ok(), fn=None"
        self._ok += 1
        self.dbg('PASS', info)
        self.end(self._fn)

    def skip(self, info):
        assert self._fn, "unexpected ctx.skip(), fn=None"
        self._skip += 1
        self.dbg('SKIP', info)
        self.end(self._fn)

    def fail(self, info):
        assert self._fn, "unexpected ctx.fail(), fn=None"
        self._fail += 1
        self.dbg('FAIL', info)
        self.end(self._fn)

    def dbg(self, msgtype, info):
        assert self._fn, "unexpected ctx.dbg(), fn=None"
        if DEBUG:
            print("{} {} {}: {}"
                  .format(self.loadercls.__name__, msgtype, self._fn, info))


@unittest.skipIf(not os.path.isdir(asset(ASSETDIR)),
                 "Need 'make testimages' to run test")
class ImageLoaderTestCase(unittest.TestCase):

    # Matches generated file names
    FILE_RE = re.compile('^v0_(\d+)x(\d+)_'
                         '([wxrgbycptA-F0-9]+)_'
                         '([0-9A-Fa-f]{2})_'
                         '([\w_]+)\.([a-z]+)$')

    def setUp(self):
        self._prepare_images()

    def _prepare_images(self):
        self._image_files = {}
        for filename in os.listdir(asset(ASSETDIR)):
            matches = self.FILE_RE.match(filename)
            if not matches:
                continue
            w, h, pat, alpha, info, ext = matches.groups()
            self._image_files[filename] = {
                'w': int(w),
                'h': int(h),
                'alpha': alpha,
                'ext': ext,
                'info': info,
                'pattern': pat,
                'predictions': pattern_to_predictions(pat, alpha),
                'require_alpha': 'BINARY' in info or 'ALPHA' in info,
            }

    def _test_imageloader(self, loadercls, extensions=None):
        if not loadercls:
            return
        if not extensions:
            extensions = loadercls.extensions()

        ctx = TestContext(loadercls)
        for filename in sorted(self._image_files.keys()):
            filedata = self._image_files[filename]

            if filedata['ext'] not in extensions:
                continue
            try:
                ctx.start(filename)
                result = loadercls(asset(ASSETDIR, filename), keep_data=True)
                if not result:
                    raise Exception('invalid result')
            except:
                ctx.skip('Error loading file, result=None')
                continue
            self._test_image(filedata, ctx, loadercls, filename, result)
            ctx.end()

        ok, skip, fail = ctx.results
        if fail:
            self.fail('{}: {} passed, {} skipped, {} failed'
                      .format(loadercls.__name__, ok, skip, fail))
        return ctx

    def _test_image(self, fd, ctx, loadercls, fn, imgdata):
        w, h, pixels, pitch = imgdata._data[0].get_mipmap(0)
        fmt = imgdata._data[0].fmt

        # required for FFPy memview
        if not isinstance(pixels, bytes):
            pixels = bytearray(pixels)

        # Convert RGBA prediction to imageloaders returned format
        predictions = [rgba_to(pix, fmt, fd['w'], fd['h'], pitch=pitch)
                       for pix in fd['predictions']]

        def debug():
            if not DEBUG:
                return
            print("    format: {}x{} {}".format(w, h, fmt))
            print("     pitch: got {} (want {})".format(pitch, want_pitch))
            if pixels not in predictions:
                print("     ERROR: Mismatch")
                for p in predictions:
                    print(" predicted: {}".format(p))
                print("       got: {}".format(bytearray(pixels)))
            else:
                print("        OK: Pixel data matches")

        # Assume pitch 0 = unaligned
        want_pitch = (pitch == 0) and bytes_per_pixel(fmt) * w or pitch
        if pitch == 0 and bytes_per_pixel(fmt) * w * h != len(pixels):
            ctx.dbg("PITCH", "pitch=0, expected fmt={} to be "
                             "unaligned @ ({}bpp) = {} bytes, got {}"
                             .format(fmt, bytes_per_pixel(fmt),
                                     bytes_per_pixel(fmt) * w * h,
                                     len(pixels)))
        elif pitch and want_pitch != pitch:
            ctx.dbg("PITCH", "fmt={}, pitch={}, expected {}"
                             .format(fmt, pitch, want_pitch))

        if pixels not in predictions:
            ctx.fail('Pixel data mismatch')
            debug()
        elif fd['require_alpha'] and not has_alpha(fmt):
            ctx.fail('Missing expected alpha channel')
            debug()
        elif fd['w'] != w:
            ctx.fail('Width mismatch, want {} got {}'
                     .format(fd['w'], w))
            debug()
        elif fd['h'] != h:
            ctx.fail('Height mismatch, want {} got {}'
                     .format(fd['h'], h))
            debug()
        elif w != 1 and h != 1:
            ctx.fail('v0 test protocol mandates w=1 or h=1')
            debug()
        else:
            ctx.ok("Passed test as {}x{} {}".format(w, h, fmt))

    def test_ImageLoaderSDL2(self):
        loadercls = LOADERS.get('ImageLoaderSDL2')
        # GIF format not listed as supported in sdl2 loader
        if loadercls:
            exts = list(loadercls.extensions()) + ['gif']
            ctx = self._test_imageloader(loadercls, exts)

    def test_ImageLoaderPIL(self):
        loadercls = LOADERS.get('ImageLoaderPIL')
        # PIL fails with all magick SGI format files, skip test
        if loadercls:
            exts = list(loadercls.extensions())
            exts.remove('sgi')
            ctx = self._test_imageloader(loadercls, exts)

    def test_ImageLoaderPygame(self):
        loadercls = LOADERS.get('ImageLoaderPygame')
        ctx = self._test_imageloader(loadercls)

    def test_ImageLoaderFFPy(self):
        loadercls = LOADERS.get('ImageLoaderFFPy')
        ctx = self._test_imageloader(loadercls)

    def test_ImageLoaderGIF(self):
        loadercls = LOADERS.get('ImageLoaderGIF')
        ctx = self._test_imageloader(loadercls)

    def test_ImageLoaderDDS(self):
        loadercls = LOADERS.get('ImageLoaderDDS')
        ctx = self._test_imageloader(loadercls)

    def test_ImageLoaderTex(self):
        loadercls = LOADERS.get('ImageLoaderTex')
        ctx = self._test_imageloader(loadercls)

    def test_missing_tests(self):
        for loader in ImageLoader.loaders:
            key = 'test_{}'.format(loader.__name__)
            msg = "Missing ImageLoader test case: {}".format(key)
            self.assertTrue(hasattr(self, key), msg)
            self.assertTrue(callable(getattr(self, key)), msg)


class ConverterTestCase(unittest.TestCase):
    def test_internal_converter_2x1(self):
        correct = {
            'rgba': b'\x01\x02\x03\xA1\x04\x05\x06\xA2',
            'abgr': b'\xA1\x03\x02\x01\xA2\x06\x05\x04',
            'bgra': b'\x03\x02\x01\xA1\x06\x05\x04\xA2',
            'argb': b'\xA1\x01\x02\x03\xA2\x04\x05\x06',
            'rgb': b'\x01\x02\x03\x04\x05\x06',
            'bgr': b'\x03\x02\x01\x06\x05\x04',
            'rgb_align4': b'\x01\x02\x03\x04\x05\x06\x00\x00',
            'bgr_align4': b'\x03\x02\x01\x06\x05\x04\x00\x00'}
        src = correct.get
        rgba = src('rgba')
        self.assertEqual(rgba_to(rgba, 'rgba', 2, 1, 0), src('rgba'))
        self.assertEqual(rgba_to(rgba, 'abgr', 2, 1, 0), src('abgr'))
        self.assertEqual(rgba_to(rgba, 'bgra', 2, 1, 0), src('bgra'))
        self.assertEqual(rgba_to(rgba, 'argb', 2, 1, 0), src('argb'))
        self.assertEqual(rgba_to(rgba, 'rgb', 2, 1, 0), src('rgb'))
        self.assertEqual(rgba_to(rgba, 'bgr', 2, 1, 0), src('bgr'))
        self.assertEqual(rgba_to(rgba, 'rgb', 2, 1, None), src('rgb_align4'))
        self.assertEqual(rgba_to(rgba, 'bgr', 2, 1, None), src('bgr_align4'))

    def test_internal_converter_3x1(self):
        pad6 = b'\x00' * 6
        correct = {
            'rgba': b'\x01\x02\x03\xFF\x04\x05\x06\xFF\x07\x08\x09\xFF',
            'abgr': b'\xFF\x03\x02\x01\xFF\x06\x05\x04\xFF\x09\x08\x07',
            'bgra': b'\x03\x02\x01\xFF\x06\x05\x04\xFF\x09\x08\x07\xFF',
            'argb': b'\xFF\x01\x02\x03\xFF\x04\x05\x06\xFF\x07\x08\x09',
            'rgb_align2': b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x00',
            'bgr_align2': b'\x03\x02\x01\x06\x05\x04\x09\x08\x07\x00',
            'rgb_align8': b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x00' + pad6,
            'bgr_align8': b'\x03\x02\x01\x06\x05\x04\x09\x08\x07\x00' + pad6}
        src = correct.get
        rgba = src('rgba')
        self.assertEqual(rgba_to(rgba, 'bgra', 3, 1, 0), src('bgra'))
        self.assertEqual(rgba_to(rgba, 'argb', 3, 1, 0), src('argb'))
        self.assertEqual(rgba_to(rgba, 'abgr', 3, 1, 0), src('abgr'))
        self.assertEqual(rgba_to(rgba, 'rgb', 3, 1, 10), src('rgb_align2'))
        self.assertEqual(rgba_to(rgba, 'bgr', 3, 1, 10), src('bgr_align2'))
        self.assertEqual(rgba_to(rgba, 'rgb', 3, 1, 16), src('rgb_align8'))
        self.assertEqual(rgba_to(rgba, 'bgr', 3, 1, 16), src('bgr_align8'))

    def test_internal_converter_1x3(self):
        pad5 = b'\x00' * 5
        correct = {
            'rgba': b'\x01\x02\x03\xFF\x04\x05\x06\xFF\x07\x08\x09\xFF',
            'rgb_raw': b'\x01\x02\x03\x04\x05\x06\x07\x08\x09',
            'bgr_raw': b'\x03\x02\x01\x06\x05\x04\x09\x08\x07',
            'rgb_align2': b'\x01\x02\x03\x00\x04\x05\x06\x00\x07\x08\x09\x00',
            'bgr_align2': b'\x03\x02\x01\x00\x06\x05\x04\x00\x09\x08\x07\x00',
            'rgb_align4': b'\x01\x02\x03\x00\x04\x05\x06\x00\x07\x08\x09\x00',
            'bgr_align4': b'\x03\x02\x01\x00\x06\x05\x04\x00\x09\x08\x07\x00',
            'rgb_align8': (b'\x01\x02\x03' + pad5 +
                           b'\x04\x05\x06' + pad5 +
                           b'\x07\x08\x09' + pad5),
            'bgr_align8': (b'\x03\x02\x01' + pad5 +
                           b'\x06\x05\x04' + pad5 +
                           b'\x09\x08\x07' + pad5),
        }
        src = correct.get
        rgba = src('rgba')
        self.assertEqual(rgba_to(rgba, 'rgb', 1, 3, 4), src('rgb_align2'))
        self.assertEqual(rgba_to(rgba, 'bgr', 1, 3, 4), src('bgr_align2'))
        self.assertEqual(rgba_to(rgba, 'rgb', 1, 3, None), src('rgb_align4'))
        self.assertEqual(rgba_to(rgba, 'bgr', 1, 3, None), src('bgr_align4'))
        self.assertEqual(rgba_to(rgba, 'rgb', 1, 3, 0), src('rgb_raw'))
        self.assertEqual(rgba_to(rgba, 'bgr', 1, 3, 0), src('bgr_raw'))
        self.assertEqual(rgba_to(rgba, 'rgb', 1, 3, 8), src('rgb_align8'))
        self.assertEqual(rgba_to(rgba, 'bgr', 1, 3, 8), src('bgr_align8'))


if __name__ == '__main__':
    import sys
    accept_filter = ['ImageLoader{}'.format(x) for x in sys.argv[1:]]
    if accept_filter:
        LOADERS = {x: LOADERS[x] for x in accept_filter}

    DEBUG = True
    unittest.main(argv=sys.argv[:1])
