'''
VBO text renderer
=================

This renderer is using other texture renderer for creating its own texture cache
with all glyphs needed, and create mesh for the text.

'''

from . import LabelRendererBase
from kivy.graphics import SizedInstructionGroup

from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle, Mesh
from kivy.core.text import Label as CoreLabel
from kivy.resources import resource_find
from kivy.cache import Cache

font_name = resource_find('data/fonts/DroidSans.ttf')
ctable = [unichr(i) for i in xrange(1024)]

Cache.register('kv.textmesh', limit=100)


class Glyph(object):

    __slots__ = ('c', 'w', 'h', 'tx', 'ty', 'tu', 'tv')

    def __init__(self, c, w, h):
        self.c = c
        self.w = w
        self.h = h


class LabelRendererMesh(LabelRendererBase):

    renderer_type = 'mesh'

    def __init__(self, **kwargs):
        super(LabelRendererMesh, self).__init__(**kwargs)

        # get a texture renderer
        self.renderer = None
        for r in LabelRendererBase.renderers.itervalues():
            if r.renderer_type == 'texture':
                self.renderer = r
                break
        if self.renderer:
            self.renderer = self.renderer(**kwargs)

    def get_extents(self, text):
        return self.renderer.get_extents(text)

    def validate(self, text):
        if self.renderer is not None:
            return False
        # remove duplicated chars and check in the ctable
        x = [x in ctable for x in set(text)]
        return False in x

    def render_begin(self, width, height):
        self.size = [width, height]
        self.mesh = []
        self.vertices = []
        self.indices = []
        self.setup_font()

    def render_text(self, text, x, y):
        g = self.gtable
        v = self.vertices
        i = self.indices
        for c in text:
            glyph = g[c]
            w = glyph.w
            h = glyph.h
            tx = glyph.tx
            ty = glyph.ty
            tu = glyph.tu
            tv = glyph.tv
            ii = len(v) / 4
            v += [
                x, y, tx, tv,
                x + w, y, tu, tv,
                x + w, y + h, tu, ty,
                x, y + h, tx, ty]
            i += [
                ii, ii + 1, ii + 2,
                ii + 2, ii + 3, ii]
            x += glyph.w
            if len(self.indices) > 65535 - 6:
                self.push_mesh()
                v = self.vertices
                i = self.indices

    def render_end(self):
        self.push_mesh()
        data = SizedInstructionGroup(size=self.size)
        for mesh in self.mesh:
            data.add(mesh)
        return data

    def push_mesh(self):
        if not len(self.vertices):
            return
        self.mesh.append(Mesh(
            vertices=self.vertices, indices=self.indices,
            mode='triangles', texture=self.texture))
        self.vertices = []
        self.indices = []

    def next_power_of_2(self, v):
        v -= 1
        v |= v >> 1
        v |= v >> 2
        v |= v >> 4
        v |= v >> 8
        v |= v >> 16
        return v + 1

    def setup_font(self):
        fontid = self.label.fontid
        result = Cache.get('kv.textmesh', fontid)
        if result is None:
            self.render_font()
            Cache.append('kv.textmesh', fontid, (self.gtable, self.texture))
        else:
            self.gtable, self.texture = result

    def render_font(self):

        # create texture of a set of characters
        self.gtable = gtable = {}
        r = self.renderer
        mh = tx = ty = 0

        for c in ctable:
            w, h = r.get_extents(c)
            # minimum maximum width that can be done with a texture.
            if tx + w > 1024:
                tx = w
                ty += mh
                mh = h
            else:
                tx += w
                if h > mh:
                    mh = h
            gtable[c] = Glyph(c, w, h)

        if ty == 0:
            ty = mh

        # determine the size of the texture
        tw = 1024
        th = self.next_power_of_2(ty)
        print 'texture size can be something near', (tw, th), ty

        # prepare texture
        self.texture = Texture.create(size=(tw, th), colorfmt='rgba')
        self.texture.flip_vertical()

        # use corelabel for rendering on our texture
        mh = tx = ty = 0
        for c in ctable:
            glyph = gtable[c]
            if glyph.w == 0:
                continue

            # precache u/v size.
            w = glyph.w
            h = glyph.h
            glyph.tx = tx / float(self.texture.width)
            glyph.ty = ty / float(self.texture.height)
            glyph.tu = (tx + glyph.w) / float(self.texture.width)
            glyph.tv = (ty + glyph.h) / float(self.texture.height)

            r.render_begin(w, h)
            r.render_text(glyph.c, 0, 0)
            data = r.render_end()
            self.texture.blit_data(data, pos=(tx, ty))

            # minimum maximum width that can be done with a texture.
            if tx + w > self.texture.width:
                tx = 0
                ty += mh
                mh = h
            else:
                tx += w
                if h > mh:
                    mh = h

LabelRendererBase.register('mesh', LabelRendererMesh)

'''
class TestWidget(Widget):
    texture = ObjectProperty(None, allownone=True)
    mesh = ObjectProperty(None, allownone=True)
    text = StringProperty('')
    def __init__(self, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super(TestWidget, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_text, 0)

    def update_graphics(self):
        self.canvas.clear()
        self.canvas.add(Color(1, 1, 1))
        if self.mesh:
            for mesh in self.mesh:
                self.canvas.add(mesh)
        else:
            self.canvas.add(Rectangle(
                pos=self.pos, size=self.size, texture=self.texture))

    def update_text(self, dt):
        self.text = ('Lorem ipsum[' + str((
            Clock.get_fps(), Clock.get_rfps(), dt
        )) + '], ') * 50

    def on_text(self, instance, text):
        if 1:
            vcl = VBOCoreLabel(text=text, text_size=(1024, None),
                    font_name=font_name)
            vcl.refresh()
            self.size = vcl.size
            self.mesh = vcl._mesh
            self.texture = None
        else:
            vcl = CoreLabel(text=text, text_size=(1024, None),
                    font_name=font_name)
            vcl.refresh()
            self.size = vcl.size
            self.texture = vcl.texture
            self.mesh = None
        self.update_graphics()
'''
