'''
Example usage of the effectwidget.

Currently highly experimental.
'''

from kivy.app import App
from kivy.uix.effectwidget import EffectWidget, shader_header, shader_uniforms
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scatter import Scatter
from kivy.uix.button import Button

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

class EffectApp(App):
    def build(self):
        # create our widget tree
        root = FloatLayout()
        sw = EffectWidget()
        root.add_widget(sw)

        sw.fs = plasma_shader

        sw.add_widget(Image(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
                            source='data/logo/kivy-icon-512.png', allow_stretch=True,
                            keep_ratio=False))

        # add a button and scatter image inside the shader widget
        btn = Button(text='Hello world', size_hint=(None, None),
                     pos_hint={'center_x': .25, 'center_y': .5})
        sw.add_widget(btn)

        return root

EffectApp().run()
