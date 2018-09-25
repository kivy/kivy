'''
Rotated Shader
=============

This shader example is a modified version of plasma.py that shows how to
rotate areas of fragment shaders bounded by vertex_instructions.
'''
from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.graphics import RenderContext
from kivy.properties import StringProperty
from kivy.uix.widget import Widget

# imported early for side effects needed for Shader
import kivy.core.window


shared_code = '''
$HEADER$

uniform float time;

vec4 tex(void)
{
   return frag_color * texture2D(texture0, tex_coord0);
}

float plasmaFunc(float n1, float n2, float n3, float n4)
{
   vec4 fPos = frag_modelview_mat * gl_FragCoord;
   return abs(sin(
                  sin(sin(fPos.x / n1) + time) +
                  sin(fPos.y / n2 + time) +
                  n4 * sin((fPos.x + fPos.y) / n3)));
}

'''


plasma_shader = shared_code + '''
void main(void)
{
   float green = plasmaFunc(40., 30., 100., 3.5);
   gl_FragColor = vec4(1.0, green, 1.0, 1.0) * tex();
}

'''


plasma_shader2 = shared_code + '''
void main(void)
{
   float red = plasmaFunc(30., 20., 10., .5);
   gl_FragColor = vec4(red, 1.0, 1.0, 1.0) * tex();
}

'''


class ShaderWidget(Widget):

    # property to set the source code for fragment shader
    fs = StringProperty(None)

    def __init__(self, **kwargs):
        # Instead of using Canvas, we will use a RenderContext,
        # and change the default fragment shader used.
        self.canvas = RenderContext(use_parent_projection=True,
                                    use_parent_modelview=True,
                                    use_parent_frag_modelview=True)

        # call the constructor of parent
        # if they are any graphics object, they will be added on our new canvas
        super(ShaderWidget, self).__init__(**kwargs)

        # We'll update our glsl variables in a clock
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def update_glsl(self, *largs):
        self.canvas['time'] = Clock.get_boottime()

    def on_fs(self, instance, value):
        # set the fragment shader to our source code
        shader = self.canvas.shader
        old_value = shader.fs
        shader.fs = value
        if not shader.success:
            shader.fs = old_value
            raise Exception('failed')


class RotatedApp(App):
    def build(self):
        main_widget = Factory.MainWidget()
        main_widget.fs = plasma_shader
        main_widget.mini.fs = plasma_shader2
        return main_widget


if __name__ == '__main__':
    RotatedApp().run()
