'''
BoxShadow
=========

.. versionadded:: 2.2.0


BoxShadow is a graphical instruction used to add a shadow effect to an element.

Its behavior is similar to the concept of a CSS3 box-shadow.

.. image:: images/boxshadow.png
    :align: center

The BoxShadow declaration must occur inside a :class:`~kivy.graphics.instructions.Canvas` canvas statement. It works
similarly to other graphical instructions such as :class:`~kivy.graphics.vertex_instructions.Rectangle`,
:class:`~kivy.graphics.vertex_instructions.RoundedRectangle`, etc.

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
                        spread_radius: -20
                        border_radius: 10, 10, 10, 10
                        blur_radius: 80 if self.state == "normal" else 50

'''

__all__ = ("BoxShadow", )

from kivy.logger import Logger
from kivy.graphics.fbo cimport Fbo
from kivy.graphics.vertex_instructions import Rectangle
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

uniform float blur_radius;
uniform vec4 border_radius;
uniform vec2 size;

// References:
// https://www.shadertoy.com/view/3tj3Dm
// https://www.shadertoy.com/view/NtVSW1
// https://iquilezles.org/articles/distfunctions2d/

float roundedBoxSDF(vec2 pos, vec2 size, vec4 radius){
    vec2 s = step(pos, vec2(0.0));
    radius = clamp(radius, 0.0, min(size.x, size.y));
    float r = mix(mix(radius.y, radius.z, s.y), mix(radius.x, radius.w, s.y), s.x);
    return length(max(abs(pos) + vec2(r) - size, 0.0)) - r;
}

float sigmoid(float x) {
    return 1.0 / (1.0 + exp(-x));
}

void main (void){

float distShadow = sigmoid(
    roundedBoxSDF(
        tex_coord0 * size - size/2.0, size/2.0 - blur_radius * 1.5 - vec2(2.0),
        border_radius) / (max(1.0, blur_radius)/4.0
    )
);


// Some devices require the resulting color to be blended with the texture.
// Otherwise there will be a compilation issue.

vec4 texture = texture2D(texture0, tex_coord0);
vec4 shadow = vec4(frag_color.rgb, 1.0 - distShadow) * (frag_color.a * 2.0);

gl_FragColor = mix(texture, shadow, 1.0);

}
"""


cdef class BoxShadow(Fbo):

    '''A box shadow effect.

    .. versionadded:: 2.2.0

    :Parameters:

        `size`: list | tuple, defaults to ``[100.0, 100.0]``.
            Define the raw size of the shadow, that is, it does not take into account
            changes in the value of :attr:`blur_radius` and/or :attr:`spread_radius` properties.
        `pos`: list | tuple, defaults to ``[0.0, 0.0]``.
            Define the raw pos of the shadow, that is, it does not take into
            account changes in the value of :attr:`offset` property.
        `offset`: list | tuple, defaults to ``[0.0, 0.0]``.
            Specifies shadow offsets in `[horizontal, vertical]` format. 
            Positive values for the offset indicate that the shadow should move to the right and/or top.
            The negative ones indicate that the shadow should move to the left and/or down.
        `blur_radius`: float, defaults to ``5.0``.
            Define the shadow blur radius. Controls shadow expansion and softness.
        `spread_radius`: float, defaults to ``0.0``.
            Define the decrease/expansion of the shadow's raw :attr:`size`.
        `border_radius`: list | tuple, defaults to ``[0.0, 0.0, 0.0, 0.0]``.
            Specifies the radii used for the rounded corners clockwise:
            top-left, top-right, bottom-right, bottom-left.
    '''

    def __init__(self, *args, **kwargs):
        super(BoxShadow, self).__init__(size=(100, 100))
        pos = kwargs.get("pos", (0.0, 0.0))
        size = kwargs.get("size", (0.0, 0.0))
        offset = kwargs.get("offset", (0.0, 0.0))
        blur_radius = kwargs.get("blur_radius", 5.0)
        spread_radius = kwargs.get("spread_radius", 0.0)
        border_radius = kwargs.get("border_radius", (0.0, 0.0,0.0, 0.0))

        self._pos = self._check_iter("pos", pos)
        self._size = self._check_iter("size", size)
        self._offset = self._check_iter("offset", offset)
        self._blur_radius = max(0.0, self._check_float("blur_radius", blur_radius))
        self._spread_radius = self._check_float("spread_radius", spread_radius)
        self._border_radius = self._check_iter("border_radius", border_radius, components=4)

        self._init_texture()

    cdef void _init_texture(self):
        self.shader.fs = SHADOW_fs
        self._rect = Rectangle(size=(100, 100))
        self._rect.texture = self.texture
        with self:
            ClearColor(1, 1, 1, 0)
            ClearBuffers()
            self._fbo_translate = Translate(0, 0)
            self._fbo_scale = Scale(1, 1, 1)
        self.add(self._rect)
        self._update_shadow()

    cdef void _update_canvas(self):
        self._rect.pos = (
            self.pos[0] + self.offset[0],
            self.pos[1] + self.offset[1],
        )
        self._rect.size = self.size

    cdef void _update_fbo(self):
        cdef float _scale_x, _scale_y
        _scale_x = 100 / self.size[0]
        _scale_y = 100 / self.size[1]
        self._fbo_scale.x = _scale_x
        self._fbo_scale.y = _scale_y
        self._fbo_translate.x = -_scale_x * (self.pos[0] + self.offset[0])
        self._fbo_translate.y = -_scale_y * (self.pos[1] + self.offset[1])

    cdef void _update_shadow(self):
        if 0 in self.size:
            return
        self._update_canvas()
        self._update_fbo()
        self["blur_radius"] = self.blur_radius
        self["border_radius"] = self.border_radius
        self["size"] = self.size

    cdef tuple _adjusted_pos(self):
        cdef float x, y
        x = self._pos[0] - self.blur_radius * 1.5 - self.spread_radius
        y = self._pos[1] - self.blur_radius * 1.5 - self.spread_radius
        return (x, y)

    cdef tuple _adjusted_size(self):
        cdef float w, h
        w = max(
            0, self._size[0] + self.blur_radius * 3 + self.spread_radius * 2
        )
        h = max(
            0, self._size[1] + self.blur_radius * 3 + self.spread_radius * 2
        )
        return (w, h)

    cdef float _check_float(self, str property_name, object value, str iter_text=""):
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"{property_name} accept only {iter_text} int/float (got {type(value)})"
            )
        return float(value)

    cdef tuple _check_iter(self, str property_name, object value, int components=2):
        cdef int _len
        cdef list _value = []
        if not isinstance(value, (list, tuple)):
            raise ValueError(
                f"{property_name} accepts only list/tuple (got {type(value)})"
            )
        _len = len(value)
        if _len != components:
            raise ValueError(
                f"{property_name} must have {components} (got {_len})"
            )

        for v in value:
            _value.append(
                self._check_float(property_name, v, iter_text="list/tuple of")
            )
        return tuple(_value)

    @property
    def pos(self):
        '''Define the raw pos of the shadow, that is, it does not take into
        account changes in the value of :attr:`offset` property.

        Defaults to ``[0.0, 0.0]``.

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
        '''Define the raw size of the shadow, that is, it does not take into
        account changes in the value of :attr:`blur_radius` and/or
        :attr:`spread_radius` properties.

        Defaults to ``[100.0, 100.0]``.

        .. note::

            It is recommended that this property matches the raw size of
            the shadow target element. To manipulate the decrease/expansion of
            the shadow's raw :attr:`size`, use :attr:`spread_radius` instead.

        '''
        return self._adjusted_size()

    @size.setter
    def size(self, value):
        self._size = self._check_iter("size", value)
        self._update_shadow()

    @property
    def border_radius(self):
        '''Specifies the radii used for the rounded corners clockwise:
        top-left, top-right, bottom-right, bottom-left.

        Defaults to ``[0.0, 0.0, 0.0, 0.0]``.

        .. image:: images/boxshadow_border_radius.svg
            :align: center
            :scale: 90%

        '''
        return self._border_radius

    @border_radius.setter
    def border_radius(self, value):
        self._border_radius = self._check_iter("border_radius", value, components=4)
        self._update_shadow()

    @property
    def spread_radius(self):
        '''Define the decrease/expansion of the shadow's inner size.

        Defaults to ``0.0``.

        In the image below, the target element has a raw size of ``200 x 150px``.
        Positive changes to the :attr:`spread_radius` value will cause the raw
        :attr:`size` of the shadow to increase in both horizontal and vertical
        directions, while negative values will cause the shadow to decrease.

        This property is especially useful for cases where you want to achieve
        a softer shadow around the element, by setting a negative value for
        :attr:`spread_radius` and a larger value for :attr:`blur_radius` as
        in the :ref:`example <example>`.

        .. image:: images/boxshadow_spread_radius.svg
            :align: center

        '''
        return self._spread_radius

    @spread_radius.setter
    def spread_radius(self, value):
        self._spread_radius = self._check_float("spread_radius", value)
        self._update_shadow()

    @property
    def offset(self):
        '''Specifies shadow offsets in `[horizontal, vertical]` format. 
        Positive values for the offset indicate that the shadow should move to
        the right and/or top.
        The negative ones indicate that the shadow should move to the left
        and/or down.

        Defaults to ``[0.0, 0.0]``.

        For this property to work as expected, it is indicated that the value
        of :attr:`pos` coincides with the position of the target element of the
        shadow, as in the example below:

        .. image:: images/boxshadow_offset.svg
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

        Defaults to ``5.0``

        In the image below, the start and end positions of the shadow blur
        effect length are indicated.
        The transition between color and transparency is seamless, and although
        the shadow appears to end before the red rectangle, its edge is made
        to be as smooth as possible.

        .. image:: images/boxshadow_blur_radius.svg
            :align: center
            :scale: 90%

        .. note::
            In some cases (**if this is not your intention**), placing an element
            above the shadow (before the blur radius ends) will result in a
            clipping/overlay effect rather than continuity, breaking the
            shadow's soft ending, as shown in the image below.

            | 

            .. image:: images/boxshadow_common_mistake_1.svg
                :align: center

        '''
        return self._blur_radius

    @blur_radius.setter
    def blur_radius(self, value):
        self._blur_radius = max(0.0, self._check_float("blur_radius", value))
        self._update_shadow()
