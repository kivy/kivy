'''
Multitexturing
==============
'''

from kivy.clock import Clock
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.graphics import RenderContext, Color, Rectangle, BindTexture


fs_multitexture = '''
$HEADER$

// New uniform that will receive texture at index 1
uniform sampler2D texture1;

void main(void) {

    // multiple current color with both texture (0 and 1).
    // currently, both will use exactly the same texture coordinates.
    gl_FragColor = frag_color * \
        texture2D(texture0, tex_coord0) * \
        texture2D(texture1, tex_coord0);
}
'''


class MultitextureWidget(Widget):

    def __init__(self, **kwargs):
        self.canvas = RenderContext()
        self.canvas.shader.fs = fs_multitexture
        with self.canvas:
            Color(1, 1, 1)

            # here, we are binding a custom texture at index 1
            # this will be used as texture1 in shader.
            BindTexture(source='mtexture2.png', index=1)

            # create a rectangle with texture (will be at index 0)
            Rectangle(size=(512, 512), source='mtexture1.png')

        # set the texture1 to use texture index 1
        self.canvas['texture1'] = 1

        # call the constructor of parent
        # if they are any graphics object, they will be added on our new canvas
        super(MultitextureWidget, self).__init__(**kwargs)

        # We'll update our glsl variables in a clock
        Clock.schedule_interval(self.update_glsl, 0)

    def update_glsl(self, *largs):
        # This is needed for the default vertex shader.
        self.canvas['projection_mat'] = Window.render_context['projection_mat']
        self.canvas['modelview_mat'] = Window.render_context['modelview_mat']


class MultitextureApp(App):

    def build(self):
        return MultitextureWidget()


if __name__ == '__main__':
    MultitextureApp().run()
