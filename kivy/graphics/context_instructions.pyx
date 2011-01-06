#cython: embedsignature=True

'''
Context instructions
====================

The context instructions represent non graphics elements like:
    - Matrix manipulation
    - Color manipulation
    - Texture binding

'''

__all__ = ('LineWidth', 'Color', 'BindTexture', 'PushMatrix', 'PopMatrix',
           'Rotate', 'Scale', 'Translate', 'MatrixInstruction')

from instructions cimport *
from transformation cimport *

from kivy.resources import resource_find
from kivy.core.image import Image
from kivy.logger import Logger

from os.path import join
from kivy import kivy_shader_dir
cdef object DEFAULT_TEXTURE
cdef object get_default_texture():
    global DEFAULT_TEXTURE
    if not DEFAULT_TEXTURE:
        DEFAULT_TEXTURE = Image(join(kivy_shader_dir, 'default.png')).texture
    return DEFAULT_TEXTURE


cdef class LineWidth(ContextInstruction):
    '''Instruction to set the line width of the drawing context
    '''
    def __init__(self, *args):
        ContextInstruction.__init__(self)
        if args:
            self.linewidth = args[0]
        else:
            self.linewidth = 2.0

    property linewidth:
        def __get__(self):
            return self.context_state['linewidth']
        def __set__(self, lw):
            self.set_state('linewidth', lw)


cdef class Color(ContextInstruction):
    '''Instruction to set the color state for any vetices being drawn after it
    '''
    def __init__(self, *args):
        ContextInstruction.__init__(self)
        cdef int vec_size = len(args)
        if vec_size == 4:
            self.rgba = args
        elif vec_size == 3:
            self.rgb = args
        else:
            self.set_state('color', [1.0, 1.0, 1.0, 1.0])

    property rgba:
        def __get__(self):
            return self.context_state['color']
        def __set__(self, rgba):
            self.set_state('color', map(float,rgba))
    property rgb:
        def __get__(self):
            return self.rgba[:-1]
        def __set__(self, rgb):
            self.rgba = (rgb[0], rgb[1], rgb[2], 1.0)
    property r:
        def __get__(self):
            return self.rgba[0]
        def __set__(self, r):
            self.rgba = [r, self.g, self.b, self.a]
    property g:
        def __get__(self):
            return self.rgba[1]
        def __set__(self, g):
            self.rgba = [self.r, g, self.b, self.a]
    property b:
        def __get__(self):
            return self.rgba[2]
        def __set__(self, b):
            self.rgba = [self.r, self.g, b, self.a]
    property a:
        def __get__(self):
            return self.rgba[3]
        def __set__(self, a):
            self.rgba = [self.r, self.g, self.b, a]





cdef class BindTexture(ContextInstruction):
    '''BindTexture Graphic instruction.
    The BindTexture Instruction will bind a texture and enable
    GL_TEXTURE_2D for subsequent drawing.

    :Parameters:
        `texture`: Texture
            specifies the texture to bind to the given index
    '''
    def __init__(self, **kwargs):
        ContextInstruction.__init__(self)
        if 'source' in kwargs and 'texture' in kwargs:
            Logger.warn("BindTexture:  both source and texture   \
                         specified in kwargs! settign source will \
                         will overwrite texture property")

        self.source = kwargs.get('source', None)
        if self.source == None:
            Logger.warn("setting texture")
            self.texture = kwargs.get('texture', None)

        Logger.warn("done %s" % kwargs)
        Logger.warn("done nitializing texture binding %s, %s", self.source, self.texture)

    cdef apply(self):

        #Logger.trace('BindTexture: binding <%s> %s' % (str(self.texture), self.texture.target))
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self._texture.target, self._texture.id)

    property texture:
        def __get__(self):
            return self._texture
        def __set__(self, object texture):
            if not texture:
                texture = get_default_texture()
            self._texture = texture

    property source:
        '''Set/get the source (filename) to load for texture.
        '''
        def __get__(self):
            return self._source
        def __set__(self, bytes filename):
            #if not filename:
            #    self._source = None
            #    self.texture = None
            Logger.trace('BindTexture: setting source: <%s>' % filename)
            self._source = resource_find(filename)
            if self._source:
                self.texture = Image(self._source).texture
            else:
                self.texture = None


cdef double radians(double degrees):
    return degrees * (3.14159265 / 180.)

cdef class PushMatrix(ContextInstruction):
    '''PushMatrix on context's matrix stack
    '''
    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self)
        self.context_push = ['modelview_mat']

cdef class PopMatrix(ContextInstruction):
    '''Pop Matrix from context's matrix stack onto model view
    '''
    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self)
        self.context_pop = ['modelview_mat']


cdef class MatrixInstruction(ContextInstruction):
    '''Base class for Matrix Instruction on canvas
    '''

    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self)

    cdef apply(self):
        '''Apply the matrix of this instance to the
        context model view matrix
        '''
        cdef RenderContext context = self.get_context()
        cdef Matrix mvm
        mvm = context.get_state('modelview_mat')
        context.set_state('modelview_mat', matrix_multiply(self.matrix, mvm))

    property matrix:
        ''' Matrix property. Matrix from transformation module
        setting the matrix using this porperty when a change is made
        is important, becasue it will notify the context about the update
        '''
        def __get__(self):
            return self.matrix
        def __set__(self, x):
            self.matrix = x
            self.flag_update()

cdef class Transform(MatrixInstruction):
    '''Transform class.  A matrix instruction class which
    has function to modify the transformation matrix
    '''
    cpdef transform(self, Matrix trans):
        '''Multiply the instructions matrix by trans
        '''
        self.matrix = matrix_multiply(self.matrix, trans)

    cpdef translate(self, float tx, float ty, float tz):
        '''Translate the instrcutions transformation by tx, ty, tz
        '''
        self.transform( matrix_translation(tx, ty, tz) )

    cpdef rotate(self, float angle, float ax, float ay, float az):
        '''Rotate the transformation by matrix by angle degress around the
        axis defined by the vector ax, ay, az
        '''
        self.transform( matrix_rotation(angle, ax, ay, az) )

    cpdef scale(self, float s):
        '''Applies a uniform scaling of s to the matrix transformation
        '''
        self.transform( matrix_scale(s, s, s) )

    cpdef identity(self):
        '''Resets the transformation to the identity matrix
        '''
        self.matrix = matrix_identity()



cdef class Rotate(Transform):
    '''Rotate the coordinate space by applying a rotation transformation
    on the modelview matrix. You can set the properties of the instructions
    afterwards with e.g.::

        rot.angle = 90
        rot.axis = (0,0,1)
    '''

    def __init__(self, *args):
        Transform.__init__(self)
        if len(args) == 4:
            self.set(args[0], args[1], args[2], args[3])
        else:
            self.set(0, 0, 0, 1)

    def set(self, float angle, float ax, float ay, float az):
        '''Set the angle and axis of rotation

        >>> rotationobject.set(90, 0, 0, 1)
        '''
        self._angle = radians(angle)
        self._axis = (ax, ay, az)
        self.matrix = matrix_rotation(self._angle, ax, ay, az)

    property angle:
        '''Property for getting/settings the angle of the rotation
        '''
        def __get__(self):
            return self._angle
        def __set__(self, a):
            self.set(a, *self._axis)

    property axis:
        '''Property for getting/settings the axis of the rotation

        The format of the axis is (x, y, z).
        '''
        def __get__(self):
            return self._axis
        def __set__(self, axis):
           self.set(self._angle, *axis)


cdef class Scale(Transform):
    '''Instruction to perform a uniform scale transformation
    '''
    def __init__(self, *args):
        cdef double s
        Transform.__init__(self)
        if len(args) == 1:
            self.s = s = args[0]
            self.matrix = matrix_scale(s, s, s)

    property scale:
        '''Property for getting/setting the scale.

        The same scale value is applied on all axis.
        '''
        def __get__(self):
            return self.s
        def __set__(self, s):
            self.s = s
            self.matrix = matrix_scale(s, s, s)


cdef class Translate(Transform):
    '''Instruction to create a translation of the model view coordinate space
    '''
    def __init__(self, *args):
        cdef double x, y, z
        Transform.__init__(self)
        if len(args) == 3:
            x, y, z = args
            self.matrix = matrix_translation(x, y, z)

    def set_translate(self, x, y, z):
        self.matrix = matrix_translation(x, y, z)

    property x:
        '''Property for getting/setting the translation on X axis
        '''
        def __get__(self):
            return self._x
        def __set__(self, float x):
            self.set_translate(x, self._y, self._z)

    property y:
        '''Property for getting/setting the translation on Y axis
        '''
        def __get__(self):
            return self._y
        def __set__(self, float y):
            self.set_translate(self._x, y, self._z)

    property z:
        '''Property for getting/setting the translation on Z axis
        '''
        def __get__(self):
            return self._z
        def __set__(self, float z):
            self.set_translate(self._x, self._y, z)

    property xy:
        '''2 tuple with translation vector in 2D for x and y axis
        '''
        def __get__(self):
            return self._x, self._y
        def __set__(self, c):
            self.set_translate(c[0], c[1], self._z)

    property xyz:
        '''3 tuple translation vector in 3D in x, y, and z axis
        '''
        def __get__(self):
            return self._x, self._y, self._z
        def __set__(self, c):
            self.set_translate(c[0], c[1], c[2])

