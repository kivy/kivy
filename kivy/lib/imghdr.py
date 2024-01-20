'''
Python Imghdr
=============

Recognize image file formats based on their first few bytes.

The initial version was written by the python community.
All the initial work credits goes to them! Thank you :)

This version has been maintained to address its planned removal
in Python 3.13 by the Python community. Its continued existence
is necessary for compatibility with the Kivy framework.
'''

from os import PathLike

__all__ = ["what"]


# ------------------------------- #
# Subroutines per image file type #
# ------------------------------- #

img_types = []


def img_jpeg(h):
    """JPEG data with JFIF or Exif markers; and raw JPEG"""
    return 'jpeg' if h[6:10] in (b'JFIF', b'Exif') or h[:4] == b'\xff\xd8\xff\xdb' else None


img_types.append(img_jpeg)


def img_png(h):
    """PNG"""
    return 'png' if h.startswith(b'\211PNG\r\n\032\n') else None


img_types.append(img_png)


def img_gif(h):
    """GIF ('87 and '89 variants)"""
    return 'gif' if h[:6] in (b'GIF87a', b'GIF89a') else None


img_types.append(img_gif)


def img_tiff(h):
    """TIFF (can be in Motorola or Intel byte order)"""
    return 'tiff' if h[:2] in (b'MM', b'II') else None


img_types.append(img_tiff)


def img_rgb(h):
    """SGI image library"""
    return 'rgb' if h.startswith(b'\001\332') else None


img_types.append(img_rgb)


def img_pbm(h):
    """PBM (portable bitmap)"""
    return 'pbm' if len(h) >= 3 and h[0] == ord(b'P') and h[1] in b'14' and h[2] in b' \t\n\r' else None


img_types.append(img_pbm)


def img_pgm(h):
    """PGM (portable graymap)"""
    return 'pgm' if len(h) >= 3 and h[0] == ord(b'P') and h[1] in b'25' and h[2] in b' \t\n\r' else None


img_types.append(img_pgm)


def img_ppm(h):
    """PPM (portable pixmap)"""
    return 'ppm' if len(h) >= 3 and h[0] == ord(b'P') and h[1] in b'36' and h[2] in b' \t\n\r' else None


img_types.append(img_ppm)


def img_rast(h):
    """Sun raster file"""
    return 'rast' if h.startswith(b'\x59\xA6\x6A\x95') else None


img_types.append(img_rast)


def img_xbm(h):
    """X bitmap (X10 or X11)"""
    return 'xbm' if h.startswith(b'#define ') else None


img_types.append(img_xbm)


def img_bmp(h):
    """BMP"""
    return 'bmp' if h.startswith(b'BM') else None


img_types.append(img_bmp)


def img_webp(h):
    """WEBP"""
    return 'webp' if h.startswith(b'RIFF') and h[8:12] == b'WEBP' else None


img_types.append(img_webp)


def img_exr(h):
    """EXR"""
    return 'exr' if h.startswith(b'\x76\x2f\x31\x01') else None


img_types.append(img_exr)


# ----------------------- #
# Recognize image headers #
# ----------------------- #

def what(file, h=None):
    if not h and isinstance(file, (str, PathLike)):
        with open(file, "rb") as f:
            h = f.read(32)
    else:
        location = file.tell()
        h = file.read(32)
        file.seek(location)
    res = None
    for ft in img_types:
        res = ft(h)
        if res:
            break
    return res


# --------------------#
# Small test program #
# --------------------#

def test():
    import sys
    recursive = 0
    if sys.argv[1:] and sys.argv[1] == '-r':
        del sys.argv[1:2]
        recursive = 1
    try:
        if sys.argv[1:]:
            testall(sys.argv[1:], recursive, 1)
        else:
            testall(['.'], recursive, 1)
    except KeyboardInterrupt:
        sys.stderr.write('\n[Interrupted]\n')
        sys.exit(1)


def testall(lst, recursive, toplevel):
    import sys
    import os
    for filename in lst:
        if os.path.isdir(filename):
            print(filename + '/:', end=' ')
            if recursive or toplevel:
                print('recursing down:')
                import glob
                names = glob.glob(os.path.join(glob.escape(filename), '*'))
                testall(names, recursive, 0)
            else:
                print('*** directory (use -r) ***')
        else:
            print(filename + ':', end=' ')
            sys.stdout.flush()
            try:
                print(what(filename))
            except OSError:
                print('*** not found ***')


if __name__ == '__main__':
    test()
