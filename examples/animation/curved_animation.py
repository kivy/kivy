'''
Widget curved-path animation
================

This example demonstrates animation along a curved path.
''' 

import math

from kivy.animation import AnimationTransition
from kivy.clock import Clock

CONSTANT = 10e-10

class HorizontalSemiEllipse:
    """
    Usage: Horizontal semi-ellipse animation.
    Parameters:
    - widget: Widget.
    - vertex_width: Maximum width the parabolic path attains.
    - height: Determines the end position, i.e., [widget.x, height].
    """

    def __init__(
        self, widget, vertex_width, height, on_complete=None, transition="linear"
    ):
        self.on_complete = on_complete
        self.widget = widget
        vertex_height = height / 2 + widget.y
        vertex_width = vertex_width + widget.x
        self.total_height = height + widget.y
        self.initial_y = widget.y
        a = (widget.x - vertex_width) / ((widget.y - vertex_height) ** 2)
        self.x = lambda y: a * ((y - vertex_height) ** 2) + vertex_width
        self.time = 0
        self.transition = transition
        if hasattr(widget, "angle"):
            self.initial_angle = widget.angle

    def set_pos(self, frame):
        if self.widget.y >= self.total_height:
            self.event.cancel()
            if self.on_complete:
                self.on_complete()
        self.time += frame
        t = getattr(AnimationTransition, self.transition)(min(1.0, self.time / self.d))
        self.widget.y = (self.initial_y * (1.0 - t)) + (self.total_height * t)
        self.widget.x = self.x(self.widget.y)
        if hasattr(self, "initial_angle"):
            self.widget.angle = self.initial_angle + math.atan(
                (self.x(self.widget.y - CONSTANT) - self.widget.x) / (CONSTANT)
            ) / (math.pi / 180)

    def start(self, d=2):
        """ 
        Parameters:
            d: total duration of animation
        """
        self.d = d
        self.event = Clock.schedule_interval(lambda _: self.set_pos(_), 0)
        
if __name__ == "__main__":
    from kivy.app import App
    from kivy.lang import Builder
    from kivy.metrics import dp
    from kivy.clock import Clock

    class TestApp(App):
        def build(self):
            return Builder.load_string(
                """ 
FloatLayout: 
    Widget:
        size_hint:None, None
        pos:[0,0]
        size:[dp(50), dp(50)]
        angle:0
        canvas:
            Color:
                rgba:1,0,0,1 
            Rectangle:
                size:self.size 
                pos:self.pos
        # Optionally add angle support
        canvas.before:
            PushMatrix
            Rotate:
                angle:self.angle
                origin: self.center
        canvas.after:
            PopMatrix
    """
            )

        def on_start(self):
            Clock.schedule_once(
                lambda _: HorizontalSemiEllipse(
                    self.root.children[0], dp(100), dp(400), transition="in_out_circ"
                ).start(d=3),
                2,
            )


    TestApp().run()
