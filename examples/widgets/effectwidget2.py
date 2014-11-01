'''
This is an example of creating your own effect by writing a glsl string.
'''

from kivy.base import runTouchApp
from kivy.lang import Builder
from kivy.uix.effectwidget import EffectWidget, EffectBase


# The effect string is glsl code defining an effect function.
effect_string = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    // Note that time is a uniform variable that is automatically
    // provided to all effects.
    float red = color.x * abs(sin(time*2.0));
    float green = color.y;  // No change
    float blue = color.z * (1.0 - abs(sin(time*2.0)));
    return vec4(red, green, blue, color.w);
}
'''


class DemoEffect(EffectWidget):
    def __init__(self, *args, **kwargs):
        self.effect_reference = EffectBase(glsl=effect_string)
        super(DemoEffect, self).__init__(*args, **kwargs)


widget = Builder.load_string('''
DemoEffect:
    effects: [self.effect_reference] if checkbox.active else []
    orientation: 'vertical'
    Button:
        text: 'Some text so you can see what happens.'
    BoxLayout:
        size_hint_y: None
        height: dp(50)
        Label:
            text: 'Enable effect?'
        CheckBox:
            id: checkbox
            active: True
''')

runTouchApp(widget)
