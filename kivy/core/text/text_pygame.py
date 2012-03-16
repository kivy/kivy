'''
Text Pygame: Draw text with pygame
'''

__all__ = ('LabelPygame', )

from . import LabelBase
from kivy.core.image import ImageData

try:
    import pygame
except:
    raise

pygame_cache = {}
pygame_cache_order = []

# init pygame font
pygame.font.init()


class LabelPygame(LabelBase):

    def _get_font_id(self):
        return '|'.join([unicode(self.options[x]) for x \
            in ('font_size', 'font_name_r', 'bold', 'italic')])

    def _get_font(self):
        fontid = self._get_font_id()
        if fontid not in pygame_cache:
            # try first the file if it's a filename
            fontobject = None
            fontname = self.options['font_name_r']
            ext = fontname.split('.')[-1]
            if ext.lower() == 'ttf':
                # fontobject
                fontobject = pygame.font.Font(fontname,
                                int(self.options['font_size'] * 1.333))

            # fallback to search a system font
            if fontobject is None:
                # try to search the font
                font = pygame.font.match_font(
                    self.options['font_name_r'].replace(' ', ''),
                    bold=self.options['bold'],
                    italic=self.options['italic'])

                # fontobject
                fontobject = pygame.font.Font(font,
                                int(self.options['font_size'] * 1.333))
            pygame_cache[fontid] = fontobject
            pygame_cache_order.append(fontid)

        # to prevent too much file open, limit the number of opened fonts to 64
        while len(pygame_cache_order) > 64:
            popid = pygame_cache_order.pop(0)
            del pygame_cache[popid]

        return pygame_cache[fontid]

    def get_extents(self, text):
        return self._get_font().size(text)

    def _render_begin(self):
        self._pygame_surface = pygame.Surface(self._size, pygame.SRCALPHA, 32)
        self._pygame_surface.fill((0, 0, 0, 0))

    def _render_text(self, text, x, y):
        font = self._get_font()
        color = [c * 255 for c in self.options['color']]
        color[0], color[2] = color[2], color[0]
        try:
            text = font.render(text, True, color)
            self._pygame_surface.blit(text, (x, y), None, pygame.BLEND_RGBA_ADD)
        except pygame.error:
            pass

    def _render_end(self):
        w, h = self._size
        data = ImageData(w, h,
            'rgba', self._pygame_surface.get_buffer().raw)

        del self._pygame_surface

        return data
