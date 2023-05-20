'''
BoxShadow
=========

.. versionadded:: 2.2.0


BoxShadow is a graphical instruction used to add a shadow effect to an element.

Its behavior is similar to the concept of a CSS3 box-shadow.

.. image:: images/boxshadow.png
    :align: center

The BoxShadow declaration must occur inside a :class:`~kivy.graphics.instructions.Canvas` statement. It works
similarly to other graphical instructions such as :class:`~kivy.graphics.vertex_instructions.Rectangle`,
:class:`~kivy.graphics.vertex_instructions.RoundedRectangle`, etc.

.. note::

    Although the ``BoxShadow`` graphical instruction has a visually similar behavior to box-shadow (CSS), the hierarchy
    of the drawing layer of ``BoxShadow`` in relation to the target element must be defined following the same layer
    hierarchy rules as when declaring other canvas instructions.
    
    |

    For more details, refer to the :attr:`~kivy.graphics.boxshadow.BoxShadow.inset` mode.

.. _example:

Example:
--------

    .. image:: images/boxshadow_demo.gif
        :align: center

    .. code-block:: kv

        <MyWidget>:
            Button:
                pos_hint: {"center_x": 0.5, "center_y": 0.5}
                size_hint: None, None
                size: 200, 150
                background_down: self.background_normal
                canvas.before:
                    Color:
                        rgba: 0, 0, 1, 0.85
                    BoxShadow:
                        pos: self.pos
                        size: self.size
                        offset: 0, -10
                        spread_radius: -20, -20
                        border_radius: 10, 10, 10, 10
                        blur_radius: 80 if self.state == "normal" else 50

'''

__all__ = ("BoxShadow", )

from kivy.logger import Logger
from kivy.graphics.fbo cimport Fbo
from kivy.graphics.vertex_instructions import Rectangle, RoundedRectangle
from kivy.graphics.context_instructions cimport Translate, Scale
from kivy.graphics.gl_instructions import ClearBuffers, ClearColor


cdef str SHADOW_fs = """
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;
/* uniform texture samplers */
uniform sampler2D texture0;

uniform int inset;
uniform float blur_radius;
uniform vec4 border_radius;
uniform vec2 spread_radius;
uniform vec2 size;
uniform vec2 offset;

// References:
// https://www.shadertoy.com/view/3tj3Dm
// https://www.shadertoy.com/view/NtVSW1
// https://iquilezles.org/articles/distfunctions2d/

float roundedBoxSDF(vec2 pos, vec2 size, vec4 radius){
    radius = min(radius, min(size.x, size.y));
    vec2 s = step(pos, vec2(0.0));
    float r = mix(mix(radius.y, radius.z, s.y), mix(radius.x, radius.w, s.y), s.x);
    vec2 q = abs(pos) - size + r;
    return min(max(q.x, q.y), 0.0) + length(max(q,0.0)) - r;
}

float sigmoid(float x) {
    return 1.0 / (1.0 + exp(-x));
}

void main (void){

    float adjustmentFactor = 0.0;
    vec2 boxSize = size / 2.0;
    vec2 boxPos = tex_coord0 * size - size/2.0;

    if (inset == 1){
        boxPos -= offset;
        boxSize -= blur_radius + spread_radius;
        adjustmentFactor = blur_radius;
    }
    else{
        boxSize -= blur_radius * 1.5 + vec2(2.0);
    }

    float distShadow = sigmoid(
        (
            roundedBoxSDF(
                boxPos,
                boxSize,
                border_radius - adjustmentFactor
            ) - adjustmentFactor
        ) / (max(1.0, blur_radius) / 4.0)
    );

    if (inset == 1){
        gl_FragColor = vec4(1.0, 1.0, 1.0, distShadow);
    }
    else{
        gl_FragColor = vec4(1.0, 1.0, 1.0, (1.0 - distShadow) * (frag_color.a * 2.0));
    }

}
"""


cdef class BoxShadow(Fbo):

    '''A box shadow effect.

    .. versionadded:: 2.2.0

    :Parameters:

        `inset`: bool, defaults to ``False``.
            Defines whether the shadow is drawn from the inside out or from the
            outline to the inside of the ``BoxShadow`` instruction.
        `size`: list | tuple, defaults to ``(100.0, 100.0)``.
            Define the raw size of the shadow, that is, you should not take into account
            changes in the value of :attr:`blur_radius` and :attr:`spread_radius`
            properties when setting this parameter.
        `pos`: list | tuple, defaults to ``(0.0, 0.0)``.
            Define the raw position of the shadow, that is, you should not take into account
            changes in the value of the :attr:`offset` property when setting this parameter.
        `offset`: list | tuple, defaults to ``(0.0, 0.0)``.
            Specifies shadow offsets in `(horizontal, vertical)` format. 
            Positive values for the offset indicate that the shadow should move to the right and/or top.
            The negative ones indicate that the shadow should move to the left and/or down.
        `blur_radius`: float, defaults to ``15.0``.
            Define the shadow blur radius. Controls shadow expansion and softness.
        `spread_radius`: list | tuple, defaults to ``(0.0, 0.0)``.
            Define the shrink/expansion of the shadow.
        `border_radius`: list | tuple, defaults to ``(0.0, 0.0, 0.0, 0.0)``.
            Specifies the radii used for the rounded corners clockwise:
            top-left, top-right, bottom-right, bottom-left.
    '''

    def __init__(self, *args, **kwargs):
        super(BoxShadow, self).__init__(size=(100, 100), fs=SHADOW_fs)
        inset = kwargs.get("inset", False)
        pos = kwargs.get("pos", (0.0, 0.0))
        size = kwargs.get("size", (100.0, 100.0))
        offset = kwargs.get("offset", (0.0, 0.0))
        blur_radius = kwargs.get("blur_radius", 15.0)
        spread_radius = kwargs.get("spread_radius", (0.0, 0.0))
        border_radius = kwargs.get("border_radius", (0.0, 0.0, 0.0, 0.0))

        self._inset = self._check_bool(inset)
        self._pos = self._check_iter("pos", pos)
        self._size = self._bounded_value(
            self._check_iter("size", size),
            min_value=0.0
        )
        self._offset = self._check_iter("offset", offset)
        self._blur_radius = self._bounded_value(
            self._check_float("blur_radius", blur_radius),
            min_value=0.0
        )
        self._spread_radius = self._check_iter("spread_radius", spread_radius)
        self._border_radius = self._bounded_value(
            self._check_iter("border_radius", border_radius, components=4),
            min_value=1.0,
            max_value=min(self.size)
        )
        self._init_texture()

    cdef void _init_texture(self):
        with self:
            ClearColor(1, 1, 1, 0)
            ClearBuffers()
            self._fbo_translate = Translate(0, 0)
            self._fbo_scale = Scale(1, 1, 1)
            self._fbo_rect = Rectangle(size=(100, 100))
        self._texture_container = RoundedRectangle(
            texture=self.texture,
            size=(100, 100),
            radius=(1, 1, 1, 1),
            segments=45
        )
        self._update_shadow()

    cdef void _update_canvas(self):
        self._texture_container.pos = self._fbo_rect.pos = self.pos
        self._texture_container.size = self._fbo_rect.size = self.size
        if self.inset:
            self._texture_container.radius = self.border_radius

    cdef void _update_fbo(self):
        cdef float scale_x, scale_y
        if 0 in self.size:
            return
        scale_x = 100 / self.size[0]
        scale_y = 100 / self.size[1]
        self._fbo_scale.x = scale_x
        self._fbo_scale.y = scale_y
        self._fbo_translate.x = - scale_x * self.pos[0]
        self._fbo_translate.y = - scale_y * self.pos[1]

    cdef void _update_shadow(self):
        self._update_canvas()
        self._update_fbo()

        self["inset"] = int(self.inset)
        self["blur_radius"] = self.blur_radius
        self["border_radius"] = self.border_radius
        self["spread_radius"] = self.spread_radius
        self["offset"] = self.offset
        self["size"] = self.size

    cdef tuple _adjusted_pos(self):
        """Return the adjusted position of the shadow texture containers,
        based on the adjusted size and offset. The pos adjustment is only
        applied if inset is disabled.
        """
        cdef float x, y
        x, y = self._pos

        # The position should be adjusted according to the size expansion,
        # with half the size used in the _adjusted_size method
        if not self.inset:
            x -= self.blur_radius * 1.5 + self.spread_radius[0] - self.offset[0]
            y -= self.blur_radius * 1.5 + self.spread_radius[1] - self.offset[1]

        return (x, y)

    cdef tuple _adjusted_size(self):
        """Returns the adjusted size of the shadow texture containers, to avoid
        unwanted shadow cropping effect. The size adjustment is only applied if
        inset is disabled.
        """
        cdef float w, h
        w, h = self._size

        # size expansion
        if not self.inset and w > 0.0 and h > 0.0:
            w += self.blur_radius * 3 + self.spread_radius[0] * 2
            h += self.blur_radius * 3 + self.spread_radius[1] * 2

        w = max(0.0, w)
        h = max(0.0, h)
        return (w, h)

    cdef object _bounded_value(self, object value, min_value=None, max_value=None):
        cdef _value = []
        if isinstance(value, (list, tuple)):
            for v in value:
                if min_value is not None and v < min_value:
                    _value.append(min_value)
                elif max_value is not None and v > max_value:
                    _value.append(max_value)
                else:
                    _value.append(v)
            value = tuple(_value)

        elif isinstance(value, (int, float)):
            if min_value is not None and value < min_value:
                value = min_value
            elif max_value is not None and value > max_value:
                value = max_value
        return value

    cdef bint _check_bool(self, object value):
        if not isinstance(value, bool):
            raise TypeError(
                f"'inset' accept only boolean values (True or False), got {type(value)}."
            )
        return value

    cdef float _check_float(self, str property_name, object value, str iter_text=""):
        if not isinstance(value, (int, float)):
            raise TypeError(
                f"'{property_name}' accept only {iter_text} int/float got {type(value)}"
            )
        return float(value)

    cdef tuple _check_iter(self, str property_name, object value, int components=2):
        cdef int _len
        cdef list _value = []
        if not isinstance(value, (list, tuple)):
            raise TypeError(
                f"'{property_name}' accepts only list/tuple, got {type(value)}"
            )
        _len = len(value)
        if _len != components:
            raise ValueError(
                f"'{property_name}' must have {components}, got {_len}"
            )

        for v in value:
            _value.append(
                self._check_float(property_name, v, iter_text="list/tuple of")
            )
        return tuple(_value)

    @property
    def pos(self):
        '''Define the raw position of the shadow, that is, you should not take
        into account changes in the value of the :attr:`offset` property when
        setting this property.

        - :attr:`inset` **OFF**:
            Returns the adjusted position of the shadow according to the
            adjusted :attr:`size` of the shadow and :attr:`offset` property.

        - :attr:`inset` **ON**:
            Returns the raw position (the same as specified).

        Defaults to ``(0.0, 0.0)``.

        .. note::

            It is recommended that this property matches the raw position of
            the shadow target element. To manipulate horizontal and vertical
            offset, use :attr:`offset` instead.

        '''
        return self._adjusted_pos()

    @pos.setter
    def pos(self, value):
        self._pos = self._check_iter("pos", value)
        self._update_shadow()

    @property
    def size(self):
        '''Define the raw size of the shadow, that is, you should not take into
        account changes in the value of :attr:`blur_radius` and :attr:`spread_radius` properties.

        - :attr:`inset` **OFF**:
            Returns the adjusted size of the shadow according to the
            :attr:`blur_radius` and :attr:`spread_radius` properties.

        - :attr:`inset` **ON**:
            Returns the raw size (the same as specified).

        Defaults to ``(100.0, 100.0)``.

        .. note::

            It is recommended that this property matches the raw size of
            the shadow target element. To control the shrink/expansion of
            the shadow's raw :attr:`size`, use :attr:`spread_radius` instead.

        '''
        return self._adjusted_size()

    @size.setter
    def size(self, value):
        _size = self._check_iter("size", value)
        self._size = self._bounded_value(_size, min_value=0.0)
        self._update_shadow()

    @property
    def border_radius(self):
        '''Specifies the radii used for the rounded corners clockwise:
        top-left, top-right, bottom-right, bottom-left.

        Defaults to ``(0.0, 0.0, 0.0, 0.0)``.

        - :attr:`inset` **OFF**:
            .. image:: images/boxshadow_border_radius.svg
                :align: center
        
        | 

        - :attr:`inset` **ON**:
            .. image:: images/boxshadow_border_radius_inset.svg
                :align: center

        '''
        return self._bounded_value(self._border_radius, min_value=1.0, max_value=max(min(self.size) / 2, 1.0))

    @border_radius.setter
    def border_radius(self, value):
        self._border_radius = self._check_iter("border_radius", value, components=4)
        self._update_shadow()

    @property
    def spread_radius(self):
        '''Define the shrink/expansion of the shadow in `[horizontal, vertical]` format.

        Defaults to ``(0.0, 0.0)``.

        This property is especially useful for cases where you want to achieve
        a softer shadow around the element, by setting negative values for
        :attr:`spread_radius` and a larger value for :attr:`blur_radius` as
        in the :ref:`example <example>`.

        - :attr:`inset` **OFF**:
            In the image below, the target element has a raw size of ``200 x 150px``.
            Positive changes to the :attr:`spread_radius` values will cause the raw
            :attr:`size` of the shadow to increase, while negative values will cause
            the shadow to shrink.

            .. image:: images/boxshadow_spread_radius.svg
                :align: center

        | 

        - :attr:`inset` **ON**:
            Positive values will cause the shadow to grow into the bounding box,
            while negative values will cause the shadow to shrink.

            .. image:: images/boxshadow_spread_radius_inset.svg
                :align: center

        '''
        return self._spread_radius

    @spread_radius.setter
    def spread_radius(self, value):
        self._spread_radius = self._check_iter("spread_radius", value)
        self._update_shadow()

    @property
    def offset(self):
        '''Specifies shadow offsets in `[horizontal, vertical]` format. 
        Positive values for the offset indicate that the shadow should move to
        the right and/or top.
        The negative ones indicate that the shadow should move to the left
        and/or down.

        Defaults to ``(0.0, 0.0)``.

        For this property to work as expected, it is indicated that the value
        of :attr:`pos` coincides with the position of the target element of the
        shadow, as in the example below:

        - :attr:`inset` **OFF**:
            .. image:: images/boxshadow_offset.svg
                :align: center
        
        | 

        - :attr:`inset` **ON**:
            .. image:: images/boxshadow_offset_inset.svg
                :align: center

        '''
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = self._check_iter("offset", value)
        self._update_shadow()

    @property
    def blur_radius(self):
        '''Define the shadow blur radius. Controls shadow expansion and softness.

        Defaults to ``15.0``.

        In the images below, the start and end positions of the shadow blur
        effect length are indicated.
        The transition between color and transparency is seamless, and although
        the shadow appears to end before before the dotted rectangle, its end
        is made to be as smooth as possible.

        - :attr:`inset` **OFF**:
            .. image:: images/boxshadow_blur_radius.svg
                :align: center
        
        | 

        - :attr:`inset` **ON**:
            .. image:: images/boxshadow_blur_radius_inset.svg
                :align: center
        
        | 

        .. note::
            In some cases (**if this is not your intention**), placing an element
            above the shadow (before the blur radius ends) will result in a unwanted
            cropping/overlay behavior rather than continuity, breaking the
            shadow's soft ending, as shown in the image below.

            | 

            .. image:: images/boxshadow_common_mistake_1.svg
                :align: center

        '''
        return self._blur_radius

    @blur_radius.setter
    def blur_radius(self, value):
        _blur_radius = self._check_float("blur_radius", value)
        self._blur_radius = self._bounded_value(_blur_radius, min_value=0.0)
        self._update_shadow()

    @property
    def inset(self):
        """Defines whether the shadow is drawn from the inside out or from the outline to the inside of the ``BoxShadow`` instruction.

        Defaults to ``False``.

        .. note::
            | 

            Although the inset mode determines the drawing behavior of the shadow, the position of the ``BoxShadow``
            instruction in the ``canvas`` hierarchy depends on the other graphic instructions present in the
            :class:`~kivy.graphics.instructions.Canvas` instruction tree.

            | 

            In other words, if the **target** is in the ``canvas`` layer and you want to use the default ``inset = False``
            mode to create an elevation effect, you must declare the ``BoxShadow`` instruction in ``canvas.before`` layer.

            | 

            .. image:: images/boxshadow_example_1.png
                :align: center
                :width: 300px

            .. code-block:: kv

                <MyWidget@Widget>:
                    size_hint: None, None
                    size: 100, 100
                    pos: 100, 100

                    canvas.before:
                        # BoxShadow statements
                        Color:
                            rgba: 0, 0, 0, 0.65
                        BoxShadow:
                            pos: self.pos
                            size: self.size
                            offset: 0, -10
                            blur_radius: 25
                            spread_radius: -10, -10
                            border_radius: 10, 10, 10, 10
                    
                    canvas:
                        # target element statements
                        Color:
                            rgba: 1, 1, 1, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size
            
            | 

            Or, if the target is in the ``canvas`` layer and you want to use the ``inset = True`` mode to create an
            insertion effect, you must declare the ``BoxShadow`` instruction in the ``canvas`` layer, immediately after
            the **target** ``canvas`` declaration, or declare it in ``canvas.after``.

            | 

            .. image:: images/boxshadow_example_2.png
                :align: center
                :width: 300px

            .. code-block:: kv

                <MyWidget@Widget>:
                    size_hint: None, None
                    size: 100, 100
                    pos: 100, 100

                    canvas:
                        # target element statements
                        Color:
                            rgba: 1, 1, 1, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size

                        # BoxShadow statements
                        Color:
                            rgba: 0, 0, 0, 0.65
                        BoxShadow:
                            inset: True
                            pos: self.pos
                            size: self.size
                            offset: 0, -10
                            blur_radius: 25
                            spread_radius: -10, -10
                            border_radius: 10, 10, 10, 10

            | 

            **In summary:**

                - Elevation effect - ``inset = False``: the ``BoxShadow`` instruction needs to be drawn **before** the target element.

                - Insertion effect - ``inset = True``: the ``BoxShadow`` instruction needs to be drawn **after** the target element.

            | 

            In general, ``BoxShadow`` is more flexible than box-shadow (CSS) because the ``inset = False`` and
            ``inset = True`` modes do not limit the drawing of the shadow below and above the target element,
            respectively. Actually, you can define any hierarchy you want in the :class:`~kivy.graphics.instructions.Canvas`
            declaration tree, to create more complex effects that go beyond common shadow effects.

        **Modes:**

            - ``False`` (default) - The shadow is drawn inside out the ``BoxShadow`` instruction, creating a raised effect.
            
            - ``True`` - The shadow is drawn from the outline to the inside of the ``BoxShadow`` instruction, creating a inset effect.

        .. image:: images/boxshadow_inset.svg
            :align: center

        """
        return self._inset

    @inset.setter
    def inset(self, value):
        self._inset = self._check_bool(value)
        self._update_shadow()
