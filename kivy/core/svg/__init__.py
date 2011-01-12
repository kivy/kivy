'''
SVG
===

Abstraction to load SVG data.
'''

__all__ = ('Svg',)

from kivy.core import core_register_libs
from kivy.cache import Cache

Cache.register('kivy.svg', limit=50)

class SvgBase(object):
    '''Base to implement an svg loader.'''

    __slots__ = ('filename', )

    def __init__(self, filename, **kwargs):
        self.filename = filename

        self.svg_data = Cache.get('kivy.svg', filename)
        if not self.svg_data:
            new_svg = self.load(filename)
            Cache.append('kivy.svg', filename, new_svg)
            self.svg_data = new_svg

    def load(self, filename):
        '''Load an svg'''
        raise NotImplementedError("abstract class SvgLoaderBase: subclass must be implemented by svg provider")

    def __getattr__(self, name):
        return self.svg_data.__getattribute__(name)

class SvgLoader(object):
    __slots__ = ('loaders')
    loaders = []

    @staticmethod
    def register(subcls):
        SvgLoader.loaders.append(subcls)

    @staticmethod
    def load(filename, **kwargs):
        # extract extensions
        ext = filename.split('.')[-1].lower()
        im = None
        for loader in SvgLoader.loaders:
            if ext not in loader.extensions():
                continue
            im = loader(filename, **kwargs)
            break
        if im is None:
            raise Exception('Unsupported extension <%s>, no loader found.' % ext)
        return im

class Svg(object):
    '''Load and draw an SVG file.

    :Parameters:
        `filename`: str
            Path to the svg that should be loaded.
        `keep_data`: bool, default to False
            Keep the raw svg data when the display list is created
        `scale`: float, default to 1.0
            Scale of the svg
        `anchor_x`: float, default to 0
            X anchor (x coordinate based on original width, which will be at x pos and used as center for scaling)
        `anchor_y`: float, default to 0
            Y anchor (y coordinate based on original height, which will be at y pos and used as center for scaling)
    '''

    @staticmethod
    def load(filename, **kwargs):
        '''Load an Svg file

        :Parameters:
            `filename`: str
                Filename of the image
        '''
        return Svg(filename, **kwargs)

    def __init__(self, arg, **kwargs):
        kwargs.setdefault('keep_data', False)

        super(Svg, self).__init__(**kwargs)

        self._scale_x   = 1.
        self._scale_y   = 1.
        self._filename  = None
        self.svg_object = None
        self.scale      = 1.
        self.anchor_x   = 0
        self.anchor_y   = 0

        #this actually loads the svg
        if isinstance(arg, basestring):
            self.filename   = arg
        else:
            raise Exception('Unable to load image with type %s' % str(type(arg)))

        # after loading, let the user take the place
        if 'scale' in kwargs:
            self.scale      = kwargs.get('scale')
        if 'anchor_x' in kwargs:
            self.anchor_x   = kwargs.get('anchor_x')
        if 'anchor_y' in kwargs:
            self.anchor_y   = kwargs.get('anchor_y')
        if 'pos' in kwargs:
            self.x, self.y  = kwargs.get('pos')
        if 'x' in kwargs:
            self.x = kwargs.get('x')
        if 'y' in kwargs:
            self.y = kwargs.get('y')

    def _get_original_width(self):
        return self.svg_object.width
    original_width = property(_get_original_width)

    def _get_original_height(self):
        return self.svg_object.height
    original_height = property(_get_original_height)

    def _get_original_size(self):
        return (self.original_width, self.original_width)
    original_height = property(_get_original_height)

    def _get_width(self):
        return self._scale_x*self.original_width
    def _set_width(self, w):
        if self.width != w: #nothing to do
            self._scale_x = w/float(self.original_width)
    width = property(_get_width, _set_width)

    def _get_height(self):
        return self._scale_y*self.original_height
    def _set_height(self, h):
        if self.height != h: #nothing to do
            self._scale_y = h/float(self.original_height)
    height = property(_get_height, _set_height)

    def _get_size(self):
        return (self.width, self.height)
    def _set_size(self, size):
        self.width = size[0]
        self.height = size[1]
    size = property(_get_size, _set_size)

    def _get_filename(self):
        return self._filename
    def _set_filename(self, value):
        if value is None:
            return
        if value == self._filename:
            return
        self._filename = value
        self.svg_object = SvgLoader.load(self._filename)
    filename = property(_get_filename, _set_filename,
            doc='Get/set the filename of svg')

    def _get_scale(self):
        return self._scale_x
    def _set_scale(self, s):
        self._scale_x = s
        self._scale_y = s
    scale = property(_get_scale, _set_scale)


def load(filename):
    '''Load an image'''
    return Svg.load(filename)


# load image loaders
core_register_libs('svg', (
    ('squirtle', 'svg_squirtle'),
))
