from kivy.app import App
from inkcanvas import InkCanvas
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
import inkcanvas

class InkCanvasTest(App):
    title = 'InkCanvas'
    inkc = InkCanvas()
    
    def callback(self, instance):
        if self.inkc.mode == InkCanvas.Mode.draw:
            self.inkc.mode = InkCanvas.Mode.erase
        elif self.inkc.mode == InkCanvas.Mode.erase:
            self.inkc.mode = InkCanvas.Mode.draw

    def build(self):
        layout = BoxLayout(orientation = 'vertical')
        btn = Button(text='Change Mode', size_hint = (1,.15))
        btn.bind(on_press=self.callback)
        layout.add_widget(btn)
        layout.add_widget(self.inkc)
        return layout
    
    def on_pause(self):
        return True

if __name__ == '__main__':
    InkCanvasTest().run()