#-*- coding: utf-8 -*-
#
#    this program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    this program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#   The Graphics Interchange Format(c) is the Copyright property of
#   CompuServe Incorporated. GIF(sm) is a Service Mark property of
#   CompuServe Incorporated.
#
# The unisys/lzw patent has expired, yes. If anyone puts another patent
# over this code, you must *burn* this file.

'''pygif: gif implementation in python

http://www.java2s.com/Open-Source/Python/Network/\
        emesene/emesene-1.6.2/pygif/pygif.py.htm'''


#TODO issues to fix
#optimize for speed  #partially done#  a lot of room for improvement
import struct
from array import array

KNOWN_FORMATS = ('GIF87a', 'GIF89a')

from kivy.compat import PY2
from kivy.logger import Logger
from kivy.core.image import ImageLoaderBase, ImageData, ImageLoader

Debug = False


class ImageLoaderGIF(ImageLoaderBase):
    '''Image loader for gif'''

    @staticmethod
    def extensions():
        '''Return accepted extension for this loader'''
        return ('gif', )

    def load(self, filename):
        try:
            try:
                im = GifDecoder(open(filename, 'rb').read())
            except UnicodeEncodeError:
                if PY2:
                    im = GifDecoder(open(filename.encode('utf8'), 'rb').read())
        except:
            Logger.warning('Image: Unable to load Image <%s>' % filename)
            raise

        if Debug:
            print(im.print_info())
        img_data = []
        ls_width = im.ls_width
        ls_height = im.ls_height
        im_images = im.images
        im_palette = im.palette
        pixel_map = array('B', [0] * (ls_width * ls_height * 4))
        for img in im_images:
            palette = img.palette if img.local_color_table_flag\
                else im_palette
            have_transparent_color = img.has_transparent_color
            transparent_color = img.transparent_color
            #draw_method_restore_previous =  1 \
            #    if img.draw_method == 'restore previous' else 0
            draw_method_replace = 1 \
                if ((img.draw_method == 'replace') or
                    (img.draw_method == 'restore background')) else 0
            pixels = img.pixels
            img_height = img.height
            img_width = img.width
            left = img.left
            top = img.top
            if img_height > ls_height or img_width > ls_width or\
                top > ls_height or left > ls_width:
                Logger.warning('Image_GIF: decoding error on frame <%s>' %
                        len(img_data))
                img_height = ls_height
                img_width = ls_width
                left = top = 0
            #reverse top to bottom and left to right
            tmp_top = (ls_height - (img_height + top))
            img_width_plus_left = (img_width + left)
            ls_width_multiply_4 = ls_width * 4
            left_multiply_4 = left * 4
            img_data_append = img_data.append
            while img_height > 0:
                i = left
                img_height -= 1
                x = (img_height * img_width) - left
                rgba_pos = (tmp_top * ls_width_multiply_4) + (left_multiply_4)
                tmp_top += 1
                while i < img_width_plus_left:
                    #this should now display corrupted gif's
                    #instead of crashing on gif's not decoded properly
                    try:
                        (r, g, b) = palette[pixels[x + i]]
                    except:
                        rgba_pos += 4
                        i += 1
                        continue
                    # when not magic pink
                    if (r, g, b) != (255, 0, 255):
                        if have_transparent_color:
                            if transparent_color == pixels[x + i]:
                                if draw_method_replace:
                                    #transparent pixel draw method replace
                                    pixel_map[rgba_pos + 3] = 0
                                    rgba_pos += 4
                                    i += 1
                                    continue
                                #transparent pixel draw method combine
                                rgba_pos += 4
                                i += 1
                                continue
                           # this pixel isn't transparent
                        #doesn't have transparent color
                        (pixel_map[rgba_pos], pixel_map[rgba_pos + 1],
                                pixel_map[rgba_pos + 2]) = (r, g, b)
                        pixel_map[rgba_pos + 3] = 255
                    # if magic pink move to next pixel
                    rgba_pos += 4
                    i += 1

            if PY2:
                img_data_append(ImageData(ls_width, ls_height,
                    'rgba', pixel_map.tostring(), flip_vertical=False))
            else:
                img_data_append(ImageData(ls_width, ls_height,
                    'rgba', pixel_map.tobytes(), flip_vertical=False))

            if draw_method_replace:
                pixel_map = array('B', [0] * (ls_width * ls_height * 4))

        self.filename = filename

        return img_data


class Gif(object):
    '''Base class to decoder'''

    # struct format strings

    #17,18:
    FMT_HEADER = '<6sHHBBB'
    #20:
    FMT_IMGDESC = '<HHHHB'

    IMAGE_SEPARATOR = 0x2C
    EXTENSION_INTRODUCER = 0x21
    GIF_TRAILER = 0x3b

    LABEL_GRAPHIC_CONTROL = 0xF9
    LABEL_COMMENT = 0xFE
    LABEL_PLAINTEXT = 0x01

    FMT_EXT_GRAPHIC_CONTROL = '<BBHB'  # 89a

    def __init__(self, data, debug):
        self.data = data
        self.pointer = 0

        # default data for an empty file
        self.header = 'GIF87a'
        self.ls_width = 0
        self.ls_height = 0
        self.flags = 0
        self.color_resolution = 0
        self.sort_flag = 0
        self.color_table_flag = 0
        self.global_color_table_size = 0
        self.background_color = 0
        self.aspect_ratio = 0
        # greyscale palette by default
        self.palette = [(x, x, x) for x in range(0, 256)]
        self.images = []

        self.debug_enabled = False
        return

    def pop(self, data, length=1):
        '''gets the next $len chars from the data stack import
        and increment the pointer'''

        start = self.pointer
        end = self.pointer + length
        self.pointer += length

        return data[start:end]

    def pops(self, format, data):
        '''pop struct: get size, pop(), unpack()'''
        size = struct.calcsize(format)
        return struct.unpack(format, self.pop(data, size))

    def print_info(self):
        '''prints out some useful info (..debug?)'''

        print("Version: %s" % self.header)
        print("Logical screen width: %d" % self.ls_width)
        print("Logical screen height: %d" % self.ls_height)
        print("Flags: %s" % repr(self.flags))
        print(" " * 6, "Color resolution: %d" % self.color_resolution)
        print(" " * 6, "Sort flag: %r" % self.sort_flag)
        print(" " * 6, "Global color table flag: %r" % self.color_table_flag)
        print(" " * 22, "...size: %d (%d bytes)" %
              (self.global_color_table_size, self.global_color_table_size * 3))
        print("Background color: %d" % self.background_color)
        print("Aspect ratio info: %d" % self.aspect_ratio)

    def new_image(self, header=None):
        '''adds a new image descriptor'''
        image = ImageDescriptor(self, header)
        self.images.append(image)
        return image


class ImageDescriptor(object):
    '''A class that represents a single image'''

    def __init__(self, parent, header=None):

        self.parent = parent
        # this will be set when needed
        self.codesize = 0

        # compressed output codes
        self.lzwcode = ''

        # uncompressed pixels (decoded)
        self.pixels = []

        # we assume a "fullscreen" image
        self.left = self.top = 0
        self.width = parent.ls_width
        self.height = parent.ls_height

        # yes, these default flags work...
        self.flags = [False for x in range(8)]
        self.local_color_table_flag = False
        self.interlace_flag = False
        self.sort_flag = False
        self.local_color_table_size = 0
        self.draw_method = 'replace'
        self.transparent_color = -1
        self.has_transparent_color = 0
        self.palette = []

        if header:
            self.setup_header(header)

    def setup_header(self, header):
        '''takes a header tuple and fills the attributes'''

        self.left = header[0]
        self.top = header[1]
        self.width = header[2]
        self.height = header[3]

        self.flags = get_bits(header[4])
        self.local_color_table_flag = self.flags[7]
        self.interlace_flag = self.flags[6]
        self.sort_flag = self.flags[5]
        #-- flags 4 and 3 are reserved
        self.local_color_table_size = 2 ** (pack_bits(self.flags[:3]) + 1)
        if self.local_color_table_flag:
            if Debug:
                print('local color table true')
            self.palette = self.parent.get_color_table(
                self.local_color_table_size * 3)

    def get_header(self):
        '''builds a header dynamically'''
        flags = [False for x in range(8)]
        flags[7] = self.local_color_table_flag
        flags[6] = self.interlace_flag
        flags[5] = self.sort_flag

        # useless!
        flags[2], flags[1], flags[0] = get_bits(len(self.palette), bits=3)

        return (self.left, self.top, self.width, self.height, pack_bits(flags))

    header = property(fget=get_header)


class GifDecoder(Gif):
    '''decodes a gif file into.. something.. else..'''

    def __init__(self, data, debug=False):
        Gif.__init__(self, data, debug)
        self.fill()

    def fill(self):
        '''reads the data and fills each field of the file'''

        # start reading from the beggining of the file
        self.pointer = 0

        #17. Header.
        #18. Logical Screen Descriptor.
        data = self.pops(Gif.FMT_HEADER, self.data)

        self.header = data[0]
        self.ls_width = data[1]
        self.ls_height = data[2]
        self.background_color = data[4]
        self.aspect_ratio = data[5]

        # flags field
        self.flags = get_bits(data[3])
        #1 bit
        self.color_table_flag = self.flags[7]
        self.sort_flag = self.flags[3]
        #3 bit
        self.color_resolution = pack_bits(self.flags[4:7])  # 7 not included
        #3 bit
        self.global_color_table_size = 2 ** (pack_bits(self.flags[:3]) + 1)

        #19. Global Color Table.
        if self.color_table_flag:
            size = (self.global_color_table_size) * 3
            self.palette = self.get_color_table(size)
        else:
            # generate a greyscale palette
            self.palette = [(x, x, x) for x in range(256)]

        # blocks
        image = None
        self_data = self.data
        self_pops = self.pops
        Gif_IMAGE_SEPARATOR = Gif.IMAGE_SEPARATOR
        Gif_FMT_IMGDESC = Gif.FMT_IMGDESC
        self_new_image = self.new_image
        self_pop = self.pop
        self_debug_enabled = self.debug_enabled
        self_lzw_decode = self.lzw_decode
        Gif_EXTENSION_INTRODUCER = Gif.EXTENSION_INTRODUCER
        Gif_GIF_TRAILER = Gif.GIF_TRAILER
        Gif_LABEL_GRAPHIC_CONTROL = Gif.LABEL_GRAPHIC_CONTROL
        trans_color = 0
        has_transparent_color = 0
        drw_method = 'replace'
        while True:
            try:
                nextbyte = self_pops('<B', self_data)[0]
            except:
                nextbyte = 0x3b  # force end

            #20. Image Descriptor
            if nextbyte == Gif_IMAGE_SEPARATOR:
                descriptor = self_pops(Gif_FMT_IMGDESC, self_data)
                image = self_new_image(descriptor)
                image.transparent_color = trans_color
                image.has_transparent_color = has_transparent_color
                image.draw_method = drw_method
                image.codesize = self_pops('<B', self_data)[0]
                image.lzwcode = b''
                image_lzwcode = image.lzwcode
                ###TODO too many corner casses for gifs:(
                table_size = image.local_color_table_size\
                    if image.local_color_table_flag and \
                    self.global_color_table_size < image.local_color_table_size\
                    else self.global_color_table_size

                while True:
                    try:
                        blocksize = self_pops('<B', self_data)[0]
                    except:
                        break
                    if blocksize == 0:
                        break   # no more image data
                    lzwdata = self_pop(self_data, blocksize)
                    image_lzwcode = b''.join((image_lzwcode, lzwdata))

                if self_debug_enabled:
                    print('LZW length:', len(image_lzwcode))

                image.lzwcode = image_lzwcode
                image.pixels = self_lzw_decode(image.lzwcode, image.codesize,
                        table_size)

            # Extensions
            elif nextbyte == Gif_EXTENSION_INTRODUCER:
                pass
            # Gif trailer
            elif nextbyte == Gif_GIF_TRAILER:
                return
            elif nextbyte == Gif_LABEL_GRAPHIC_CONTROL:
                nextbyte = self_pops('<B', self_data)[0]
                drw_bits = (get_bits(self_pops('<B', self_data)[0]))
                has_transparent_color = drw_bits[0]
                if drw_bits[2:5] == array('B', [0, 0, 1]):
                    drw_method = 'replace'
                elif (drw_bits[2:5]) == array('B', [0, 1, 0]):
                    drw_method = 'restore background'
                else:
                    drw_method = 'restore previous'
                nextbyte = self_pops('<B', self_data)[0]
                nextbyte = self_pops('<B', self_data)[0]
                nextbyte = self_pops('<B', self_data)[0]
                trans_color = nextbyte
                pass
            # "No Idea What Is This"
            else:
                pass

    def string_to_bits(self, string):
        '''high level string unpacker'''
        ordarray = array('B', string)
        bits = array('B')
        bits_append = bits.append
        _get_bits = get_bits
        for byte in ordarray:
            list(map(bits_append, _get_bits(byte)))
        return bits

    def readable(bool_list):
        '''Converts a list of booleans to a readable list of ints
        Useful for debug only'''
        return [int(x) for x in bool_list]

    def bits_to_int(self, bits):
        '''high level bit list packer'''
        c = 1
        i = 0
        for bit in bits:
            if bit:
                i += 2 ** (c - 1)
            c += 1
        return i

    def get_color_table(self, size):
        '''Returns a color table in the format [(r,g,b),(r,g,b), ...]'''

        raw_color_table = self.pops("<%dB" % size, self.data)
        pos = 0
        palette = []
        palette_append = palette.append

        while pos + 3 < (size + 1):
            red = raw_color_table[pos]
            green = raw_color_table[pos + 1]
            blue = raw_color_table[pos + 2]
            palette_append((red, green, blue))
            pos += 3
        return palette

    def lzw_decode(self, input, initial_codesize, color_table_size):
        '''Decodes a lzw stream from input import
        Returns list of ints (pixel values)'''
        string_table = {}
        output = array('B')
        output_append = output.append
        output_extend = output.extend
        old = ''
        index = 0

        bits = self.string_to_bits(input)
        self.bitpointer = 0

        codesize = initial_codesize + 1
        clearcode, end_of_info = color_table_size, color_table_size + 1

        if Debug:
            print('codesize: %d' % codesize)
            print('clearcode %d, end_of_info: %d' % (clearcode, end_of_info))

        def pop(size, _bits):
            ''' return bits '''
            start = self.bitpointer
            end = self.bitpointer = start + size
            return _bits[start: end]

        def clear():
            '''Called on clear code'''
            string_table.clear()
            for index in range(color_table_size):
                string_table[index] = chr(index)
            index = end_of_info + 1
            return index

        index = clear()
        # skip first (clear)code
        bits = bits[codesize:]
        # read first code, append to output
        self_bits_to_int = self.bits_to_int

        code = self_bits_to_int(pop(codesize, bits))
        if code in string_table:
            output_append(ord(string_table[code]))
        else:
            Logger.warning('Image_GIF: decoding error on code '
                '<%d> aode size <%d>' % (code, codesize))
            string_table[code] = string_table[0]
            output_append(ord(string_table[code]))
        old = string_table[code]
        bitlen = len(bits)

        while self.bitpointer < bitlen:
            # read next code
            code = self_bits_to_int(pop(codesize, bits))

            # special code?
            if code == clearcode:
                index = clear()
                codesize = initial_codesize + 1
                code = self_bits_to_int(pop(codesize, bits))
                if code in string_table:
                    output_append(ord(string_table[code]))
                else:
                    Logger.warning('Image_GIF: decoding error on code '
                        '<%d> aode size <%d>' % (code, codesize))
                    string_table[code] = string_table[0]
                    output_append(ord(string_table[code]))
                old = string_table[code]
                continue

            elif code == end_of_info:
                break

            # code in stringtable?
            if code in string_table:
                c = string_table[code]
                string_table[index] = ''.join((old, c[0]))
            else:
                c = ''.join((old, old[0]))
                string_table[code] = c

            index += 1
            old = c
            output_extend(list(map(ord, c)))

            if index == 2 ** codesize:
                codesize += 1
                if codesize == 13:
                    codesize = 12

        if self.debug_enabled:
            print('Output stream len: %d' % len(output))
        return output


def get_bits(flags, reverse=False, bits=8):
    '''return a list with $bits items, one for each enabled bit'''

    mybits = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048)[:bits]

    rev_num = 1
    if reverse:
        rev_num = -1
    ret = array('B')
    ret_append = ret.append
    for bit in mybits[::rev_num]:
        ret_append(flags & bit != 0)
    return ret


def pack_bits(bits):
    '''convert a bit (bool or int) tuple into a int'''
    packed = 0
    level = 0
    for bit in bits:
        if bit:
            packed += 2 ** level
        level += 1
    return packed

# register
ImageLoader.register(ImageLoaderGIF)
