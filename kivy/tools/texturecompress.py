#:/usr/bin/env python2.7
'''
Texture compression tool
========================

This tool is designed to compress images into:

- PVRTC (PowerVR Texture Compression), mostly iOS devices
- ETC1 (Ericson compression), working on all GLES2/Android devices

Usage
-----

In order to compress a texture::

    texturecompress.py [--dir <directory>] <format> <image.png>

This will create a `image.tex` file with a json header that contains all the
image information and the compressed data.

TODO
----

Support more format, such as:

- S3TC (already supported in Kivy)
- DXT1 (already supported in Kivy)
'''

import json
from struct import pack
from pprint import pprint
from subprocess import Popen
from PIL import Image
from argparse import ArgumentParser
from sys import exit
from os.path import join, exists, dirname, basename
from os import environ, unlink


class Tool(object):
    def __init__(self, options):
        super(Tool, self).__init__()
        self.options = options
        self.source_fn = options.image
        self.dest_dir = options.dir or dirname(options.image)

    @property
    def tex_fn(self):
        fn = basename(self.source_fn).rsplit('.', 1)[0] + '.tex'
        return join(self.dest_dir, fn)

    def compress(self):
        pass

    def nearest_pow2(self, v):
        # Credits: Sean Anderson
        v -= 1
        v |= v >> 1
        v |= v >> 2
        v |= v >> 4
        v |= v >> 8
        v |= v >> 16
        return v + 1

    def runcmd(self, cmd):
        print('Run: {}'.format(' '.join(cmd)))
        Popen(cmd).communicate()

    def write_tex(self, data, fmt, image_size, texture_size, mipmap=False,
            formatinfo=None):
        infos = {
            'datalen': len(data),
            'image_size': image_size,
            'texture_size': texture_size,
            'mipmap': mipmap,
            'format': fmt}
        if formatinfo:
            infos['formatinfo'] = formatinfo
        header = json.dumps(infos, indent=0, separators=(',', ':'))
        header = header.replace('\n', '')
        with open(self.tex_fn, 'wb') as fd:
            fd.write('KTEX')
            fd.write(pack('I', len(header)))
            fd.write(header)
            fd.write(data)

        print('Done! Compressed texture written at {}'.format(self.tex_fn))
        pprint(infos)

    @staticmethod
    def run():
        parser = ArgumentParser(
                description='Convert images to compressed texture')
        parser.add_argument('--mipmap', type=bool, default=False,
                help='Auto generate mipmaps')
        parser.add_argument('--dir', type=str, default=None,
                help='Output directory to generate the compressed texture')
        parser.add_argument('format', type=str, choices=['pvrtc', 'etc1'],
                help='Format of the final texture')
        parser.add_argument('image', type=str,
                help='Image filename')
        args = parser.parse_args()

        if args.format == 'pvrtc':
            PvrtcTool(args).compress()
        elif args.format == 'etc1':
            Etc1Tool(args).compress()
        else:
            print('Unknown compression format')
            exit(1)


class Etc1Tool(Tool):
    def __init__(self, options):
        super(Etc1Tool, self).__init__(options)
        self.etc1tool = None
        self.locate_etc1tool()

    def locate_etc1tool(self):
        search_directories = [environ.get('ANDROIDSDK', '/')]
        search_directories += environ.get('PATH', '').split(':')
        for directory in search_directories:
            fn = join(directory, 'etc1tool')
            if not exists(fn):
                fn = join(directory, 'tools', 'etc1tool')
                if not exists(fn):
                    continue
            print('Found texturetool at {}'.format(directory))
            self.etc1tool = fn
            return

        if self.etc1tool is None:
            print('Error: Unable to locate "etc1tool".\n'
                  'Make sure that "etc1tool" is available in your PATH.\n'
                  'Or export the path of your Android SDK to ANDROIDSDK')
            exit(1)

    def compress(self):
        # 1. open the source image, and get the dimensions
        image = Image.open(self.source_fn)
        w, h = image.size
        print('Image size is {}x{}'.format(*image.size))

        # 2. search the nearest 2^
        w2 = self.nearest_pow2(w)
        h2 = self.nearest_pow2(h)
        print('Nearest power-of-2 size is {}x{}'.format(w2, h2))

        # 3. invoke etc1tool
        raw_tex_fn = self.tex_fn + '.raw'
        cmd = [self.etc1tool, self.source_fn, '--encodeNoHeader', '-o',
               raw_tex_fn]
        try:
            self.runcmd(cmd)
            with open(raw_tex_fn, 'rb') as fd:
                data = fd.read()
        finally:
            if exists(raw_tex_fn):
                unlink(raw_tex_fn)

        # 5. write texture info
        self.write_tex(data, 'etc1_rgb8', (w, h), (w2, h2), self.options.mipmap)


class PvrtcTool(Tool):
    def __init__(self, options):
        super(PvrtcTool, self).__init__(options)
        self.texturetool = None
        self.locate_texturetool()

    def locate_texturetool(self):
        search_directories = [
            ('/Applications/Xcode.app/Contents/Developer/Platforms/'
             'iPhoneOS.platform/Developer/usr/bin/'),
            '/Developer/Platforms/iPhoneOS.platform/Developer/usr/bin/']
        search_directories += environ.get('PATH', '').split(':')

        for directory in search_directories:
            fn = join(directory, 'texturetool')
            if not exists(fn):
                continue
            print('Found texturetool at {}'.format(directory))
            self.texturetool = fn
            return

        print('Error: Unable to locate "texturetool".\n'
              'Please install the iPhone SDK, or the PowerVR SDK.\n'
              'Then make sure that "texturetool" is available in your PATH.')
        exit(1)

    def compress(self):
        # 1. open the source image, and get the dimensions
        image = Image.open(self.source_fn)
        w, h = image.size
        print('Image size is {}x{}'.format(*image.size))

        # 2. search the nearest 2^
        w2 = self.nearest_pow2(w)
        h2 = self.nearest_pow2(h)
        print('Nearest power-of-2 size is {}x{}'.format(w2, h2))

        # 3. for PVR, the image MUST be a square. use the bigger size then
        s2 = max(w2, h2)
        print('PVR need a square image, the texture will be {0}x{0}'.format(s2))

        # 4. invoke texture tool
        raw_tex_fn = self.tex_fn + '.raw'
        cmd = [self.texturetool]
        if self.options.mipmap:
            cmd += ['-m']
        cmd += ['-e', 'PVRTC', '-o', raw_tex_fn, '-f', 'RAW', self.source_fn]
        try:
            self.runcmd(cmd)
            with open(raw_tex_fn, 'rb') as fd:
                data = fd.read()
        finally:
            if exists(raw_tex_fn):
                unlink(raw_tex_fn)

        # 5. write texture info
        self.write_tex(data, 'pvrtc_rgba4', (w, h), (s2, s2),
                       self.options.mipmap)


if __name__ == '__main__':
    Tool.run()
