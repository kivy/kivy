'''
Atlas
=====

.. versionadded:: 1.1.0

Atlas manages texture atlases: packing multiple textures into
one. With it, you reduce the number of images loaded and speedup the
application loading. This module contains both the Atlas class and command line
processing for creating an atlas from a set of individual PNG files. The
command line section requires the Pillow library, or the defunct Python Imaging
Library (PIL), to be installed.

An Atlas is composed of 2 or more files:
    - a json file (.atlas) that contains the image file names and texture
      locations of the atlas.
    - one or multiple image files containing textures referenced by the .atlas
      file.

Definition of .atlas files
--------------------------

A file with ``<basename>.atlas`` is a json file formatted like this::

    {
        "<basename>-<index>.png": {
            "id1": [ <x>, <y>, <width>, <height> ],
            "id2": [ <x>, <y>, <width>, <height> ],
            # ...
        },
        # ...
    }

Example from the Kivy ``data/images/defaulttheme.atlas``::

    {
        "defaulttheme-0.png": {
            "progressbar_background": [431, 224, 59, 24],
            "image-missing": [253, 344, 48, 48],
            "filechooser_selected": [1, 207, 118, 118],
            "bubble_btn": [83, 174, 32, 32],
            # ... and more ...
        }
    }

In this example, "defaulttheme-0.png" is a large image, with the pixels in the
rectangle from (431, 224) to (431 + 59, 224 + 24) usable as
``atlas://data/images/defaulttheme/progressbar_background`` in
any image parameter.

How to create an Atlas
----------------------

.. warning::

    The atlas creation requires the Pillow library (or the defunct Imaging/PIL
    library). This requirement will be removed in the future when the Kivy core
    Image is able to support loading, blitting, and saving operations.

You can directly use this module to create atlas files with this command::

    $ python -m kivy.atlas <basename> <size> <list of images...>


Let's say you have a list of images that you want to put into an Atlas. The
directory is named ``images`` with lots of 64x64 png files inside::

    $ ls
    images
    $ cd images
    $ ls
    bubble.png bubble-red.png button.png button-down.png

You can combine all the png's into one and generate the atlas file with::

    $ python -m kivy.atlas myatlas 256x256 *.png
    Atlas created at myatlas.atlas
    1 image has been created
    $ ls
    bubble.png bubble-red.png button.png button-down.png myatlas.atlas
    myatlas-0.png

As you can see, we get 2 new files: ``myatlas.atlas`` and ``myatlas-0.png``.
``myatlas-0.png`` is a new 256x256 .png composed of all your images.

.. note::

    When using this script, the ids referenced in the atlas are the base names
    of the images without the extension. So, if you are going to name a file
    ``../images/button.png``, the id for this image will be ``button``.

    If you need path information included, you should include ``use_path`` as
    follows::

        $ python -m kivy.atlas use_path myatlas 256 *.png

    In which case the id for ``../images/button.png`` will be ``images_button``


How to use an Atlas
-------------------

Usually, you would specify the images by supplying the path::

    a = Button(background_normal='images/button.png',
               background_down='images/button_down.png')

In our previous example, we have created the atlas containing both images and
put them in ``images/myatlas.atlas``. You can use url notation to reference
them::

    a = Button(background_normal='atlas://images/myatlas/button',
               background_down='atlas://images/myatlas/button_down')

In other words, the path to the images is replaced by::

    atlas://path/to/myatlas/id
    # will search for the ``path/to/myatlas.atlas`` and get the image ``id``

.. note::

    In the atlas url, there is no need to add the ``.atlas`` extension. It will
    be automatically append to the filename.

Manual usage of the Atlas
-------------------------

::

    >>> from kivy.atlas import Atlas
    >>> atlas = Atlas('path/to/myatlas.atlas')
    >>> print(atlas.textures.keys())
    ['bubble', 'bubble-red', 'button', 'button-down']
    >>> print(atlas['button'])
    <kivy.graphics.texture.TextureRegion object at 0x2404d10>
'''

__all__ = ('Atlas', )

import json
from os.path import basename, dirname, join, splitext
from kivy.event import EventDispatcher
from kivy.logger import Logger
from kivy.properties import AliasProperty, DictProperty, ListProperty
import os


# late import to prevent recursion
CoreImage = None


class Atlas(EventDispatcher):
    '''Manage texture atlas. See module documentation for more information.
    '''

    original_textures = ListProperty([])
    '''List of original atlas textures (which contain the :attr:`textures`).

    :attr:`original_textures` is a :class:`~kivy.properties.ListProperty` and
    defaults to [].

    .. versionadded:: 1.9.1
    '''

    textures = DictProperty({})
    '''List of available textures within the atlas.

    :attr:`textures` is a :class:`~kivy.properties.DictProperty` and defaults
    to {}.
    '''

    def _get_filename(self):
        return self._filename

    filename = AliasProperty(_get_filename, None)
    '''Filename of the current Atlas.

    :attr:`filename` is an :class:`~kivy.properties.AliasProperty` and defaults
    to None.
    '''

    def __init__(self, filename):
        self._filename = filename
        super(Atlas, self).__init__()
        self._load()

    def __getitem__(self, key):
        return self.textures[key]

    def _load(self):
        # late import to prevent recursive import.
        global CoreImage
        if CoreImage is None:
            from kivy.core.image import Image as CoreImage

        # must be a name finished by .atlas ?
        filename = self._filename
        assert(filename.endswith('.atlas'))
        filename = filename.replace('/', os.sep)

        Logger.debug('Atlas: Load <%s>' % filename)
        with open(filename, 'r') as fd:
            meta = json.load(fd)

        Logger.debug('Atlas: Need to load %d images' % len(meta))
        d = dirname(filename)
        textures = {}
        for subfilename, ids in meta.items():
            subfilename = join(d, subfilename)
            Logger.debug('Atlas: Load <%s>' % subfilename)

            # load the image
            ci = CoreImage(subfilename)
            atlas_texture = ci.texture
            self.original_textures.append(atlas_texture)

            # for all the uid, load the image, get the region, and put
            # it in our dict.
            for meta_id, meta_coords in ids.items():
                x, y, w, h = meta_coords
                textures[meta_id] = atlas_texture.get_region(*meta_coords)

        self.textures = textures

    @staticmethod
    def create(outname, filenames, size, padding=2, use_path=False):
        '''This method can be used to create an atlas manually from a set of
        images.

        :Parameters:
            `outname`: str
                Basename to use for ``.atlas`` creation and ``-<idx>.png``
                associated images.
            `filenames`: list
                List of filenames to put in the atlas.
            `size`: int or list (width, height)
                Size of the atlas image.
            `padding`: int, defaults to 2
                Padding to put around each image.

                Be careful. If you're using a padding < 2, you might have
                issues with the borders of the images. Because of the OpenGL
                linearization, it might use the pixels of the adjacent image.

                If you're using a padding >= 2, we'll automatically generate a
                "border" of 1px around your image. If you look at
                the result, don't be scared if the image inside is not
                exactly the same as yours :).

            `use_path`: bool, defaults to False
                If True, the relative path of the source png
                file names will be included in the atlas ids rather
                that just in the file names. Leading dots and slashes will be
                excluded and all other slashes in the path will be replaced
                with underscores. For example, if `use_path` is False
                (the default) and the file name is
                ``../data/tiles/green_grass.png``, the id will be
                ``green_grass``. If `use_path` is True, it will be
                ``data_tiles_green_grass``.

            .. versionchanged:: 1.8.0
                Parameter use_path added
        '''
        # Thanks to
        # omnisaurusgames.com/2011/06/texture-atlas-generation-using-python/
        # for its initial implementation.
        try:
            from PIL import Image
        except ImportError:
            Logger.critical('Atlas: Imaging/PIL are missing')
            raise

        if isinstance(size, (tuple, list)):
            size_w, size_h = list(map(int, size))
        else:
            size_w = size_h = int(size)

        # open all of the images
        ims = list()
        for f in filenames:
            fp = open(f, 'rb')
            im = Image.open(fp)
            im.load()
            fp.close()
            ims.append((f, im))

        # sort by image area
        ims = sorted(ims, key=lambda im: im[1].size[0] * im[1].size[1],
                     reverse=True)

        # free boxes are empty space in our output image set
        # the freebox tuple format is: outidx, x, y, w, h
        freeboxes = [(0, 0, 0, size_w, size_h)]
        numoutimages = 1

        # full boxes are areas where we have placed images in the atlas
        # the full box tuple format is: image, outidx, x, y, w, h, filename
        fullboxes = []

        # do the actual atlasing by sticking the largest images we can
        # have into the smallest valid free boxes
        for imageinfo in ims:
            im = imageinfo[1]
            imw, imh = im.size
            imw += padding
            imh += padding
            if imw > size_w or imh > size_h:
                Logger.error(
                    'Atlas: image %s (%d by %d) is larger than the atlas size!'
                    % (imageinfo[0], imw, imh))
                return

            inserted = False
            while not inserted:
                for idx, fb in enumerate(freeboxes):
                    # find the smallest free box that will contain this image
                    if fb[3] >= imw and fb[4] >= imh:
                        # we found a valid spot! Remove the current
                        # freebox, and split the leftover space into (up to)
                        # two new freeboxes
                        del freeboxes[idx]
                        if fb[3] > imw:
                            freeboxes.append((
                                fb[0], fb[1] + imw, fb[2],
                                fb[3] - imw, imh))

                        if fb[4] > imh:
                            freeboxes.append((
                                fb[0], fb[1], fb[2] + imh,
                                fb[3], fb[4] - imh))

                        # keep this sorted!
                        freeboxes = sorted(freeboxes,
                                           key=lambda fb: fb[3] * fb[4])
                        fullboxes.append((im,
                                          fb[0], fb[1] + padding,
                                          fb[2] + padding, imw - padding,
                                          imh - padding, imageinfo[0]))
                        inserted = True
                        break

                if not inserted:
                    # oh crap - there isn't room in any of our free
                    # boxes, so we have to add a new output image
                    freeboxes.append((numoutimages, 0, 0, size_w, size_h))
                    numoutimages += 1

        # now that we've figured out where everything goes, make the output
        # images and blit the source images to the appropriate locations
        Logger.info('Atlas: create an {0}x{1} rgba image'.format(size_w,
                                                                 size_h))
        outimages = [Image.new('RGBA', (size_w, size_h))
                     for i in range(0, int(numoutimages))]
        for fb in fullboxes:
            x, y = fb[2], fb[3]
            out = outimages[fb[1]]
            out.paste(fb[0], (fb[2], fb[3]))
            w, h = fb[0].size
            if padding > 1:
                out.paste(fb[0].crop((0, 0, w, 1)), (x, y - 1))
                out.paste(fb[0].crop((0, h - 1, w, h)), (x, y + h))
                out.paste(fb[0].crop((0, 0, 1, h)), (x - 1, y))
                out.paste(fb[0].crop((w - 1, 0, w, h)), (x + w, y))

        # save the output images
        for idx, outimage in enumerate(outimages):
            outimage.save('%s-%d.png' % (outname, idx))

        # write out an json file that says where everything ended up
        meta = {}
        for fb in fullboxes:
            fn = '%s-%d.png' % (basename(outname), fb[1])
            if fn not in meta:
                d = meta[fn] = {}
            else:
                d = meta[fn]

            # fb[6] contain the filename
            if use_path:
                # use the path with separators replaced by _
                # example '../data/tiles/green_grass.png' becomes
                # 'data_tiles_green_grass'
                uid = splitext(fb[6])[0]
                # remove leading dots and slashes
                uid = uid.lstrip('./\\')
                # replace remaining slashes with _
                uid = uid.replace('/', '_').replace('\\', '_')
            else:
                # for example, '../data/tiles/green_grass.png'
                # just get only 'green_grass' as the uniq id.
                uid = splitext(basename(fb[6]))[0]

            x, y, w, h = fb[2:6]
            d[uid] = x, size_h - y - h, w, h

        outfn = '%s.atlas' % outname
        with open(outfn, 'w') as fd:
            json.dump(meta, fd)

        return outfn, meta


if __name__ == '__main__':
    """ Main line program. Process command line arguments
    to make a new atlas. """

    import sys
    from glob import glob
    argv = sys.argv[1:]
    # earlier import of kivy has already called getopt to remove kivy system
    # arguments from this line. That is all arguments up to the first '--'
    if len(argv) < 3:
        print('Usage: python -m kivy.atlas [-- [--use-path] '
              '[--padding=2]] <outname> '
              '<size|512x256> <img1.png> [<img2.png>, ...]')
        sys.exit(1)

    options = {'use_path': False}
    while True:
        option = argv[0]
        if option == '--use-path':
            options['use_path'] = True
        elif option.startswith('--padding='):
            options['padding'] = int(option.split('=', 1)[-1])
        elif option[:2] == '--':
            print('Unknown option {}'.format(option))
            sys.exit(1)
        else:
            break
        argv = argv[1:]

    outname = argv[0]
    try:
        if 'x' in argv[1]:
            size = list(map(int, argv[1].split('x', 1)))
        else:
            size = int(argv[1])
    except ValueError:
        print('Error: size must be an integer or <integer>x<integer>')
        sys.exit(1)

    filenames = [fname for fnames in argv[2:] for fname in glob(fnames)]
    ret = Atlas.create(outname, filenames, size, **options)
    if not ret:
        print('Error while creating atlas!')
        sys.exit(1)

    fn, meta = ret
    print('Atlas created at', fn)
    print('%d image%s been created' % (len(meta),
          's have' if len(meta) > 1 else ' has'))
