'''
Pygame text renderer
====================

'''

__all__ = ('LabelRendererPygame', )

from . import LabelRendererBase
from kivy.core.image import ImageData
import pygame

pygame_cache = {}
pygame_cache_order = []

# init pygame font
pygame.font.init()


class LabelRendererPygame(LabelRendererBase):

    renderer_type = 'texture'

    def _get_font_id(self):
        options = self.label.options
        return '|'.join([unicode(options[x]) for x \
            in ('font_size', 'font_name', 'bold', 'italic')])

    def _get_font(self):
        options = self.label.options
        fontid = self._get_font_id()
        if fontid not in pygame_cache:
            # try first the file if it's a filename
            fontobject = None
            fontname = options['font_name']
            ext = fontname.split('.')[-1]
            if ext.lower() == 'ttf':
                # fontobject
                fontobject = pygame.font.Font(fontname,
                                int(options['font_size'] * 1.333))

            # fallback to search a system font
            if fontobject is None:
                # try to search the font
                font = pygame.font.match_font(
                    options['font_name'].replace(' ', ''),
                    bold=options['bold'],
                    italic=options['italic'])

                # fontobject
                fontobject = pygame.font.Font(font,
                                int(options['font_size'] * 1.333))
            pygame_cache[fontid] = fontobject
            pygame_cache_order.append(fontid)

        # to prevent too much file open, limit the number of opened fonts to 64
        while len(pygame_cache_order) > 64:
            popid = pygame_cache_order.pop(0)
            del pygame_cache[popid]

        return pygame_cache[fontid]

    def get_extents(self, text):
        font = self._get_font()
        w, h = font.size(text)
        return w, h

    def render_begin(self, width, height):
        self._size = (width, height)
        self._pygame_surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        self._pygame_surface.fill((0, 0, 0, 0))

    def render_text(self, text, x, y):
        font = self._get_font()
        try:
            text = font.render(text, 1, (255, 255, 255))
            self._pygame_surface.blit(text, (x, y), None, pygame.BLEND_RGBA_ADD)
        except pygame.error:
            pass

    def render_end(self):
        width, height = self._size
        data = ImageData(width, height,
            'rgba', self._pygame_surface.get_buffer().raw)
        del self._pygame_surface
        return data

# auto register renderer
LabelRendererBase.register('pygame', LabelRendererPygame)

