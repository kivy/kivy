'''
Atlas
=====

Atlas is a class that can be used to pack multiple images into one.
'''

import json
from os.path import basename, dirname, join, splitext
from kivy.event import EventDispatcher
from kivy.logger import Logger
from kivy.properties import AliasProperty, DictProperty

CoreImage = None

class Atlas(EventDispatcher):

    textures = DictProperty({})

    def _get_filename(self):
        return self._filename

    filename = AliasProperty(_get_filename, None)

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

        Logger.debug('Atlas: Load <%s>' % filename)
        with open(filename, 'r') as fd:
            meta = json.load(fd)

        Logger.debug('Atlas: Need to load %d images' % len(meta))
        d = dirname(filename)
        textures = {}
        for subfilename, ids in meta.iteritems():
            subfilename = join(d, subfilename)
            Logger.debug('Atlas: Load <%s>' % subfilename)

            # load the image
            ci = CoreImage(subfilename)

            # for all the uid, load the image, get the region, and put it in our
            # dict.
            for meta_id, meta_coords in ids.iteritems():
                x, y, w, h = meta_coords
                textures[meta_id] = ci.texture.get_region(*meta_coords)

        self.textures = textures

    @staticmethod
    def create(outname, filenames, size):
        '''This method can be used to create manually an atlas from a set of
        images.

        Thanks to
        http://omnisaurusgames.com/2011/06/texture-atlas-generation-using-python/
        for its initial implementation.
        '''
        import Image

        # open all of the images
        ims = [(f, Image.open(f)) for f in filenames]

        # sort by image area
        ims = sorted(ims, key=lambda im : im[1].size[0]*im[1].size[1], reverse=True)

        # free boxes are empty space in our output image set
        # the freebox tuple format is: outidx, x, y, w, h
        freeboxes = [(0, 0, 0, size, size)]
        numoutimages = 1
        padding = 1

        # full boxes are areas where we have placed images in the atlas
        # the full box tuple format is: image, outidx, x, y, w, h, filename
        fullboxes = []

        # do the actual atlasing by sticking the largest images we can have into
        # the smallest valid free boxes
        for imageinfo in ims:
            im = imageinfo[1]
            imw, imh = im.size
            imw += padding
            imh += padding
            if imw > size or imh > size:
                Logger.error('Atlas: image %s is larger than the atlas size!'%\
                    imageinfo[0])
                return

            inserted = False
            while not inserted:
                for idx, fb in enumerate(freeboxes):
                    # find the smallest free box that will contain this image
                    if fb[3] >= imw and fb[4] >= imh:
                        # we found a valid spot! Remove the current freebox, and
                        # split the leftover space into (up to) two new
                        # freeboxes
                        del freeboxes[idx]
                        if fb[3] > imw:
                            freeboxes.append( (fb[0], fb[1]+imw, fb[2],
                                fb[3]-imw, imh) )

                        if fb[4] > imh:
                            freeboxes.append( (fb[0], fb[1], fb[2]+imh,
                                fb[3], fb[4] - imh) )

                        # keep this sorted!
                        freeboxes = sorted(freeboxes, key = lambda fb : fb[3]*fb[4])
                        fullboxes.append( (im, fb[0], fb[1] + padding, fb[2] +
                            padding, imw - padding, imh - padding, imageinfo[0]))
                        inserted = True
                        break

                if not inserted:
                    # oh crap - there isn't room in any of our free boxes, so we
                    # have to add a new output image
                    freeboxes.append((numoutimages, 0, 0, size, size))
                    numoutimages += 1

        # now that we've figured out where everything goes, make the output
        # images and blit the source images to the approriate locations
        Logger.info('Atlas: create an {0}x{0} rgba image'.format(size))
        outimages = [Image.new("RGBA", (int(size),int(size))) for i in range(0, int(numoutimages))]
        for fb in fullboxes:
            outimages[fb[1]].paste(fb[0], (fb[2], fb[3]))

        # save the output images
        for idx, outimage in enumerate(outimages):
            outimage.save('%s-%d.png' % (outname, idx))

        # write out an xml file that says where everything ended up
        meta = {}
        for fb in fullboxes:
            fn = '%s-%d.png' % (basename(outname), fb[1])
            if fn not in meta:
                d = meta[fn] = {}
            else:
                d = meta[fn]

            # fb[6] contain the filename aka '../apok.png'. just get only 'apok'
            # as the uniq id.
            uid = splitext(basename(fb[6]))[0]
            x, y, w, h = fb[2:6]
            d[uid] = x, size-y-h, w, h
            #xmlfile.write('\t<image name="{0}" file="{1}-{2}.png" x="{3}" y ="{4}" w="{5}" h="{6}" />\n'.format(fb[6],outname, fb[1], fb[2], fb[3], fb[4], fb[5] ))

        #xmlfile.write("</images>\n")
        #print ("It all fit into " + str(numoutimages) + " images!")
        outfn = '%s.atlas' % outname
        with open(outfn, 'w') as fd:
            json.dump(meta, fd)

        return outfn, meta

if __name__ == '__main__':

    import sys
    print sys.argv
    argv = sys.argv[1:]
    if len(argv) < 3:
        print 'Usage: python -m kivy.atlas <outname> <size> <img1.png>' \
              '[<img2.png>, ...]'
        sys.exit(1)

    outname = argv[0]
    try:
        size = int(argv[1])
    except ValueError:
        print 'Error: size must be an integer'
        sys.exit(1)

    filenames = argv[2:]
    ret = Atlas.create(outname, filenames, size)
    if not ret:
        print 'Error while creating atlas!'
        sys.exit(1)

    fn, meta = ret
    print 'Atlas created at', fn
    print '%d image%s have been created' % (len(meta),
            's' if len(meta) > 1 else '')
    with open(fn) as fd:
        print fd.read()

    # try to reread it
    a = Atlas(fn)
