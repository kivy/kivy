'''EffectWidget
============

(highly experimental)

Experiment to make an EffectWidget, exposing part of the shader
pipeline so users can write and easily apply their own glsl effects.

Basic idea: Take implementation inspiration from shadertree example,
draw children to Fbo and apply custom shader to a RenderContext.

'''

from kivy.clock import Clock
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.scatter import Scatter
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.properties import StringProperty, ObjectProperty
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

plasma_shader = shader_header + '''
uniform vec2 resolution;
uniform float time;

void main(void)
{
    float x = gl_FragCoord.x;
    float y = gl_FragCoord.y;

    vec4 normal_rgba = texture2D(texture0, tex_coord0);

    float mov0 = x+y+cos(sin(time)*2.)*100.+sin(x/100.)*1000.;
    float mov1 = y / resolution.y / 0.2 + time;
    float mov2 = x / resolution.x / 0.2;
    float c1 = abs(sin(mov1+time)/2.+mov2/2.-mov1-mov2+time);
    float c2 = abs(sin(c1+sin(mov0/1000.+time)+
                   sin(y/40.+time)+sin((x+y)/100.)*3.));
    float c3 = abs(sin(c2+cos(mov1+mov2+c2)+cos(mov2)+sin(x/1000.)));
    gl_FragColor = vec4( normal_rgba.x, c2, normal_rgba.y, 1.0);
}
'''

shader_monochrome = shader_header + '''
void main() {
    vec4 rgb = texture2D(texture0, tex_coord0);
    float c = (rgb.x + rgb.y + rgb.z) * 0.3333;
    gl_FragColor = vec4(c, c, c, 1.0);
}
'''

shader_postprocessing = shader_header + '''
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

with open('gradient.glsl') as fileh:
    gradient_shader = shader_header + shader_uniforms + fileh.read()


class EffectWidget(FloatLayout):

    fs = StringProperty(None)

    # Texture of the Fbo
    texture = ObjectProperty(None)

    # Rectangle clearing Fbo
    fbo_rectangle = ObjectProperty(None)

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

        self.texture = self.fbo.texture

    def on_pos(self, *args):
        self.fbo_translation.x = -self.x
        self.fbo_translation.y = -self.y

    def on_size(self, *args):
        self.fbo.size = self.size
        self.fbo_rectangle.size = self.size
        self.texture = self.fbo.texture

    def update_glsl(self, *largs):
        self.canvas['time'] = Clock.get_boottime()
        self.canvas['resolution'] = map(float, self.size)

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


if __name__ == "__main__":
    from kivy.uix.image import Image

    class EffectApp(App):
        def build(self):
            # create our widget tree
            root = FloatLayout()
            sw = EffectWidget()
            root.add_widget(sw)

            sw.fs = plasma_shader

            sw.add_widget(Image(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
                                source='colours.png', allow_stretch=True,
                                keep_ratio=False))

            # add a button and scatter image inside the shader widget
            btn = Button(text='Hello world', size_hint=(None, None),
                         pos_hint={'center_x': .25, 'center_y': .5})
            sw.add_widget(btn)

            center = Window.width * 0.75 - 256, Window.height * 0.5 - 256

            return root

    EffectApp().run()
