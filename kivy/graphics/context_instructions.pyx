'''
Context instructions
====================

The context instructions represent non graphics elements like:

* Matrix manipulation (PushMatrix, PopMatrix, Rotate, Translate, Scale,
  MatrixInstruction)
* Color manipulation (Color)
* Texture binding (BindTexture)

.. versionchanged:: 1.0.8
    LineWidth instruction have been removed. It wasn't working before, and we
    actually no implementation working. We need to do more experimentation to
    get it right. Check the bug `#207
    <https://github.com/kivy/kivy/issues/207>`_ for more informations.

'''

__all__ = ('Color', 'BindTexture', 'PushMatrix', 'PopMatrix',
           'Rotate', 'Scale', 'Translate', 'MatrixInstruction',
           'gl_init_resources')

from instructions cimport *
from transformation cimport *

from kivy.cache import Cache
from kivy.resources import resource_find
from kivy.core.image import Image
from kivy.logger import Logger

from os.path import join
from kivy import kivy_shader_dir

cdef object DEFAULT_TEXTURE = None
cdef object get_default_texture():
    global DEFAULT_TEXTURE
    if not DEFAULT_TEXTURE:
        DEFAULT_TEXTURE = Image(join(kivy_shader_dir, 'default.png')).texture
    return DEFAULT_TEXTURE

# register Image cache
Cache.register('kv.texture', limit=1000, timeout=60)
Cache.register('kv.shader', limit=1000, timeout=60)

# ensure that our resources are cleaned
def gl_init_resources():
    global DEFAULT_TEXTURE
    DEFAULT_TEXTURE = None
    Cache.remove('kv.texture')
    Cache.remove('kv.shader')
    reset_gl_context()

# Taken from colorsys module, and optimized for cython
# HSV: Hue, Saturation, Value
# H: position in the spectrum
# S: color saturation ("purity")
# V: color brightness

cdef inline float max3(float a, float b, float c):
    if a > b:
        return a if a > c else c
    return b if b > c else c

cdef inline float min3(float a, float b, float c):
    if a < b:
        return a if a < c else c
    return b if b < c else c

cdef tuple rgb_to_hsv(float r, float g, float b):
    cdef float h
    cdef float maxc = max3(r, g, b)
    cdef float minc = min3(r, g, b)
    cdef float v = maxc
    if minc == maxc: return 0.0, 0.0, v
    cdef float s = (maxc-minc) / maxc
    cdef float rc = (maxc-r) / (maxc-minc)
    cdef float gc = (maxc-g) / (maxc-minc)
    cdef float bc = (maxc-b) / (maxc-minc)
    if r == maxc: h = bc-gc
    elif g == maxc: h = 2.0+rc-bc
    else: h = 4.0+gc-rc
    h = (h/6.0) % 1.0
    return h, s, v

cdef tuple hsv_to_rgb(float h, float s, float v):
    if s == 0.0: return v, v, v
    cdef int i = int(h*6.0) # XXX assume int() truncates!
    cdef float f = (h*6.0) - i
    cdef float p = v*(1.0 - s)
    cdef float q = v*(1.0 - s*f)
    cdef float t = v*(1.0 - s*(1.0-f))
    i = i%6
    if i == 0: return v, t, p
    if i == 1: return q, v, p
    if i == 2: return p, v, t
    if i == 3: return p, q, v
    if i == 4: return t, p, v
    if i == 5: return v, p, q
    # Cannot get here


cdef class Color(ContextInstruction):
    '''Instruction to set the color state for any vertices being drawn after it.
    All the values passed are between 0 and 1, not 0 and 255.

    In Python, you can do::

        from kivy.graphics import Color

        # create red color
        c = Color(1, 0, 0)
        # create blue color
        c = Color(0, 1, 0)
        # create blue color with 50% alpha
        c = Color(0, 1, 0, .5)

        # using hsv mode
        c = Color(0, 1, 1, mode='hsv')
        # using hsv mode + alpha
        c = Color(0, 1, 1, .2, mode='hsv')

    In kv lang::

        <Rule>:
            canvas:
                # red color
                Color:
                    rgb: 1, 0, 0
                # blue color
                Color:
                    rgb: 0, 1, 0
                # blue color with 50% alpha
                Color:
                    rgba: 0, 1, 0, .5

                # using hsv mode
                Color:
                    hsv: 0, 1, 1

                # using hsv mode + alpha
                Color:
                    hsv: 0, 1, 1
                    a: .5

    '''
    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        cdef int vec_size = len(args)
        if kwargs.get('mode', '') == 'hsv':
            if vec_size == 4:
                self.hsv = args[:3]
                self.a = args[3]
            elif vec_size == 3:
                self.hsv = args
            else:
                self.set_state('color', [1.0, 1.0, 1.0, 1.0])
        else:
            if vec_size == 4:
                self.rgba = args
            elif vec_size == 3:
                self.rgb = args
            else:
                self.set_state('color', [1.0, 1.0, 1.0, 1.0])

    property rgba:
        '''RGBA color, list of 4 values in 0-1 range
        '''
        def __get__(self):
            return self.context_state['color']
        def __set__(self, rgba):
            self.set_state('color', map(float,rgba))
    property rgb:
        '''RGB color, list of 3 values in 0-1 range, alpha will be 1.
        '''
        def __get__(self):
            return self.rgba[:-1]
        def __set__(self, rgb):
            self.rgba = (rgb[0], rgb[1], rgb[2], 1.0)
    property r:
        '''Red component, between 0-1
        '''
        def __get__(self):
            return self.rgba[0]
        def __set__(self, r):
            self.rgba = [r, self.g, self.b, self.a]
    property g:
        '''Green component, between 0-1
        '''
        def __get__(self):
            return self.rgba[1]
        def __set__(self, g):
            self.rgba = [self.r, g, self.b, self.a]
    property b:
        '''Blue component, between 0-1
        '''
        def __get__(self):
            return self.rgba[2]
        def __set__(self, b):
            self.rgba = [self.r, self.g, b, self.a]
    property a:
        '''Alpha component, between 0-1
        '''
        def __get__(self):
            return self.rgba[3]
        def __set__(self, a):
            self.rgba = [self.r, self.g, self.b, a]
    property hsv:
        '''HSV color, list of 3 values in 0-1 range, alpha will be 1.
        '''
        def __get__(self):
            return rgb_to_hsv(self.r, self.g, self.b)
        def __set__(self, x):
            self.rgb = hsv_to_rgb(x[0], x[1], x[2])
    property h:
        '''Hue component, between 0-1
        '''
        def __get__(self):
            return self.hsv[0]
        def __set__(self, x):
            self.hsv = [x, self.s, self.v]
    property s:
        '''Saturation component, between 0-1
        '''
        def __get__(self):
            return self.hsv[1]
        def __set__(self, x):
            self.hsv = [self.h, x, self.v]
    property v:
        '''Value component, between 0-1
        '''
        def __get__(self):
            return self.hsv[2]
        def __set__(self, x):
            self.hsv = [self.h, self.s, x]


cdef class BindTexture(ContextInstruction):
    '''BindTexture Graphic instruction.
    The BindTexture Instruction will bind a texture and enable
    GL_TEXTURE_2D for subsequent drawing.

    :Parameters:
        `texture`: Texture
            specifies the texture to bind to the given index
    '''
    def __init__(self, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        if 'source' in kwargs and 'texture' in kwargs:
            Logger.warn('BindTexture: both source and texture specified '
                        'in kwargs! Settings source will overwrite'
                        'texture property')

        self.source = kwargs.get('source', None)
        if self.source is None:
            self.texture = kwargs.get('texture', None)

        self.index = kwargs.get('index', 0)

    cdef void apply(self):
        cdef RenderContext context = self.get_context()
        context.set_texture(self._index, self._texture)

    property texture:
        def __get__(self):
            return self._texture
        def __set__(self, object texture):
            if not texture:
                texture = get_default_texture()
            self._texture = texture

    property index:
        def __get__(self):
            return self._index
        def __set__(self, int index):
            if self._index == index:
                return
            self._index = index
            self.flag_update()

    property source:
        '''Set/get the source (filename) to load for texture.
        '''
        def __get__(self):
            return self._source
        def __set__(self, bytes filename):
            Logger.trace('BindTexture: setting source: <%s>' % filename)
            self._source = <bytes>resource_find(filename)
            if self._source:
                tex = Cache.get('kv.texture', filename)
                if not tex:
                    tex = Image(self._source).texture
                    Cache.append('kv.texture', filename, tex)
                self.texture = tex
            else:
                self.texture = None


cdef double radians(double degrees):
    return degrees * (3.14159265 / 180.)

cdef class PushMatrix(ContextInstruction):
    '''PushMatrix on context's matrix stack
    '''
    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        self.context_push = ['modelview_mat']

cdef class PopMatrix(ContextInstruction):
    '''Pop Matrix from context's matrix stack onto model view
    '''
    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        self.context_pop = ['modelview_mat']


cdef class MatrixInstruction(ContextInstruction):
    '''Base class for Matrix Instruction on canvas
    '''

    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self, **kwargs)

    cdef void apply(self):
        '''Apply the matrix of this instance to the
        context model view matrix
        '''
        cdef RenderContext context = self.get_context()
        cdef Matrix mvm
        mvm = context.get_state('modelview_mat')
        context.set_state('modelview_mat', mvm.multiply(self.matrix))

    property matrix:
        ''' Matrix property. Numpy matrix from transformation module
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
        self.matrix = self.matrix.multiply(trans)

    cpdef translate(self, float tx, float ty, float tz):
        '''Translate the instrcutions transformation by tx, ty, tz
        '''
        self.transform( Matrix().translate(tx, ty, tz) )

    cpdef rotate(self, float angle, float ax, float ay, float az):
        '''Rotate the transformation by matrix by angle degress around the
        axis defined by the vector ax, ay, az
        '''
        self.transform( Matrix().rotate(angle, ax, ay, az) )

    cpdef scale(self, float s):
        '''Applies a uniform scaling of s to the matrix transformation
        '''
        self.transform( Matrix().scale(s, s, s) )

    cpdef identity(self):
        '''Resets the transformation to the identity matrix
        '''
        self.matrix = Matrix()



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
        self._angle = angle
        self._axis = (ax, ay, az)
        self.matrix = Matrix().rotate(radians(self._angle), ax, ay, az)

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
            self.matrix = Matrix().scale(s, s, s)

    property scale:
        '''Property for getting/setting the scale.

        The same scale value is applied on all axis.
        '''
        def __get__(self):
            return self.s
        def __set__(self, s):
            self.s = s
            self.matrix = Matrix().scale(s, s, s)


cdef class Translate(Transform):
    '''Instruction to create a translation of the model view coordinate space
    '''
    def __init__(self, *args):
        cdef double x, y, z
        Transform.__init__(self)
        if len(args) == 3:
            x, y, z = args
            self.matrix = Matrix().translate(x, y, z)

    cdef set_translate(self, double x, double y, double z):
        self.matrix = Matrix().translate(x, y, z)

    property x:
        '''Property for getting/setting the translation on X axis
        '''
        def __get__(self):
            return self._x
        def __set__(self, double x):
            self.set_translate(x, self._y, self._z)

    property y:
        '''Property for getting/setting the translation on Y axis
        '''
        def __get__(self):
            return self._y
        def __set__(self, double y):
            self.set_translate(self._x, y, self._z)

    property z:
        '''Property for getting/setting the translation on Z axis
        '''
        def __get__(self):
            return self._z
        def __set__(self, double z):
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

