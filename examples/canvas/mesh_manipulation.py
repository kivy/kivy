'''
Mesh Manipulation Example
=========================

This demonstrates creating a mesh and using it to deform the texture (the
kivy log). You should see the kivy logo with a five sliders to right.
The sliders change the mesh points' x and y offsets, radius, and a
'wobble' deformation's magnitude and speed.

This example is developed in gabriel's blog post at
http://kivy.org/planet/2014/01/kivy-image-manipulations-with-mesh-and-textures/
'''

from kivy.app import App
from kivy.lang import Builder
from kivy.core.image import Image as CoreImage
from kivy.properties import ListProperty, ObjectProperty, NumericProperty
from kivy.clock import Clock
from kivy.core.window import Window
from math import sin, cos, pi


kv = '''
BoxLayout:
    Widget:
        canvas:
            Color:
                rgba: 1, 1, 1, 1
            Mesh:
                vertices: app.mesh_points
                indices: range(len(app.mesh_points) // 4)
                texture: app.mesh_texture
                mode: 'triangle_fan'
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: None
        width: 100
        Slider:
            value: app.offset_x
            on_value: app.offset_x = args[1]
            min: -1
            max: 1
        Slider:
            value: app.offset_y
            on_value: app.offset_y = args[1]
            min: -1
            max: 1
        Slider:
            value: app.radius
            on_value: app.radius = args[1]
            min: 10
            max: 1000
        Slider:
            value: app.sin_wobble
            on_value: app.sin_wobble = args[1]
            min: -50
            max: 50
        Slider:
            value: app.sin_wobble_speed
            on_value: app.sin_wobble_speed = args[1]
            min: 0
            max: 50
            step: 1
'''


class MeshBallApp(App):
    mesh_points = ListProperty([])
    mesh_texture = ObjectProperty(None)
    radius = NumericProperty(500)
    offset_x = NumericProperty(.5)
    offset_y = NumericProperty(.5)
    sin_wobble = NumericProperty(0)
    sin_wobble_speed = NumericProperty(0)

    def build(self):
        self.mesh_texture = CoreImage('data/logo/kivy-icon-512.png').texture
        Clock.schedule_interval(self.update_points, 0)
        return Builder.load_string(kv)

    def update_points(self, *args):
        """ replace self.mesh_points based on current slider positions.
        Called continuously by a timer because this only sample code.
        """
        points = [Window.width / 2, Window.height / 2, .5, .5]
        i = 0
        while i < 2 * pi:
            i += 0.01 * pi
            points.extend([
                Window.width / 2 + cos(i) * (self.radius + self.sin_wobble
                                             * sin(i * self.sin_wobble_speed)),
                Window.height / 2 + sin(i) * (self.radius + self.sin_wobble
                                              * sin(i * self.sin_wobble_speed)),
                self.offset_x + sin(i),
                self.offset_y + cos(i)])

        self.mesh_points = points

if __name__ == '__main__':
    MeshBallApp().run()
