'''EffectWidget
============

(highly experimental)

Experiment to make an EffectWidget, exposing part of the shader
pipeline so users can write and easily apply their own glsl effects.

Basic idea: Take implementation inspiration from shadertree example,
draw children to Fbo and apply custom shader to a RenderContext.

'''

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivy.graphics import (RenderContext, Fbo, Color, Rectangle,
                           Translate, PushMatrix, PopMatrix,
                           ClearColor, ClearBuffers)
from kivy.base import EventLoop

Builder.load_string('''
<EffectWidget>:
    canvas:
        Color:
            rgba: 1, 1, 1, 1
        Rectangle:
            texture: self.texture
            pos: self.pos
            size: self.size

<ScatterImage>:
    size: image.size
    Image:
        id: image
        source: root.source
        size: self.texture_size
''')

shader_header = '''
#ifdef GL_ES
precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0;
'''

shader_uniforms = '''
uniform vec2 resolution;
uniform float time;
'''

shader_footer_trivial = '''
void main (void){
     gl_FragColor = frag_color * texture2D(texture0, tex_coord0);
}
'''
#    gl_FragColor = texture2D(texture0, tex_coord0);

shader_footer_effect = '''
void main (void){
    vec4 normal_color = frag_color * texture2D(texture0, tex_coord0);
    vec4 effect_color = effect(normal_color, texture0, tex_coord0,
                               gl_FragCoord.xy);
    gl_FragColor = effect_color;
}
'''

effect_trivial = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    return color;
}
'''

effect_monochrome = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    float mag = 1.0/3.0 * (color.x + color.y + color.z);
    return vec4(mag, mag, mag, color.w);
}
'''


class EffectFbo(Fbo):
    def __init__(self, *args, **kwargs):
        super(EffectFbo, self).__init__(*args, **kwargs)
        self.input_texture = None
        self.texture_rectangle = None
        self.effect = ''
        self.fs = ''

    def set_fs(self, value):
        # set the fragment shader to our source code
        shader = self.shader
        old_value = shader.fs
        shader.fs = value
        if not shader.success:
            shader.fs = old_value
            raise Exception('failed')


class EffectWidget(FloatLayout):

    fs = StringProperty(None)

    # Texture of the final Fbo
    texture = ObjectProperty(None)

    # Rectangle clearing Fbo
    fbo_rectangle = ObjectProperty(None)

    # List of effect strings
    effects = ListProperty([])

    # One extra Fbo for each effect
    fbo_list = ListProperty([])

    def __init__(self, **kwargs):
        # Make sure opengl context exists
        EventLoop.ensure_window()

        self.canvas = RenderContext(use_parent_projection=True)

        with self.canvas:
            self.fbo = Fbo(size=self.size, use_parent_projection=True)

        with self.fbo.before:
            PushMatrix()
            self.fbo_translation = Translate(-self.x, -self.y, 0)
        with self.fbo:
            Color(0, 0, 0)
            self.fbo_rectangle = Rectangle(size=self.size)
        with self.fbo.after:
            PopMatrix()

        super(EffectWidget, self).__init__(**kwargs)

        Clock.schedule_interval(self.update_glsl, 0)

        self.refresh_fbo_setup()
        #self.texture = self.fbo.texture

    def on_pos(self, *args):
        self.fbo_translation.x = -self.x
        self.fbo_translation.y = -self.y

    def on_size(self, *args):
        self.fbo.size = self.size
        self.fbo_rectangle.size = self.size
        #self.texture = self.fbo.texture
        self.refresh_fbo_setup()

    def update_glsl(self, *largs):
        self.canvas['time'] = Clock.get_boottime()
        self.canvas['resolution'] = map(float, self.size)

    def on_effects(self, *args):
        self.refresh_fbo_setup()

    def refresh_fbo_setup(self, *args):
        while len(self.fbo_list) < len(self.effects):
            with self.canvas:
                new_fbo = EffectFbo(size=self.size,
                                    use_parent_projection=True)
            with new_fbo:
                Color(1, 1, 1, 1)
                new_fbo.texture_rectangle = Rectangle(
                    size=self.size,
                    texture=new_fbo.input_texture)

                new_fbo.texture_rectangle.size = self.size
            self.fbo_list.append(new_fbo)

        while len(self.fbo_list) > len(self.effects):
            old_fbo = self.fbo_list.pop()
            index = self.canvas.index(old_fbo)
            self.canvas.remove(index)

        if len(self.fbo_list) == 0:
            self.texture = self.fbo.texture
            return

        # Do resizing etc.
        for i in range(len(self.fbo_list)):
            self.fbo_list[i].size = self.size
            self.fbo_list[i].texture_rectangle.size = self.size

        for i in range(1, len(self.fbo_list)):
            fbo = self.fbo_list[i]
            fbo.input_texture = self.fbo_list[i - 1].texture
            fbo.texture_rectangle.texture = fbo.input_texture

        for effect, fbo in zip(self.effects, self.fbo_list):
            fbo.set_fs(shader_header + shader_uniforms + effect +
                       shader_footer_effect)

        self.fbo_list[0].input_texture = self.fbo.texture
        self.fbo_list[0].texture_rectangle.texture = self.fbo.texture
        self.texture = self.fbo_list[-1].texture

        Clock.schedule_once(self.fbo_capture, 1)

    def fbo_capture(self, *args):
        self.fbo.texture.save('fboin.png')
        for i, fbo in enumerate(self.fbo_list):
            fbo.input_texture.save('fbo{}_in.png'.format(i))
            fbo.texture_rectangle.texture.save('fbo{}_rec.png'.format(i))
            fbo.texture.save('fbo{}_out.png'.format(i))
        self.texture.save('selfout.png')

    def on_fs(self, instance, value):
        # set the fragment shader to our source code
        shader = self.canvas.shader
        old_value = shader.fs
        shader.fs = value
        if not shader.success:
            shader.fs = old_value
            raise Exception('failed')

    def add_widget(self, widget):
        # Add the widget to our Fbo instead of the normal canvas
        c = self.canvas
        self.canvas = self.fbo
        super(EffectWidget, self).add_widget(widget)
        self.canvas = c

    def remove_widget(self, widget):
        # Remove the widget from our Fbo instead of the normal canvas
        c = self.canvas
        self.canvas = self.fbo
        super(EffectWidget, self).remove_widget(widget)
        self.canvas = c

    def clear_widgets(self, children=None):
        # Clear widgets from our Fbo instead of the normal canvas
        c = self.canvas
        self.canvas = self.fbo
        super(EffectWidget, self).clear_widgets(children)
        self.canvas = c
