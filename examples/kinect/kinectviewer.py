import freenect
from time import sleep
from threading import Thread
from collections import deque
from kivy.app import App
from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty
from kivy.graphics import RenderContext, Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.boxlayout import BoxLayout


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
uniform vec2 size;
'''

hsv_func = '''
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

points_kinect = fragment_header + hsv_func + '''
void main (void) {
    // threshold used to reduce the depth (better result)
    const int th = 5;

    // size of a square
    int square = floor(depth_range);

    // number of square on the display
    vec2 count = size / square;

    // current position of the square
    vec2 pos = floor(tex_coord0.xy * count) / count;

    // texture step to pass to another square
    vec2 step = 1 / count;

    // texture step to pass to another pixel
    vec2 pxstep = 1 / size;

    // center of the square
    vec2 center = pos + step / 2.;

    // calculate average of every pixels in the square
    float s = 0, x, y;
    for (x = 0; x < square; x++) {
        for (y = 0; y < square; y++) {
            s += texture2D(texture0, pos + pxstep * vec2(x,y)).r;
        }
    }
    float v = s / (square * square);

    // threshold the value
    float dr = th / 10.;
    v = min(v, dr) / dr;

    // calculate the distance between the center of the square and current pixel
    // display the pixel only if the distance is inside the circle
    float vdist = length(abs(tex_coord0 - center) * size / square);
    float value = 1 - v;
    if ( vdist < value ) {
        vec3 col = HSVtoRGB(vec3(value, 1., 1.));
        gl_FragColor = vec4(col, 1);
    }
}
'''
hsv_kinect = fragment_header + hsv_func + '''
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
        self.index = 0

    def run(self):
        q = self.queue
        while not self.quit:
            depths = freenect.sync_get_depth(index=self.index)
            if depths is None:
                sleep(2)
                continue
            q.appendleft(depths)

    def pop(self):
        return self.queue.pop()


class KinectViewer(Widget):

    depth_range = NumericProperty(7.7)

    shader = StringProperty("rgb")

    index = NumericProperty(0)

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

    def on_index(self, instance, value):
        self.kinect.index = value

    def on_shader(self, instance, value):
        if value == 'rgb':
            self.canvas.shader.fs = rgb_kinect
        elif value == 'hsv':
            self.canvas.shader.fs = hsv_kinect
        elif value == 'points':
            self.canvas.shader.fs = points_kinect

    def update_transformation(self, *largs):
        # update projection mat and uvsize
        self.canvas['projection_mat'] = Window.render_context['projection_mat']
        self.canvas['depth_range'] = self.depth_range
        self.canvas['size'] = list(map(float, self.size))
        try:
            value = self.kinect.pop()
        except:
            return
        f = value[0].astype('ushort') * 32
        self.texture.blit_buffer(
            f.tostring(), colorfmt='luminance', bufferfmt='ushort')
        self.canvas.ask_update()


class KinectViewerApp(App):

    def build(self):
        root = BoxLayout(orientation='vertical')

        self.viewer = viewer = KinectViewer(
            index=self.config.getint('kinect', 'index'),
            shader=self.config.get('shader', 'theme'))
        root.add_widget(viewer)

        toolbar = BoxLayout(size_hint=(1, None), height=50)
        root.add_widget(toolbar)

        slider = Slider(min=1., max=32., value=1.)

        def update_depth_range(instance, value):
            viewer.depth_range = value

        slider.bind(value=update_depth_range)
        toolbar.add_widget(slider)

        return root

    def build_config(self, config):
        config.add_section('kinect')
        config.set('kinect', 'index', '0')
        config.add_section('shader')
        config.set('shader', 'theme', 'rgb')

    def build_settings(self, settings):
        settings.add_json_panel('Kinect Viewer', self.config, data='''[
            { "type": "title", "title": "Kinect" },
            { "type": "numeric", "title": "Index",
              "desc": "Kinect index, from 0 to X",
              "section": "kinect", "key": "index" },
            { "type": "title", "title": "Shaders" },
            { "type": "options", "title": "Theme",
              "desc": "Shader to use for a specific visualization",
              "section": "shader", "key": "theme",
              "options": ["rgb", "hsv", "points"]}
        ]''')

    def on_config_change(self, config, section, key, value):
        if config is not self.config:
            return
        token = (section, key)
        if token == ('kinect', 'index'):
            self.viewer.index = int(value)
        elif token == ('shader', 'theme'):
            if value == 'rgb':
                self.viewer.canvas.shader.fs = rgb_kinect
            elif value == 'hsv':
                self.viewer.shader = value

if __name__ == '__main__':
    KinectViewerApp().run()
