'''
Obj: handle 3D mesh from the OBJ format file.

OBJ is a geometry definition file, adopted by many vendor graphics.
To known more about the format, check http://en.wikipedia.org/wiki/Obj
'''

__all__ = ('OBJ', 'Material', 'MaterialGroup', 'Mesh')

import os
from kivy.logger import Logger
from kivy.core.image import Image
from OpenGL.GL import GL_FRONT_AND_BACK, GL_DIFFUSE, GL_AMBIENT, GL_SPECULAR, \
        GL_SHININESS, GL_AMBIENT_AND_DIFFUSE, GL_COLOR_MATERIAL, GLfloat, \
        GL_BACK, GL_CULL_FACE, GL_CLIENT_VERTEX_ARRAY_BIT, GL_EMISSION, \
        GL_CURRENT_BIT, GL_ENABLE_BIT, GL_LIGHTING_BIT, GL_COMPILE, \
        GL_T2F_N3F_V3F, GL_TRIANGLES, GL_LIGHT0, GL_LIGHTING, GL_DEPTH_TEST, \
        GL_LIGHT_MODEL_LOCAL_VIEWER, GL_LIGHT_MODEL_AMBIENT, GL_REPEAT, \
        glEnable, glDisable, glPushClientAttrib, glPushAttrib, \
        glPopClientAttrib, glPopAttrib, glInterleavedArrays, glDrawArrays, \
        glNewList, glEndList, glCullFace, glMaterialfv, glColorMaterial, \
        glCallList, glGenLists, glMaterialf, glLightfv, glLightModelfv, \
        glColor3f

class Material(object):
    '''
    Material class to handle attribute like light (ambient, diffuse, specular,
    emmission, shininess), opacity, texture...
    '''
    diffuse = [.8, .8, .8]
    ambient = [.2, .2, .2]
    specular = [0., 0., 0.]
    emission = [0., 0., 0.]
    shininess = 0.
    opacity = 1.
    texture = None

    def __init__(self, name):
        self.name = name

    def apply(self, face=GL_FRONT_AND_BACK):
        '''Apply the material on current context'''
        if self.texture:
            self.texture.enable()
            self.texture.bind()
            glEnable(GL_COLOR_MATERIAL)

        glMaterialfv(face, GL_DIFFUSE, self.diffuse + [self.opacity])
        glMaterialfv(face, GL_AMBIENT, self.ambient + [self.opacity])
        glMaterialfv(face, GL_SPECULAR, self.specular + [self.opacity])
        glMaterialfv(face, GL_EMISSION, self.emission + [self.opacity])
        glMaterialf(face, GL_SHININESS, self.shininess)
        glColorMaterial(face, GL_AMBIENT_AND_DIFFUSE)

    def unapply(self):
        if self.texture:
            self.texture.disable()
            glDisable(GL_COLOR_MATERIAL)

class MaterialGroup(object):
    '''
    Groups of material
    '''
    def __init__(self, material):
        self.material = material

        # Interleaved array of floats in GL_T2F_N3F_V3F format
        self.vertices = []
        self.array = None

class Mesh(object):
    '''
    Class to store a mesh in T2F_N3F_V3F format.
    '''
    def __init__(self, name):
        self.name = name
        self.groups = []

        # Display list, created only if compile() is called, but used
        # automatically by draw()
        self.list = None

    def draw(self):
        '''Draw the mesh on screen (using display list if compiled)'''
        if self.list:
            glCallList(self.list)
            return

        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT | GL_LIGHTING_BIT)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        for group in self.groups:
            if group.material:
                group.material.apply()
            if group.array is None:
                if group.material and group.material.texture:
                    if group.material.texture.rectangle:
                        # texture is a rectangle texture
                        # that's mean we need to adjust the range of texture
                        # coordinate from original 0-1 to 0-width/0-height
                        group.vertices[0::8] = map(
                            lambda x: x * group.material.texture.width,
                            group.vertices[0::8]
                        )
                        group.vertices[1::8] = map(
                            lambda x: x * group.material.texture.height,
                            group.vertices[1::8]
                        )
                group.array = (GLfloat * len(group.vertices))(*group.vertices)
                group.triangles = len(group.vertices) / 8
            glInterleavedArrays(GL_T2F_N3F_V3F, 0, group.array)
            glDrawArrays(GL_TRIANGLES, 0, group.triangles)
            if group.material:
                group.material.unapply()
        glPopAttrib()
        glPopClientAttrib()

    def compile(self):
        '''Compile the mesh in display list'''
        if self.list:
            return
        gllist = glGenLists(1)
        glNewList(gllist, GL_COMPILE)
        self.draw()
        glEndList()
        self.list = gllist


class OBJ:
    '''3D object representation.

    :Parameters:
        `filename` : string
            Filename of object
        `file` : File object, default to None
            Use file instead of filename if possible
        `path` : string, default to None
            Use custom path for material
        `compat` : bool, default to True
            Set to False if you want to take care yourself of the lights, depth
            test, color...
    '''
    def __init__(self, filename, file=None, path=None, compat=True):
        self.materials = {}
        self.meshes = {}        # Name mapping
        self.mesh_list = []     # Also includes anonymous meshes
        self.compat = compat

        if file is None:
            file = open(filename, 'r')

        if path is None:
            path = os.path.dirname(filename)
            self.path = path

        mesh = None
        group = None
        material = None

        vertices = [[0., 0., 0.]]
        normals = [[0., 0., 0.]]
        tex_coords = [[0., 0.]]

        for line in open(filename, 'r'):
            if line.startswith('#'):
                continue
            values = line.split()
            if not values:
                continue

            if values[0] == 'v':
                vertices.append(map(float, values[1:4]))
            elif values[0] == 'vn':
                normals.append(map(float, values[1:4]))
            elif values[0] == 'vt':
                tex_coords.append(map(float, values[1:3]))
            elif values[0] == 'mtllib':
                self.load_material_library(values[1])
            elif values[0] in ('usemtl', 'usemat'):
                material = self.materials.get(values[1], None)
                if material is None:
                    Logger.warning('OBJ: Unknown material: %s' % values[1])
                if mesh is not None:
                    group = MaterialGroup(material)
                    mesh.groups.append(group)
            elif values[0] == 'o':
                mesh = Mesh(values[1])
                self.meshes[mesh.name] = mesh
                self.mesh_list.append(mesh)
                group = None
            elif values[0] == 'f':
                if mesh is None:
                    mesh = Mesh('')
                    self.mesh_list.append(mesh)
                if material is None:
                    material = Material('')
                if group is None:
                    group = MaterialGroup(material)
                    mesh.groups.append(group)

                # For fan triangulation, remember first and latest vertices
                v1 = None
                vlast = None
                for i, v in enumerate(values[1:]):
                    v_index, t_index, n_index = \
                        (map(int, [j or 0 for j in v.split('/')]) + [0, 0])[:3]
                    if v_index < 0:
                        v_index += len(vertices) - 1
                    if t_index < 0:
                        t_index += len(tex_coords) - 1
                    if n_index < 0:
                        n_index += len(normals) - 1
                    vertex = tex_coords[t_index] + \
                            normals[n_index] + \
                            vertices[v_index]

                    if i >= 3:
                        # Triangulate
                        group.vertices += v1 + vlast
                    group.vertices += vertex

                    if i == 0:
                        v1 = vertex
                    vlast = vertex

    def open_material_file(self, filename):
        '''Override for loading from archive/network etc.'''
        return open(os.path.join(self.path, filename), 'r')

    def load_material_library(self, filename):
        material = None
        file = self.open_material_file(filename)

        for line in file:
            if line.startswith('#'):
                continue
            values = line.split()
            if not values:
                continue

            if values[0] == 'newmtl':
                material = Material(values[1])
                self.materials[material.name] = material
            elif material is None:
                Logger.warning('OBJ: Expected "newmtl" in %s' % filename)
                continue

            try:
                if values[0] == 'Kd':
                    material.diffuse = map(float, values[1:])
                elif values[0] == 'Ka':
                    material.ambient = map(float, values[1:])
                elif values[0] == 'Ks':
                    material.specular = map(float, values[1:])
                elif values[0] == 'Ke':
                    material.emission = map(float, values[1:])
                elif values[0] == 'Ns':
                    material.shininess = float(values[1])
                elif values[0] == 'd':
                    material.opacity = float(values[1])
                elif values[0] == 'map_Kd':
                    try:
                        filename = ' '.join(values[1:])
                        material.texture = Image(filename).texture
                        material.texture.wrap = GL_REPEAT
                    except:
                        Logger.warning('OBJ: Could not load texture %s' % values[1])
                        raise
            except:
                Logger.warning('OBJ: Parse error in %s.' % filename)
                raise

    def enter(self):
        if not self.compat:
            return
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0, 0, 0, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (.8, .8, .8, 1))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (.9, .9, .9))
        glLightModelfv(GL_LIGHT_MODEL_LOCAL_VIEWER, 0)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)
        glColor3f(1, 1, 1)

    def leave(self):
        if not self.compat:
            return
        glDisable(GL_LIGHTING)
        glDisable(GL_LIGHT0)
        glDisable(GL_COLOR_MATERIAL)
        glDisable(GL_DEPTH_TEST)

    def draw(self):
        '''Draw the object on screen'''
        self.enter()
        for mesh in self.mesh_list:
            mesh.draw()
        self.leave()

