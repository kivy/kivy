from kivy.uix.button import Button
from kivy.uix.stencilview import StencilView
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from random import random as r
from functools import partial


class StencilTestWidget(StencilView):
    '''Drag to define stencil area
    '''
    def __init__(self, **kwargs):
        super(StencilTestWidget, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        self.pos = touch.pos
        self.size = (1,1)

    def on_touch_move(self, touch):
        self.size = (touch.x-touch.ox, touch.y-touch.oy)


class StencilCanvasApp(App):

    def add_rects(self, label, wid, count, *largs):
        label.text = str(int(label.text) + count)
        with wid.canvas:
            for x in xrange(count):
                Color(r(), 1, 1, mode='hsv')
                Rectangle(pos=(r() * wid.width + wid.x,
                               r() * wid.height + wid.y), size=(10,10))

    def reset_stencil(self, wid, *largs):
        wid.pos = (0,0)
        wid.size = Window.size

    def reset_rects(self, label, wid, *largs):
        label.text = '0'
        wid.canvas.clear()

    def build(self):
        wid = StencilTestWidget()

        label = Label(text='0')

        btn_add500 = Button(text='+ 200 rects')
        btn_add500.bind(on_press=partial(self.add_rects, label, wid, 200))

        btn_reset = Button(text='Reset Rectangles')
        btn_reset.bind(on_press=partial(self.reset_rects, label, wid))

        btn_stencil = Button(text='Reset Stencil')
        btn_stencil.bind(on_press=partial(self.reset_stencil, wid))

        layout = BoxLayout(size_hint=(1, None), height=50)
        layout.add_widget(btn_add500)
        layout.add_widget(btn_reset)
        layout.add_widget(btn_stencil)
        layout.add_widget(label)

        root = BoxLayout(orientation='vertical')
        root.add_widget(wid)
        root.add_widget(layout)

        return root

if __name__ == '__main__':
    StencilCanvasApp().run()
