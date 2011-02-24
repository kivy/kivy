import freenect
from threading import Thread
from collections import deque
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.graphics import RenderContext, Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

fragment_header = '''
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0;

/* custom input */
uniform float depth_range;
'''

rgb_kinect = fragment_header + '''
void main (void) {
    float value = texture2D(texture0, tex_coord0).r;
    value = mod(value * depth_range, 1.);
    vec3 col = vec3(0., 0., 0.);
    if ( value <= 0.33 )
        col.r = clamp(value, 0., 0.33) * 3.;
    if ( value <= 0.66 )
        col.g = clamp(value - 0.33, 0., 0.33) * 3.;
    col.b = clamp(value - 0.66, 0., 0.33) * 3.;
    gl_FragColor = vec4(col, 1.);
}
'''

hsv_kinect = fragment_header + '''
vec3 HSVtoRGB(vec3 color) {
    float f,p,q,t, hueRound;
    int hueIndex;
    float hue, saturation, v;
    vec3 result;

    /* just for clarity */
    hue = color.r;
    saturation = color.g;
    v = color.b;

    hueRound = floor(hue * 6.0);
    hueIndex = mod(int(hueRound), 6.);
    f = (hue * 6.0) - hueRound;
    p = v * (1.0 - saturation);
    q = v * (1.0 - f*saturation);
    t = v * (1.0 - (1.0 - f)*saturation);

    switch(hueIndex) {
        case 0:
            result = vec3(v,t,p);
        break;
        case 1:
            result = vec3(q,v,p);
        break;
        case 2:
            result = vec3(p,v,t);
        break;
        case 3:
            result = vec3(p,q,v);
        break;
        case 4:
            result = vec3(t,p,v);
        break;
        case 5:
            result = vec3(v,p,q);
        break;
    }
    return result;
}

void main (void) {
    float value = texture2D(texture0, tex_coord0).r;
    value = mod(value * depth_range, 1.);
    vec3 col = HSVtoRGB(vec3(value, 1., 1.));
    gl_FragColor = vec4(col, 1.);
}
'''


class KinectDepth(Thread):
    def __init__(self, *largs, **kwargs):
        super(KinectDepth, self).__init__(*largs, **kwargs)
        self.daemon = True
        self.queue = deque()
        self.quit = False

    def run(self):
        q = self.queue
        while not self.quit:
            depths = freenect.sync_get_depth()
            if depths is None:
                continue
            q.appendleft(depths)

    def pop(self):
        return self.queue.pop()

class KinectViewer(Widget):

    depth_range = NumericProperty(1.)

    def __init__(self, **kwargs):
        # change the default canvas to RenderContext, we can change the shader
        self.canvas = RenderContext()
        self.canvas.shader.fs = hsv_kinect

        # add kinect depth provider, and start the thread
        self.kinect = KinectDepth()
        self.kinect.start()

        # parent init
        super(KinectViewer, self).__init__(**kwargs)

        # allocate texture for pushing depth
        self.texture = Texture.create(
            size=(640, 480), colorfmt='luminance', bufferfmt='ushort')
        self.texture.flip_vertical()

        # create default canvas element
        with self.canvas:
            Color(1, 1, 1)
            Rectangle(size=Window.size, texture=self.texture)

        # add a little clock to update our glsl
        Clock.schedule_interval(self.update_transformation, 0)

    def update_transformation(self, *largs):
        # update projection mat and uvsize
        self.canvas['projection_mat'] = Window.render_context['projection_mat']
        self.canvas['depth_range'] = self.depth_range
        try:
            value = self.kinect.pop()
        except:
            return
        f = value[0].astype('ushort') * 32
        self.texture.blit_buffer(
            f.tostring(), colorfmt='luminance', bufferfmt='ushort')


class KinectViewerApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')

        viewer = KinectViewer()
        root.add_widget(viewer)

        toolbar = BoxLayout(size_hint=(1, None), height=50)
        root.add_widget(toolbar)

        slider = Slider(min=1., max=10., value=1.)
        def update_depth_range(instance, value):
            viewer.depth_range = value
        slider.bind(value=update_depth_range)
        toolbar.add_widget(slider)

        button = Button(text='Use RGB shader')
        def use_rgb(*l):
            viewer.canvas.shader.fs = rgb_kinect
        button.bind(on_press=use_rgb)
        toolbar.add_widget(button)

        button = Button(text='Use HSV shader')
        def use_hsv(*l):
            viewer.canvas.shader.fs = hsv_kinect
        button.bind(on_press=use_hsv)
        toolbar.add_widget(button)

        return root

if __name__ == '__main__':
    KinectViewerApp().run()
