'''
Icon generator
==============

This tool will help you to generate all the icons wanted for Google Play Store,
App Store, Amazon store.
'''

import sys
from PIL import Image
from os.path import exists, join, realpath, basename, dirname
from os import makedirs
from argparse import ArgumentParser


class Converter(object):

    converters = {
        'appstore': {
            'directory_name': 'ios',
            'sizes': [
                ('App store high resolution', '{}-appstore-1024.png', 1024),
                ('App store normal resolution', '{}-appstore-512.png', 512),
                # iOS 7
                ('iPhone (iOS 7)', '{}-60.png', 120),
                ('iPhone @2 (iOS 7)', '{}-60@2x.png', 120),
                ('iPad (iOS 7)', '{}-76.png', 76),
                ('iPad @2 (iOS 7)', '{}-60@2x.png', 152),
                # iOS 6.1 and earlier
                ('iPhone (iOS >= 6.1)', '{}-57.png', 57),
                ('iPhone @2 (iOS >= 6.1)', '{}-57@2x.png', 114),
                ('iPad (iOS >= 6.1)', '{}-72.png', 72),
                ('iPad @2 (iOS >= 6.1)', '{}-72@2x.png', 114),
                # iTunes artwork (ad-hoc)
                ('iTunes Artwork (ad-hoc)', 'iTunesArtwork', 512),
                ('iTunes Artwork @2 (ad-hoc)', 'iTunesArtwork@2x', 1024),
            ]},
        'playstore': {
            'directory_name': 'android',
            'sizes': [
                ('Google Play icon', '{}-googleplay-512.png', 512),
                ('Launcher icon MDPI', '{}-48.png', 48),
                ('Launcher icon HDPI', '{}-72.png', 72),
                ('Launcher icon XHDPI', '{}-96.png', 96),
                ('Launcher icon XXHDPI', '{}-144.png', 48),
                ('Launcher icon XXXHDPI', '{}-192.png', 192),
            ]},
        'amazonstore': {
            'directory_name': 'amazon',
            'sizes': [
                ('Small icon', '{}-114.png', 114),
                ('Large icon', '{}-512.png', 512),
            ]}}

    def run(self):
        parser = ArgumentParser(
                description='Generate icons for various stores')
        parser.add_argument('--dir', type=str, default=None,
                help=('Output directory to generate all the icons,'
                      'defaults to the directory of the source icon'))
        parser.add_argument('--force', type=bool, default=False,
                help=('Generate all icons even if the source is not perfect.'))
        parser.add_argument('icon', type=str,
                help='Base icon (must be 1024x1024 or 512x512)')

        args = parser.parse_args()
        if not exists(args.icon):
            print('Error: No such icon file')
            sys.exit(1)

        # ensure the destination directory will be set
        if args.dir is None:
            args.dir = dirname(args.icon)

        # read the source image, and do some quality checks
        base_fn = basename(args.icon).rsplit('.', 1)[0]
        source = Image.open(args.icon)
        self.ensure_quality(source, args.force)

        for directory_name, sizeinfo in self.iterate():
            description, pattern_fn, size = sizeinfo
            print('Generate {}: {}x{}'.format(description, size, size))
            dest_dir = realpath(join(args.dir, directory_name))
            if not exists(dest_dir):
                makedirs(dest_dir)
            icon_fn = join(dest_dir, pattern_fn.format('Icon'))
            self.convert_to(source, icon_fn, size)

    def convert_to(self, source, icon_fn, size):
        dest = source.resize((size, size))
        dest.save(icon_fn, 'png')

    def ensure_quality(self, image, force=False):
        messages = []
        w, h = image.size
        if w != h:
            messages.append('Width and height should be the same')
        if w not in (512, 1024):
            messages.append(
                'Source image is recommended to be 1024 (512 minimum)')
        if not messages:
            return

        print('Quality check failed')
        for message in messages:
            print('- {}'.format(message))
        if not force:
            sys.exit(1)

    def iterate(self):
        for store, infos in Converter.converters.items():
            for size in infos['sizes']:
                yield infos['directory_name'], size


if __name__ == '__main__':
    Converter().run()
