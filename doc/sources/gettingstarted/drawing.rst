Drawing
-------

graphics instructions, canvas

Each widget has a canvas, that is, a place to draw on. The canvas is a group of instructions that are executed whenever needed to keep the widget representation up to date. You can add two types of instructions to the canvas, context instructions and vertex instructions. You can put instructions either from python or from kv. If you add them from kv, the advantage is that they are automatically updated when any property they depend on change, in python, you need to do this yourself.

python:

class MyWidget(Widget):
    def __init__(self, \*args):
        super(MyWidget, self).__init__(\*args)
        self.bind(pos=self.update_canvas)
        self.bind(size=self.update_canvas)
        self.update_canvas()

    def update_canvas(self, \*args):
        self.clear_canvas() # need to reset everything
        with self.canvas:
            Color(0.5, 0.5, 0.5, 0.5) # context instruction
            Rectangle(self.pos, self.size) # vertex instruction

However, doing all that in kv is just:

MyWidget:
    canvas:
        Color:
            rgba: 0.5, 0.5, 0.5. 0.5
        Rectangle:
            pos: self.pos
            size: self.size

Much easier, right? :)

Oh about canvas, I omitted that it's actually three groups of instuctions. 

canvas.before
canvas
canvas.after

They work the same but this allows you to seperate your instructions based on when you want each to happen.
