__all__ = ('LineWidth', 'Color', 'BindTexture')

from instructions cimport ContextInstruction


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
            self.set_state('color', args)
        elif vec_size == 3:
            self.set_state('color', [args[0], args[1], args[2], 1.0])
        else:
            self.set_state('color', [1.0, 1.0, 1.0, 1.0])

    property rgba:
        def __get__(self):
            return self.context_state['color']
        def __set__(self, rgba):
            self.set_state('color', rgba)
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
    def __init__(self, *args):
        ContextInstruction.__init__(self)
        if args:
            self.set_state('texture0', args[0])
        else:
            self.set_state('texture0', 0)

    property texture:
        def __get__(self):
            return self.context_state['tetxure0']
        def __set__(self, object texture):
            self.set_state('texture0', texture)


"""
cdef class PushMatrix(ContextInstruction):
    '''PushMatrix on context's matrix stack
    '''
    cdef apply(self):
        self.context.get('mvm').push()

cdef class PopMatrix(ContextInstruction):
    '''Pop Matrix from context's matrix stack onto model view
    '''
    cdef apply(self):
        self.context.get('mvm').pop()


cdef class MatrixInstruction(ContextInstruction):
    '''Base class for Matrix Instruction on canvas
    '''

    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self)

    cdef apply(self):
        '''Apply matrix to the matrix of this instance to the
        context model view matrix
        '''
        self.context.get('mvm').apply(self.mat)

    property matrix:
        ''' Matrix property. Numpy matrix from transformation module
        setting the matrix using this porperty when a change is made
        is important, becasue it will notify the context about the update
        '''
        def __get__(self):
            return self.mat
        def __set__(self, mat):
            self.mat = mat
            self.context.post_update()

cdef class Transform(MatrixInstruction):
    '''Transform class.  A matrix instruction class which
    has function to modify the transformation matrix
    '''
    cpdef transform(self, object trans):
        '''Multiply the instructions matrix by trans
        '''
        self.mat = matrix_multiply(self.mat, trans)

    cpdef translate(self, float tx, float ty, float tz):
        '''Translate the instrcutions transformation by tx, ty, tz
        '''
        self.transform( translation_matrix(tx, ty, tz) )

    cpdef rotate(self, float angle, float ax, float ay, float az):
        '''Rotate the transformation by matrix by angle degress around the
        axis defined by the vector ax, ay, az
        '''
        self.transform( rotation_matrix(angle, [ax, ay, az]) )

    cpdef scale(self, float s):
        '''Applies a uniform scaling of s to the matrix transformation
        '''
        self.transform( scale_matrix(s, s, s) )

    cpdef identity(self):
        '''Resets the transformation to the identity matrix
        '''
        self.matrix = identity_matrix()



cdef class Rotate(Transform):
    '''Rotate the coordinate space by applying a rotation transformation
    on the modelview matrix. You can set the properties of the instructions
    afterwards with e.g. ::

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
        self._angle = angle
        self._axis = (ax, ay, az)
        self.matrix = rotation_matrix(self._angle, self._axis)

    property angle:
        def __get__(self):
            return self._angle
        def __set__(self, a):
            self.set(a, *self._axis)

    property axis:
        def __get__(self):
            return self._axis
        def __set__(self, axis):
           self.set(self._angle, *axis)


cdef class Scale(Transform):
    '''Instruction to perform a uniform scale transformation
    '''
    def __init__(self, *args):
        Transform.__init__(self)
        if len(args) == 1:
            self.s = args[0]
            self.matrix = scale_matrix(self.s)

    property scale:
        '''Sets the scale factor for the transformation
        '''
        def __get__(self):
            return self.s
        def __set__(self, s):
            self.s = s
            self.matrix = scale_matrix(s)


cdef class  Translate(Transform):
    '''Instruction to create a translation of the model view coordinate space
    '''
    def __init__(self, *args):
        Transform.__init__(self)
        if len(args) == 3:
            self.matrix = translation_matrix(args)

    def set_translate(self, x, y, z):
        self.matrix = translation_matrix([x,y,z])

    property x:
        '''Sets the translation on the x axis
        '''
        def __get__(self):
            return self._x
        def __set__(self, float x):
            self.set_translate(x, self._y, self._z)

    property y:
        '''Sets the translation on the y axis
        '''
        def __get__(self):
            return self._y
        def __set__(self, float y):
            self.set_translate(self._x, y, self._z)

    property z:
        '''Sets the translation on the z axis
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
"""
