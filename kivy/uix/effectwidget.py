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
from kivy.uix.boxlayout import BoxLayout
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

effect_red = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    return vec4(color.x, 0.0, 0.0, 1.0);
}
'''

effect_green = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    return vec4(0.0, color.y, 0.0, 1.0);
}
'''

effect_blue = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    return vec4(0.0, 0.0, color.z, 1.0);
}
'''

effect_invert = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    return vec4(1.0 - color.xyz, 1.0);
}
'''

effect_mix = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    return vec4(color.z, color.x, color.y, 1.0);
}
'''

effect_flash = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    return color * abs(sin(time));
}
'''

effect_blur_h = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    float dt = 0.5 * 1.0 / resolution.x;
    vec4 sum = vec4(0.0);
    sum += texture2D(texture, vec2(tex_coords.x - 4.0*dt, tex_coords.y)) * 0.05;
    sum += texture2D(texture, vec2(tex_coords.x - 3.0*dt, tex_coords.y)) * 0.09;
    sum += texture2D(texture, vec2(tex_coords.x - 2.0*dt, tex_coords.y)) * 0.12;
    sum += texture2D(texture, vec2(tex_coords.x - dt, tex_coords.y)) * 0.15;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y)) * 0.16;
    sum += texture2D(texture, vec2(tex_coords.x + dt, tex_coords.y)) * 0.15;
    sum += texture2D(texture, vec2(tex_coords.x + 2.0*dt, tex_coords.y)) * 0.12;
    sum += texture2D(texture, vec2(tex_coords.x + 3.0*dt, tex_coords.y)) * 0.09;
    sum += texture2D(texture, vec2(tex_coords.x + 4.0*dt, tex_coords.y)) * 0.05;
    return sum;
}
'''

effect_blur_v = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    float dt = 0.5 * 1.0 / resolution.y;
    vec4 sum = vec4(0.0);
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y - 4.0*dt)) * 0.05;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y - 3.0*dt)) * 0.09;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y - 2.0*dt)) * 0.12;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y - dt)) * 0.15;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y)) * 0.16;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y + dt)) * 0.15;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y + 2.0*dt)) * 0.12;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y + 3.0*dt)) * 0.09;
    sum += texture2D(texture, vec2(tex_coords.x, tex_coords.y + 4.0*dt)) * 0.05;
    return sum;
}
'''

effect_postprocessing = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    vec2 q = tex_coord0 * vec2(1, -1);
    vec2 uv = 0.5 + (q-0.5);//*(0.9);// + 0.1*sin(0.2*time));

    vec3 oricol = texture2D(texture0,vec2(q.x,1.0-q.y)).xyz;
    vec3 col;

    col.r = texture2D(texture0,vec2(uv.x+0.003,-uv.y)).x;
    col.g = texture2D(texture0,vec2(uv.x+0.000,-uv.y)).y;
    col.b = texture2D(texture0,vec2(uv.x-0.003,-uv.y)).z;

    col = clamp(col*0.5+0.5*col*col*1.2,0.0,1.0);

    //col *= 0.5 + 0.5*16.0*uv.x*uv.y*(1.0-uv.x)*(1.0-uv.y);

    col *= vec3(0.8,1.0,0.7);

    col *= 0.9+0.1*sin(10.0*time+uv.y*1000.0);

    col *= 0.97+0.03*sin(110.0*time);

    float comp = smoothstep( 0.2, 0.7, sin(time) );
    //col = mix( col, oricol, clamp(-2.0+2.0*q.x+3.0*comp,0.0,1.0) );

    gl_FragColor = vec4(col,1.0);
}
'''

effect_plasma = '''
vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
   float x = coords.x;
   float y = coords.y;
   float mov0 = x+y+cos(sin(time)*2.)*100.+sin(x/100.)*1000.;
   float mov1 = y / resolution.y / 0.2 + time;
   float mov2 = x / resolution.x / 0.2;
   float c1 = abs(sin(mov1+time)/2.+mov2/2.-mov1-mov2+time);
   float c2 = abs(sin(c1+sin(mov0/1000.+time)+sin(y/40.+time)+
                  sin((x+y)/100.)*3.));
   float c3 = abs(sin(c2+cos(mov1+mov2+c2)+cos(mov2)+sin(x/1000.)));
   return vec4( 0.5*(c1 + color.z), 0.5*(c2 + color.x),
                0.5*(c3 + color.y), 1.0);
}
'''


class EffectFbo(Fbo):
    def __init__(self, *args, **kwargs):
        super(EffectFbo, self).__init__(*args, **kwargs)
        self.texture_rectangle = None

    def set_fs(self, value):
        # set the fragment shader to our source code
        shader = self.shader
        old_value = shader.fs
        shader.fs = value
        if not shader.success:
            shader.fs = old_value
            raise Exception('failed')


class EffectWidget(BoxLayout):

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

        self.canvas = RenderContext(use_parent_projection=True,
                                    use_parent_modelview=True)

        with self.canvas:
            self.fbo = Fbo(size=self.size)

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
        Clock.schedule_interval(self.update_fbos, 0)

    def on_pos(self, *args):
        self.fbo_translation.x = -self.x
        self.fbo_translation.y = -self.y

    def on_size(self, *args):
        self.fbo.size = self.size
        self.fbo_rectangle.size = self.size
        self.refresh_fbo_setup()

    def update_glsl(self, *largs):
        time = Clock.get_boottime()
        resolution = [float(size) for size in self.size]
        self.canvas['time'] = time
        self.canvas['resolution'] = resolution
        for fbo in self.fbo_list:
            fbo['time'] = time
            fbo['resolution'] = resolution

    def on_effects(self, *args):
        self.refresh_fbo_setup()

    def update_fbos(self, *args):
        for fbo in self.fbo_list:
            fbo.ask_update()

    def refresh_fbo_setup(self, *args):
        # Add/remove fbos until there is one per effect
        while len(self.fbo_list) < len(self.effects):
            with self.canvas:
                new_fbo = EffectFbo(size=self.size)
            with new_fbo:
                Color(1, 1, 1, 1)
                new_fbo.texture_rectangle = Rectangle(
                    size=self.size)

                new_fbo.texture_rectangle.size = self.size
            self.fbo_list.append(new_fbo)
        while len(self.fbo_list) > len(self.effects):
            old_fbo = self.fbo_list.pop()
            self.canvas.remove(old_fbo)

        # Do resizing etc.
        self.fbo.size = self.size
        self.fbo_rectangle.size = self.size
        for i in range(len(self.fbo_list)):
            self.fbo_list[i].size = self.size
            self.fbo_list[i].texture_rectangle.size = self.size

        # If there are no effects, just draw our main fbo
        if len(self.fbo_list) == 0:
            self.texture = self.fbo.texture
            return

        for i in range(1, len(self.fbo_list)):
            fbo = self.fbo_list[i]
            fbo.texture_rectangle.texture = self.fbo_list[i - 1].texture

        for effect, fbo in zip(self.effects, self.fbo_list):
            fbo.set_fs(shader_header + shader_uniforms + effect +
                       shader_footer_effect)

        self.fbo_list[0].texture_rectangle.texture = self.fbo.texture
        self.texture = self.fbo_list[-1].texture

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
