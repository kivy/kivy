'''
Tree shader
===========

This example is an experimentation to show how we can use shader for a tree
subset. Here, we made a ShaderTreeWidget, different than the ShaderWidget
in the plasma.py example.

The ShaderTree widget create a Frambuffer, render his children on it, and
render the Framebuffer with a specific Shader.
With this way, you can apply cool effect on your widgets :)

'''

from kivy.clock import Clock
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window  # side effects needed by Shader
from kivy.properties import StringProperty, ObjectProperty
from kivy.graphics import (RenderContext, Fbo, Color, ClearColor, ClearBuffers,
        Rectangle)

import itertools


header = '''
$HEADER$

uniform vec2 resolution;
uniform float time;
'''

# pulse (Danguafer/Silexars, 2010)
shader_pulse = header + '''
void main(void)
{
    vec2 halfres = resolution.xy/2.0;
    vec2 cPos = vec4(frag_modelview_mat * gl_FragCoord).xy;

    cPos.x -= 0.5*halfres.x*sin(time/2.0)+0.3*halfres.x*cos(time)+halfres.x;
    cPos.y -= 0.4*halfres.y*sin(time/5.0)+0.3*halfres.y*cos(time)+halfres.y;
    float cLength = length(cPos);

    vec2 uv = tex_coord0+(cPos/cLength)*sin(cLength/30.0-time*10.0)/25.0;
    vec3 col = texture2D(texture0,uv).xyz*50.0/cLength;

    gl_FragColor = vec4(col,1.0);
}
'''

# post processing (by iq, 2009)
shader_postprocessing = header + '''
uniform vec2 uvsize;
uniform vec2 uvpos;
void main(void)
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

shader_monochrome = header + '''
void main() {
    vec4 rgb = texture2D(texture0, tex_coord0);
    float c = (rgb.x + rgb.y + rgb.z) * 0.3333;
    gl_FragColor = vec4(c, c, c, 1.0);
}
'''


class ShaderWidget(FloatLayout):

    # property to set the source code for fragment shader
    fs = StringProperty(None)

    # texture of the framebuffer
    texture = ObjectProperty(None)

    def __init__(self, **kwargs):
        # Instead of using canvas, we will use a RenderContext,
        # and change the default shader used.
        self.canvas = RenderContext(use_parent_projection=True,
                                    use_parent_modelview=True,
                                    use_parent_frag_modelview=True)

        with self.canvas:
            self.fbo = Fbo(size=self.size)
            self.fbo_color = Color(1, 1, 1, 1)
            self.fbo_rect = Rectangle()

        with self.fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()

        # call the constructor of parent
        # if they are any graphics object, they will be added on our new canvas
        super(ShaderWidget, self).__init__(**kwargs)

        # We'll update our glsl variables in a clock
        Clock.schedule_interval(self.update_glsl, 0)

    def update_glsl(self, *largs):
        self.canvas['time'] = Clock.get_boottime()
        self.canvas['resolution'] = [float(v) for v in self.size]

    def on_fs(self, instance, value):
        # set the fragment shader to our source code
        shader = self.canvas.shader
        old_value = shader.fs
        shader.fs = value
        if not shader.success:
            shader.fs = old_value
            raise Exception('failed')

    #
    # now, if we have new widget to add,
    # add their graphics canvas to our Framebuffer, not the usual canvas.
    #

    def add_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(ShaderWidget, self).add_widget(widget)
        self.canvas = c

    def remove_widget(self, widget):
        c = self.canvas
        self.canvas = self.fbo
        super(ShaderWidget, self).remove_widget(widget)
        self.canvas = c

    def on_size(self, instance, value):
        self.fbo.size = value
        self.texture = self.fbo.texture
        self.fbo_rect.size = value

    def on_pos(self, instance, value):
        self.fbo_rect.pos = value

    def on_texture(self, instance, value):
        self.fbo_rect.texture = value


class RootWidget(FloatLayout):
    shader_btn = ObjectProperty(None)
    shader_widget = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)

        # prepare shader list
        available_shaders = [
                shader_pulse,
                shader_postprocessing,
                shader_monochrome,
        ]
        self.shaders = itertools.cycle(available_shaders)

        self.shader_btn.bind(on_release=self.change)

    def change(self, *largs):
        self.shader_widget.fs = next(self.shaders)


class ShaderTreeApp(App):
    def build(self):
        return RootWidget()


if __name__ == '__main__':
    ShaderTreeApp().run()
