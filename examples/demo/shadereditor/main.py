'''
Live Shader Editor
==================

This provides a live editor for vertex and fragment editors.
You should see a window with two editable panes on the left
and a large kivy logo on the right.The top pane is the
Vertex shader and the bottom is the Fragment shader. The file shadereditor.kv
describes the interface.

On each keystroke to either shader, declarations are added and the shaders
are compiled. If there are no errors, the screen is updated. Otherwise,
the error is visible as logging message in your terminal.
'''


import sys
import kivy
kivy.require('1.0.6')

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.graphics import RenderContext
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock

fs_header = '''
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0;

/* custom one */
uniform vec2 resolution;
uniform float time;
'''

vs_header = '''
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs to the fragment shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* vertex attributes */
attribute vec2     vPosition;
attribute vec2     vTexCoords0;

/* uniform variables */
uniform mat4       modelview_mat;
uniform mat4       projection_mat;
uniform vec4       color;
'''


class ShaderViewer(FloatLayout):
    fs = StringProperty(None)
    vs = StringProperty(None)

    def __init__(self, **kwargs):
        self.canvas = RenderContext()
        super(ShaderViewer, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_shader, 0)

    def update_shader(self, *args):
        s = self.canvas
        s['projection_mat'] = Window.render_context['projection_mat']
        s['time'] = Clock.get_boottime()
        s['resolution'] = list(map(float, self.size))
        s.ask_update()

    def on_fs(self, instance, value):
        self.canvas.shader.fs = value

    def on_vs(self, instance, value):
        self.canvas.shader.vs = value

Factory.register('ShaderViewer', cls=ShaderViewer)


class ShaderEditor(FloatLayout):

    source = StringProperty('data/logo/kivy-icon-512.png')

    fs = StringProperty('''
void main (void){
    gl_FragColor = frag_color * texture2D(texture0, tex_coord0);
}
''')
    vs = StringProperty('''
void main (void) {
  frag_color = color;
  tex_coord0 = vTexCoords0;
  gl_Position = projection_mat * modelview_mat * vec4(vPosition.xy, 0.0, 1.0);
}
''')

    viewer = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ShaderEditor, self).__init__(**kwargs)
        self.test_canvas = RenderContext()
        s = self.test_canvas.shader
        self.trigger_compile = Clock.create_trigger(self.compile_shaders, -1)
        self.bind(fs=self.trigger_compile, vs=self.trigger_compile)

    def compile_shaders(self, *largs):
        print('try compile')
        if not self.viewer:
            return
        fs = fs_header + self.fs
        vs = vs_header + self.vs
        print('-->', fs)
        self.viewer.fs = fs
        print('-->', vs)
        self.viewer.vs = vs


class ShaderEditorApp(App):
    def build(self):
        kwargs = {}
        if len(sys.argv) > 1:
            kwargs['source'] = sys.argv[1]
        return ShaderEditor(**kwargs)

if __name__ == '__main__':
    ShaderEditorApp().run()
