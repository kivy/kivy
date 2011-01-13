'''
SVG: Squirtle SVG image loader
'''

__all__ = ('SvgLoaderSquirtle', )

from kivy.logger import Logger
from kivy.core.svg import SvgBase, SvgLoader
from kivy.lib import squirtle


class SvgSquirtle(SvgBase):
    '''Svg loader based on squirtle library'''

    @staticmethod
    def extensions():
        '''Return accepted extension for this loader'''
        return ('svg', )

    def load(self, filename):
        '''loads a squirtle svg object from teh filename'''
        Logger.debug('SVG: Load <%s>' % filename)
        try:
            svg = squirtle.SVG(filename)
        except:
            Logger.warning('SVG: Unable to load SVG file <%s>' %
                                     filename)
            raise
        return svg

    def draw(self):
        self.svg_data.draw(0, 0)

# register
SvgLoader.register(SvgSquirtle)

