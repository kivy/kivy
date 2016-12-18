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
from kivy.uix.button import Button
from kivy.uix.scatter import Scatter
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty
from kivy.graphics import RenderContext, Fbo, Color, Rectangle


header = '''
#ifdef GL_ES
precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0;

uniform vec2 resolution;
uniform float time;
'''

# pulse (Danguafer/Silexars, 2010)
shader_pulse = header + '''
void main(void)
{
    vec2 halfres = resolution.xy/2.0;
    vec2 cPos = gl_FragCoord.xy;

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
        self.canvas = RenderContext(use_parent_projection=True)

        # We create a framebuffer at the size of the window
        # FIXME: this should be created at the size of the widget
        with self.canvas:
            self.fbo = Fbo(size=Window.size, use_parent_projection=True)

        # Set the fbo background to black.
        with self.fbo:
            Color(0, 0, 0)
            Rectangle(size=Window.size)

        # call the constructor of parent
        # if they are any graphics object, they will be added on our new canvas
        super(ShaderWidget, self).__init__(**kwargs)

        # We'll update our glsl variables in a clock
        Clock.schedule_interval(self.update_glsl, 0)

        # Don't forget to set the texture property to the texture
        # of framebuffer
        self.texture = self.fbo.texture

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


class ScatterImage(Scatter):
    source = StringProperty(None)


class ShaderTreeApp(App):
    def build(self):
        # prepare shader list
        available_shaders = (
            shader_pulse, shader_postprocessing, shader_monochrome)
        self.shader_index = 0

        # create our widget tree
        root = FloatLayout()
        sw = ShaderWidget()
        root.add_widget(sw)

        # add a button and scatter image inside the shader widget
        btn = Button(text='Hello world', size_hint=(None, None),
                     pos_hint={'center_x': .25, 'center_y': .5})
        sw.add_widget(btn)

        center = Window.width * 0.75 - 256, Window.height * 0.5 - 256
        scatter = ScatterImage(source='tex3.jpg', size_hint=(None, None),
                               size=(512, 512), pos=center)
        sw.add_widget(scatter)

        # create a button outside the shader widget, to change the current used
        # shader
        btn = Button(text='Change fragment shader', size_hint=(1, None),
                     height=50)

        def change(*largs):
            sw.fs = available_shaders[self.shader_index]
            self.shader_index = ((self.shader_index + 1) %
                                 len(available_shaders))
        btn.bind(on_release=change)
        root.add_widget(btn)
        return root


if __name__ == '__main__':
    ShaderTreeApp().run()
