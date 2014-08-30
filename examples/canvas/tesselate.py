from kivy.app import App
from kivy.graphics import Mesh, Color
from kivy.graphics.tesselator import Tesselator, WINDING_ODD, TYPE_POLYGONS
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder

Builder.load_string("""
<ShapeBuilder>:
    BoxLayout:
        size_hint_y: None
        height: "48dp"
        spacing: "2dp"
        padding: "2dp"

        ToggleButton:
            text: "Debug"
            id: debug
            on_release: root.build()
        Button:
            text: "New shape"
            on_release: root.push_shape()
        Button:
            text: "Build"
            on_release: root.build()
        Button:
            text: "Reset"
            on_release: root.reset()

    BoxLayout:
        size_hint_y: None
        height: "48dp"
        top: root.top
        spacing: "2dp"
        padding: "2dp"
        Label:
            id: status
            text: "Status"
""")


class ShapeBuilder(FloatLayout):
    def __init__(self, **kwargs):
        super(ShapeBuilder, self).__init__(**kwargs)
        self.shapes = [
            [0, 0,   200, 0,  200, 200, 0, 200],
            [50, 50, 150, 50, 150, 150, 50, 150]
        ]
        self.shape = []
        self.build()

    def on_touch_down(self, touch):
        if super(ShapeBuilder, self).on_touch_down(touch):
            return True
        print touch.pos
        self.shape.extend(touch.pos)
        self.build()
        return True

    def on_touch_move(self, touch):
        if super(ShapeBuilder, self).on_touch_move(touch):
            return True
        print touch.pos
        self.shape.extend(touch.pos)
        self.build()
        return True

    def on_touch_up(self, touch):
        if super(ShapeBuilder, self).on_touch_up(touch):
            return True
        print "TOUCH UP"
        self.push_shape()
        self.build()

    def push_shape(self):
        self.shapes.append(self.shape)
        self.shape = []

    def build(self):
        print "build()"
        tess = Tesselator()
        count = 0
        for shape in self.shapes:
            if len(shape) >= 3:
                tess.add_contour(shape)
                count += 1
        if self.shape and len(self.shape) >= 3:
            tess.add_contour(self.shape)
            count += 1
        if not count:
            return
        print "Tesselate", count, "shapes"
        ret = tess.tesselate(WINDING_ODD, TYPE_POLYGONS)
        print "Result:", ret
        print "Vertex count:", tess.vertex_count
        print "Element count:", tess.element_count

        self.canvas.after.clear()

        debug = self.ids.debug.state == "down"
        if debug:
            from random import random
            with self.canvas.after:
                c = 0
                for vertices in tess.meshes:
                    Color(c, 1, 1, mode="hsv")
                    c += 0.5
                    indices = [0]
                    for i in range(1, len(vertices) / 4):
                        if i > 0:
                            indices.append(i)
                        indices.append(i)
                        indices.append(0)
                        indices.append(i)
                    indices.pop(-1)
                    Mesh(vertices=vertices, indices=indices, mode="lines")
        else:
            with self.canvas.after:
                Color(1, 1, 1, 1)
                for vertices in tess.meshes:
                    indices = range(len(vertices) / 4)
                    Mesh(vertices=vertices, indices=indices, mode="triangle_fan")

        self.ids.status.text = "Vertex: {} - Elements: {}".format(
            tess.vertex_count, tess.element_count)

    def reset(self):
        self.shapes = []
        self.shape = []
        self.canvas.after.clear()



class TessApp(App):
    def build(self):
        """
        tess = Tesselator()
        tess.add_contour([0, 0, 200, 0, 200, 200, 0, 200])
        tess.add_contour([50, 50, 150, 50, 150, 150, 50, 150])
        print tess.tesselate(WINDING_ODD, TYPE_POLYGONS)
        print "Vertex count:", tess.vertex_count
        print "Element count:", tess.element_count
        print tess.meshes

        root = Widget()
        with root.canvas:
            Color(1, 1, 1, 1)
            for vertices in tess.meshes:
                indices = range(len(vertices) / 4)
                print list(vertices), list(indices)
                Mesh(vertices=vertices, indices=indices, mode="triangle_fan")

        return root
        """
        return ShapeBuilder()

TessApp().run()
