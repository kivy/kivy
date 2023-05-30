'''
This example demonstrates creating and using an AdvancedEffectBase. In
this case, we use it to efficiently pass the touch coordinates into the shader.
'''

from kivy.base import runTouchApp
from kivy.properties import ListProperty
from kivy.lang import Builder
from kivy.uix.effectwidget import EffectWidget, AdvancedEffectBase


effect_string = '''
uniform vec2 touch;

vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    vec2 distance = 0.025*(coords - touch);
    float dist_mag = (distance.x*distance.x + distance.y*distance.y);
    vec3 multiplier = vec3(abs(sin(dist_mag - time)));
    return vec4(multiplier * color.xyz, 1.0);
}
'''


class TouchEffect(AdvancedEffectBase):
    touch = ListProperty([0.0, 0.0])

    def __init__(self, *args, **kwargs):
        super(TouchEffect, self).__init__(*args, **kwargs)
        self.glsl = effect_string

        self.uniforms = {'touch': [0.0, 0.0]}

    def on_touch(self, *args, **kwargs):
        self.uniforms['touch'] = [float(i) for i in self.touch]


class TouchWidget(EffectWidget):
    def __init__(self, *args, **kwargs):
        super(TouchWidget, self).__init__(*args, **kwargs)
        self.effect = TouchEffect()
        self.effects = [self.effect]

    def on_touch_down(self, touch):
        super(TouchWidget, self).on_touch_down(touch)
        self.on_touch_move(touch)

    def on_touch_move(self, touch):
        self.effect.touch = touch.pos


root = Builder.load_string('''
TouchWidget:
    Button:
        text: 'Some text!'
    Image:
        source: 'data/logo/kivy-icon-512.png'
        fit_mode: "fill"
''')


runTouchApp(root)
