'''
Context instructions
====================

The context instructions represent non graphics elements such as:

* Matrix manipulations (PushMatrix, PopMatrix, Rotate, Translate, Scale,
  MatrixInstruction)
* Color manipulations (Color)
* Texture bindings (BindTexture)

.. versionchanged:: 1.0.8
    The LineWidth instruction has been removed. It wasn't working before and we
    actually have no working implementation. We need to do more experimentation
    to get it right. Check the bug
    `#207 <https://github.com/kivy/kivy/issues/207>`_ for more information.

'''

__all__ = ('Color', 'BindTexture', 'PushMatrix', 'PopMatrix',
           'Rotate', 'Scale', 'Translate', 'MatrixInstruction',
           'gl_init_resources')

from kivy.compat import PY2
from kivy.graphics.instructions cimport *
from kivy.graphics.transformation cimport *

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
Cache.register('kv.shader', limit=1000, timeout=3600)

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
    if r == maxc: h = bc - gc
    elif g == maxc: h = <float>2.0 + rc - bc
    else: h = <float>4.0 + gc - rc
    h = (h / <float>6.0) % <float>1.0
    return h, s, v

cdef tuple hsv_to_rgb(float h, float s, float v):
    if s == 0.0: return v, v, v
    cdef long i = long(h * 6.0)
    cdef float f = (h * <float>6.0) - i
    cdef float p = v * (<float>1.0 - s)
    cdef float q = v * (<float>1.0 - s * f)
    cdef float t = v * (<float>1.0 - s * (<float>1.0 - f))
    i = i % 6
    if i == 0: return v, t, p
    if i == 1: return q, v, p
    if i == 2: return p, v, t
    if i == 3: return p, q, v
    if i == 4: return t, p, v
    if i == 5: return v, p, q
    # Cannot get here


cdef class PushState(ContextInstruction):
    '''Instruction that pushes arbitrary states/uniforms onto the context
    state stack.

    .. versionadded:: 1.6.0
    '''
    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        self.context_push = list(args)

    @property
    def state(self):
        return ','.join(self.context_push)

    @state.setter
    def state(self, value):
        self.context_push = value.split(',')

    @property
    def states(self):
        return self.context_push

    @states.setter
    def states(self, value):
        self.context_push = list(value)


cdef class ChangeState(ContextInstruction):
    '''Instruction that changes the values of arbitrary states/uniforms on the
    current render context.

    .. versionadded:: 1.6.0
    '''
    def __init__(self, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        self.context_state.update(**kwargs)

    @property
    def changes(self):
        return self.context_state

    @changes.setter
    def changes(self, value):
        self.context_state = dict(value)


cdef class PopState(ContextInstruction):
    '''Instruction that pops arbitrary states/uniforms off the context
    state stack.

    .. versionadded:: 1.6.0
    '''
    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        self.context_pop = list(args)

    @property
    def state(self):
        return ','.join(self.context_pop)

    @state.setter
    def state(self, value):
        self.context_pop = value.split(',')

    @property
    def states(self):
        return self.context_pop

    @states.setter
    def states(self, value):
        self.context_pop = list(value)


cdef class Color(ContextInstruction):
    '''
    Instruction to set the color state for any vertices being
    drawn after it.

    This represents a color between 0 and 1, but is applied as a
    *multiplier* to the texture of any vertex instructions following
    it in a canvas. If no texture is set, the vertex instruction
    takes the precise color of the Color instruction.

    For instance, if a Rectangle has a texture with uniform color
    ``(0.5, 0.5, 0.5, 1.0)`` and the preceding Color has
    ``rgba=(1, 0.5, 2, 1)``, the actual visible color will be
    ``(0.5, 0.25, 1.0, 1.0)`` since the Color instruction is applied as
    a multiplier to every rgba component. In this case, a Color
    component outside the 0-1 range gives a visible result as the
    intensity of the blue component is doubled.

    To declare a Color in Python, you can do::

        from kivy.graphics import Color

        # create red v
        c = Color(1, 0, 0)
        # create blue color
        c = Color(0, 1, 0)
        # create blue color with 50% alpha
        c = Color(0, 1, 0, .5)

        # using hsv mode
        c = Color(0, 1, 1, mode='hsv')
        # using hsv mode + alpha
        c = Color(0, 1, 1, .2, mode='hsv')

    You can also set color components that are available as properties
    by passing them as keyword arguments::

        c = Color(b=0.5)  # sets the blue component only

    In kv lang you can set the color properties directly:

    .. code-block:: kv

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
        cdef long vec_size = <long>len(args)
        if kwargs.get('mode', '') == 'hsv':
            if vec_size == 4:
                self.rgba = [0, 0, 0, args[3]]
                self.hsv = args[:3]
            elif vec_size == 3:
                self.rgba = [0, 0, 0, 1.]
                self.hsv = args
            else:
                self.set_state('color', [1.0, 1.0, 1.0, 1.0])
        else:
            if vec_size == 4:
                self.rgba = args
            elif vec_size == 3:
                self.rgba = [args[0], args[1], args[2], 1.]
            else:
                self.set_state('color', [1.0, 1.0, 1.0, 1.0])

        for property_name in ['r', 'g', 'b', 'a',
                              'rgb', 'rgba', 'hsv',
                              'h', 's', 'v']:
            if property_name in kwargs:
                setattr(self, property_name, kwargs[property_name])

    @property
    def rgba(self):
        '''RGBA color, list of 4 values in 0-1 range.
        '''
        return self.context_state['color']

    @rgba.setter
    def rgba(self, rgba):
        self.set_state('color', [float(x) for x in rgba])
        self.flag_data_update()

    @property
    def rgb(self):
        '''RGB color, list of 3 values in 0-1 range. The alpha will be 1.
        '''
        return self.rgba[:-1]

    @rgb.setter
    def rgb(self, rgb):
        self.rgba = (rgb[0], rgb[1], rgb[2], self.a)

    @property
    def r(self):
        '''Red component, between 0 and 1.
        '''
        return self.rgba[0]

    @r.setter
    def r(self, r):
        self.rgba = [r, self.g, self.b, self.a]

    @property
    def g(self):
        '''Green component, between 0 and 1.
        '''
        return self.rgba[1]

    @g.setter
    def g(self, g):
        self.rgba = [self.r, g, self.b, self.a]

    @property
    def b(self):
        '''Blue component, between 0 and 1.
        '''
        return self.rgba[2]

    @b.setter
    def b(self, b):
        self.rgba = [self.r, self.g, b, self.a]

    @property
    def a(self):
        '''Alpha component, between 0 and 1.
        '''
        return self.rgba[3]

    @a.setter
    def a(self, a):
        self.rgba = [self.r, self.g, self.b, a]

    @property
    def hsv(self):
        '''HSV color, list of 3 values in 0-1 range, alpha will be 1.
        '''
        return rgb_to_hsv(self.r, self.g, self.b)

    @hsv.setter
    def hsv(self, x):
        self.rgb = hsv_to_rgb(x[0], x[1], x[2])

    @property
    def h(self):
        '''Hue component, between 0 and 1.
        '''
        return self.hsv[0]

    @h.setter
    def h(self, x):
        self.hsv = [x, self.s, self.v]

    @property
    def s(self):
        '''Saturation component, between 0 and 1.
        '''
        return self.hsv[1]

    @s.setter
    def s(self, x):
        self.hsv = [self.h, x, self.v]

    @property
    def v(self):
        '''Value component, between 0 and 1.
        '''
        return self.hsv[2]

    @v.setter
    def v(self, x):
        self.hsv = [self.h, self.s, x]


cdef class BindTexture(ContextInstruction):
    '''BindTexture Graphic instruction.
    The BindTexture Instruction will bind a texture and enable
    GL_TEXTURE_2D for subsequent drawing.

    :Parameters:
        `texture`: Texture
            Specifies the texture to bind to the given index.
    '''
    def __init__(self, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        if 'source' in kwargs and 'texture' in kwargs:
            Logger.warn('BindTexture: both source and texture specified '
                        'in kwargs! Settings source will overwrite'
                        'texture property')

        self.source = kwargs.get('source', None)
        if self.source is None and 'texture' in kwargs:
            self.texture = kwargs['texture']

        self.index = kwargs.get('index', 0)

    cdef int apply(self) except -1:
        cdef RenderContext context = self.get_context()
        context.set_texture(self._index, self._texture)

    @property
    def texture(self):
        return self._texture

    @texture.setter
    def texture(self, object texture):
        if texture is None:
            texture = get_default_texture()
        if self._texture is texture:
            return
        self._texture = texture
        self.flag_data_update()

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, int index):
        if self._index == index:
            return
        self._index = index
        self.flag_data_update()

    @property
    def source(self):
        '''Set/get the source (filename) to load for the texture.
        '''
        return self._source

    @source.setter
    def source(self, filename):
        self._source = resource_find(filename)
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


cdef class LoadIdentity(ContextInstruction):
    '''Load the identity Matrix into the matrix stack specified by
    the instructions stack property (default='modelview_mat')

    .. versionadded:: 1.6.0
    '''
    def __init__(self, **kwargs):
        self.stack = kwargs.get('stack', 'modelview_mat')

    @property
    def stack(self):
        '''Name of the matrix stack to use. Can be 'modelview_mat',
        'projection_mat' or 'frag_modelview_mat'.
        '''
        if PY2:
            return self.context_state.keys()[0]
        else:
            return list(self.context_state.keys())[0]

    @stack.setter
    def stack(self, value):
        self.context_state = {value: Matrix()}


cdef class PushMatrix(ContextInstruction):
    '''Push the matrix onto the context's matrix stack.
    '''
    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        self.stack = kwargs.get('stack', 'modelview_mat')

    @property
    def stack(self):
        '''Name of the matrix stack to use. Can be 'modelview_mat',
        'projection_mat' or 'frag_modelview_mat'.

        .. versionadded:: 1.6.0
        '''
        return self.context_push[0]

    @stack.setter
    def stack(self, value):
        value = value or 'modelview_mat'
        self.context_push = [value]


cdef class PopMatrix(ContextInstruction):
    '''Pop the matrix from the context's matrix stack onto the model view.
    '''
    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        self.stack = kwargs.get('stack', 'modelview_mat')

    @property
    def stack(self):
        '''Name of the matrix stack to use. Can be 'modelview_mat',
        'projection_mat' or 'frag_modelview_mat'.

        .. versionadded:: 1.6.0
        '''
        return self.context_push[0]

    @stack.setter
    def stack(self, value):
        value = value or 'modelview_mat'
        self.context_pop = [value]


cdef class ApplyContextMatrix(ContextInstruction):
    '''Pre-multiply the matrix at the top of the stack specified by
    `target_stack` by the matrix at the top of the 'source_stack'

    .. versionadded:: 1.6.0
    '''
    def __init__(self, **kwargs):
        self.target_stack = kwargs.get('target_stack', 'modelview_mat')
        self.source_stack = kwargs.get('source_stack', 'modelview_mat')

    cdef int apply(self) except -1:
        cdef RenderContext context = self.get_context()
        m = context.get_state(self._target_stack)
        m = m.multiply(context.get_state(self._source_stack))
        context.set_state(self._target_stack, m)

    @property
    def target_stack(self):
        '''Name of the matrix stack to use as a target.
        Can be 'modelview_mat', 'projection_mat' or 'frag_modelview_mat'.

        .. versionadded:: 1.6.0
        '''
        return self._target_stack

    @target_stack.setter
    def target_stack(self, value):
        self._target_stack = value or 'modelview_mat'

    @property
    def source_stack(self):
        '''Name of the matrix stack to use as a source.
        Can be 'modelview_mat', 'projection_mat' or 'frag_modelview_mat'.

        .. versionadded:: 1.6.0
        '''
        return self._source_stack

    @source_stack.setter
    def source_stack(self, value):
        self._source_stack = value or 'modelview_mat'


cdef class UpdateNormalMatrix(ContextInstruction):
    '''Update the normal matrix 'normal_mat' based on the current
    modelview matrix. This will compute 'normal_mat' uniform as:
    `inverse( transpose( mat3(mvm) ) )`

    .. versionadded:: 1.6.0
    '''
    cdef int apply(self) except -1:
        cdef RenderContext context = self.get_context()
        mvm = context.get_state('modelview_mat')
        context.set_state('normal_mat', mvm.normal_matrix())


cdef class MatrixInstruction(ContextInstruction):
    '''Base class for Matrix Instruction on the canvas.
    '''

    def __init__(self, *args, **kwargs):
        ContextInstruction.__init__(self, **kwargs)
        self.stack = kwargs.get('stack', 'modelview_mat')
        self._matrix = None

    cdef int apply(self) except -1:
        '''Apply the matrix of this instance to the
        context model view matrix.
        '''
        cdef RenderContext context = self.get_context()
        cdef Matrix mvm
        mvm = context.get_state(self._stack)
        context.set_state(self._stack, mvm.multiply(self.matrix))

    @property
    def matrix(self):
        ''' Matrix property. Matrix from the transformation module.
        Setting the matrix using this property when a change is made
        is important because it will notify the context about the update.
        '''
        if self._matrix == None:
            self._matrix = Matrix()
        return self._matrix

    @matrix.setter
    def matrix(self, x):
        self._matrix = x
        self.flag_data_update()

    @property
    def stack(self):
        '''Name of the matrix stack to use. Can be 'modelview_mat',
        'projection_mat' or 'frag_modelview_mat'.

        .. versionadded:: 1.6.0
        '''
        return self._stack

    @stack.setter
    def stack(self, value):
        value = value or "modelview_mat"
        self._stack = value


cdef class Transform(MatrixInstruction):
    '''Transform class. A matrix instruction class which
    modifies the transformation matrix.
    '''

    def __init__(self, *args, **kwargs):
        MatrixInstruction.__init__(self, **kwargs)

    cpdef transform(self, Matrix trans):
        '''Multiply the instructions matrix by trans.
        '''
        self.matrix = self.matrix.multiply(trans)

    cpdef translate(self, float tx, float ty, float tz):
        '''Translate the instructions transformation by tx, ty, tz.
        '''
        self.transform( Matrix().translate(tx, ty, tz) )

    cpdef rotate(self, float angle, float ax, float ay, float az):
        '''Rotate the transformation by matrix by *angle* degrees around the
        axis defined by the vector ax, ay, az.
        '''
        self.transform( Matrix().rotate(angle, ax, ay, az) )

    cpdef scale(self, float s):
        '''Applies a uniform scaling of s to the matrix transformation.
        '''
        self.transform( Matrix().scale(s, s, s) )

    cpdef identity(self):
        '''Resets the transformation to the identity matrix.
        '''
        self.matrix = Matrix()


cdef class Rotate(Transform):
    '''Rotate the coordinate space by applying a rotation transformation
    on the modelview matrix. You can set the properties of the instructions
    afterwards with e.g. ::

        rot.angle = 90
        rot.axis = (0, 0, 1)
    '''

    def __init__(self, *args, **kwargs):
        Transform.__init__(self, **kwargs)
        self._origin = (0, 0, 0)

        # compatibility mode from version < 1.7
        if len(args) == 4:
            self._angle = args[0]
            self._axis = args[1:]
        else:
            self._angle = 0
            self._axis = (0, 0, 1)

        if 'axis' in kwargs:
            self._axis = kwargs['axis']
        if 'angle' in kwargs:
            self._angle = kwargs['angle']
        if 'origin' in kwargs:
            origin = kwargs['origin']
            if len(origin) == 3:
                self._origin = tuple(origin)
            elif len(origin) == 2:
                self._origin = (origin[0], origin[1], 0.)
            else:
                raise Exception('invalid number of components in origin')

        self.compute()


    def set(self, float angle, float ax, float ay, float az):
        '''Set the angle and axis of rotation.

        >>> rotationobject.set(90, 0, 0, 1)

        .. deprecated:: 1.7.0

            The set() method doesn't use the new :attr:`origin` property.
        '''
        self._angle = angle
        self._axis = (ax, ay, az)
        self.matrix = Matrix().rotate(radians(self._angle), ax, ay, az)

    cdef void compute(self):
        cdef float angle = self._angle
        cdef float ax, ay, az, ox, oy, oz
        ax, ay, az = self._axis
        ox, oy, oz = self._origin
        cdef Matrix matrix
        matrix = Matrix().translate(ox, oy, oz)
        matrix = matrix.multiply(Matrix().rotate(
            radians(self._angle), ax, ay, az))
        matrix = matrix.multiply(Matrix().translate(-ox, -oy, -oz))
        self.matrix = matrix

    @property
    def angle(self):
        '''Property for getting/setting the angle of the rotation.
        '''
        return self._angle

    @angle.setter
    def angle(self, a):
        self._angle = a
        self.compute()

    @property
    def axis(self):
        '''Property for getting/setting the axis of the rotation.

        The format of the axis is (x, y, z).
        '''
        return self._axis

    @axis.setter
    def axis(self, axis):
        self._axis = axis
        self.compute()

    @property
    def origin(self):
        '''Origin of the rotation.

        .. versionadded:: 1.7.0

        The format of the origin can be either (x, y) or (x, y, z).
        '''
        return self._origin

    @origin.setter
    def origin(self, origin):
        if len(origin) == 3:
            self._origin = tuple(origin)
        elif len(origin) == 2:
            self._origin = (origin[0], origin[1], 0.)
        else:
            raise Exception('invalid number of components in origin')
        self.compute()


cdef class Scale(Transform):
    '''Instruction to create a non uniform scale transformation.

    Create using three arguments::

       Scale(x, y, z)   # scale the axes independently

    .. versionchanged:: 2.3.0
        Allowed kwargs to be used to supply x, y and z.
        Removed depreciated Scale(s) in favour of Scale(x, y, z).
    '''
    def __init__(self, *args, **kwargs):
        cdef double x, y, z

        x, y, z = 1.0, 1.0, 1.0
        if len(args) == 3:
            x, y, z = args
        x = kwargs.pop("x", x)
        y = kwargs.pop("y", y)
        z = kwargs.pop("z", z)

        Transform.__init__(self, **kwargs)
        self._origin = (0, 0, 0)

        if 'origin' in kwargs:
            origin = kwargs['origin']
            if len(origin) == 3:
                self._origin = tuple(origin)
            elif len(origin) == 2:
                self._origin = (origin[0], origin[1], 0.)
            else:
                raise Exception('invalid number of components in origin')

        self.set_scale(x, y, z)

    cdef set_scale(self, double x, double y, double z):
        cdef double ox, oy, oz
        self._x = x
        self._y = y
        self._z = z
        ox, oy, oz = self._origin
        cdef Matrix matrix
        matrix = Matrix().translate(ox, oy, oz)
        matrix = matrix.multiply(Matrix().scale(x, y, z))
        matrix = matrix.multiply(Matrix().translate(-ox, -oy, -oz))
        self.matrix = matrix

    @property
    def x(self):
        '''Property for getting/setting the scale on the X axis.

        .. versionchanged:: 1.6.0
        '''
        return self._x

    @x.setter
    def x(self, double x):
        self.set_scale(x, self._y, self._z)

    @property
    def y(self):
        '''Property for getting/setting the scale on the Y axis.

        .. versionchanged:: 1.6.0
        '''
        return self._y

    @y.setter
    def y(self, double y):
        self.set_scale(self._x, y, self._z)

    @property
    def z(self):
        '''Property for getting/setting the scale on Z axis.

        .. versionchanged:: 1.6.0
        '''
        return self._z

    @z.setter
    def z(self, double z):
        self.set_scale(self._x, self._y, z)

    @property
    def xyz(self):
        '''3 tuple scale vector in 3D in x, y, and z axis.

        .. versionchanged:: 1.6.0
        '''
        return self._x, self._y, self._z

    @xyz.setter
    def xyz(self, c):
        self.set_scale(c[0], c[1], c[2])

    @property
    def origin(self):
        '''Origin of the scale.

        .. versionadded:: 1.9.0

        The format of the origin can be either (x, y) or (x, y, z).
        '''
        return self._origin

    @origin.setter
    def origin(self, origin):
        if len(origin) == 3:
            self._origin = tuple(origin)
        elif len(origin) == 2:
            self._origin = (origin[0], origin[1], 0.)
        else:
            raise Exception('invalid number of components in origin')
        self.set_scale(self._x, self._y, self._z)


cdef class Translate(Transform):
    '''Instruction to create a translation of the model view coordinate space.

    Construct by either::

        Translate(x, y)         # translate in just the two axes
        Translate(x, y, z)      # translate in all three axes

    .. versionchanged:: 2.3.0
        Allowed kwargs to be used to supply x, y and z.
    '''
    def __init__(self, *args, **kwargs):
        cdef double x, y, z
        x, y, z = 0, 0, 0
        if len(args) == 3:
            x, y, z = args
        elif len(args) == 2:
            x, y = args
        x = kwargs.pop("x", x)
        y = kwargs.pop("y", y)
        z = kwargs.pop("z", z)

        Transform.__init__(self, **kwargs)
        self.set_translate(x, y, z)

    cdef set_translate(self, double x, double y, double z):
        self.matrix = Matrix().translate(x, y, z)
        self._x = x
        self._y = y
        self._z = z

    @property
    def x(self):
        '''Property for getting/setting the translation on the X axis.
        '''
        return self._x

    @x.setter
    def x(self, double x):
        self.set_translate(x, self._y, self._z)

    @property
    def y(self):
        '''Property for getting/setting the translation on the Y axis.
        '''
        return self._y

    @y.setter
    def y(self, double y):
        self.set_translate(self._x, y, self._z)

    @property
    def z(self):
        '''Property for getting/setting the translation on the Z axis.
        '''
        return self._z

    @z.setter
    def z(self, double z):
        self.set_translate(self._x, self._y, z)

    @property
    def xy(self):
        '''2 tuple with translation vector in 2D for x and y axis.
        '''
        return self._x, self._y

    @xy.setter
    def xy(self, c):
        self.set_translate(c[0], c[1], self._z)

    @property
    def xyz(self):
        '''3 tuple translation vector in 3D in x, y, and z axis.
        '''
        return self._x, self._y, self._z

    @xyz.setter
    def xyz(self, c):
        self.set_translate(c[0], c[1], c[2])
