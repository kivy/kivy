from c_opengl cimport *

from os.path import join
from kivy import kivy_shader_dir
from kivy.logger import Logger
from kivy.core.image import Image



cdef object DEFAULT_TEXTURE
cdef object get_default_texture():
    global DEFAULT_TEXTURE
    if not DEFAULT_TEXTURE:
        DEFAULT_TEXTURE = Image(join(kivy_shader_dir, 'default.png')).texture
    return DEFAULT_TEXTURE


cdef class TextureManager:

    def __init__(self):
        self.free_texture_units = []
        self.texture_units = dict()
        self.textures = dict()
        self.reset()

    cdef int bind_texture(self, object texture):
        cdef tex_unit = 0
        #if binding None or 0, return texture unit of default texture
        if texture == None or texture == 0:
            return tex_unit
        #if its already bound, nothing to do
        tex_unit = self.textures.get(texture, -1)
        if tex_unit != -1:
            return tex_unit
        # texture not bound yet, so bind it to a new unit
        if self.free_texture_units:
            tex_unit = self.free_texture_units.pop()
        else:
            tex_unit = len(self.textures)

        #if weve reached max number of texture units, fallback to switching
        #TODO: make this use the least recent used texture
        if tex_unit == GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS:
            tex_unit = 1
            old_texture = self.texture_units[tex_unit]
            del self.textures[old_texture]

        #actually bind teh texture to teh correct texture unit
        glActiveTexture(GL_TEXTURE0 + tex_unit)
        glBindTexture(texture.target, texture.id)
        self.textures[texture] = tex_unit
        self.texture_units[tex_unit] = texture
        #return the texture unit we bound the texture to
        Logger.trace("TextureManager: binding texture on unit %d."%tex_unit)
        return tex_unit

    cdef release_texture(self, object texture):
        #warn if texture to release isnt actualy bound
        if not texture in self.textures:
            Logger.warn("TextureManager: trying to release unbound texture!")
            return
        #unbind teh texture, and mark the texture unit as freed
        cdef int tex_unit = self.textures[texture]
        self.free_texture_units.append(tex_unit)
        glActiveTexture(GL_TEXTURE0 + tex_unit)
        glBindTexture(texture.target, 0)
        del self.texture_units[tex_unit]
        del self.textures[texture]

    cdef bind_all(self):
        #Logger.trace("TextureManager: rebinding %d textures"%len(self.textures))
        #rebind all teh textures on the correct texture unit
        for unit, texture in self.texture_units.iteritems():
            glActiveTexture(GL_TEXTURE0 + unit)
            glBindTexture(texture.target, texture.id)
            
    cdef release_all(self):
        Logger.trace("TextureManager: releasing %d textures"%len(self.textures))
        for texture in self.texture_units.itervalues():
            self.release_texture(texture)

    cdef reset(self):
        Logger.trace("TextureManager: reseting TextureManager")
        self.release_all()
        self.free_texture_units = []
        self.textures = dict()
        tex0 = Image(join(kivy_shader_dir, 'default.png')).texture
        self.bind_texture(tex0)

