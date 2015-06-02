from kivy.app import App
from inkcanvas import InkCanvasBehavior
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle

from functools import partial
  
class InkCanvasFloat(InkCanvasBehavior, FloatLayout):
    def __init__(self, **kwargs):
        super(InkCanvasFloat, self).__init__(**kwargs)
  
class InkCanvasTest(App):
    title = 'InkCanvas'

    def callback(self, button, result, *args):
        if self.inkc.mode == InkCanvasBehavior.Mode.draw:
            self.inkc.mode = InkCanvasBehavior.Mode.erase
            button.text = 'Erase Mode'
        elif self.inkc.mode == InkCanvasBehavior.Mode.erase:
            self.inkc.mode = InkCanvasBehavior.Mode.draw
            button.text = 'Draw Mode'

    def build(self):
        self.inkc = inkc = InkCanvasFloat()
        inkc.bind(size=self._update_rect, pos = self._update_rect)
        btn = Button(text='Change Mode', size_hint = (1,.15))
        btn.bind(on_press=partial(self.callback, btn))
        inkc.add_widget(btn)
        with inkc.canvas.before:
            Color(1,1,1,1)
            self.rect = Rectangle(size = inkc.size, pos = inkc.pos)
        return inkc
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
      
    def on_pause(self):
        return True
  
if __name__ == '__main__':
    InkCanvasTest().run()