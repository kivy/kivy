from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle

class Touchdebug(Widget):
    def on_touch_down(self, touch):
        win = self.get_parent_window()
        ud = touch.userdata
        with self.canvas:
            ud['color'] = Color(1, 1, 1)
            ud['lines'] = (
                Rectangle(pos=(touch.x, 0), size=(1, win.height)),
                Rectangle(pos=(0, touch.y), size=(win.width, 1)))

        ud['label'] = Label()
        self.update_touch_label(ud['label'], touch)
        self.add_widget(ud['label'])

    def on_touch_move(self, touch):
        ud = touch.userdata
        ud['lines'][0].pos = touch.x, 0
        ud['lines'][1].pos = 0, touch.y
        ud['label'].pos = touch.pos
        self.update_touch_label(ud['label'], touch)

    def on_touch_up(self, touch):
        ud = touch.userdata
        self.canvas.remove(ud['color'])
        self.canvas.remove(ud['lines'][0])
        self.canvas.remove(ud['lines'][1])
        self.remove_widget(ud['label'])

    def update_touch_label(self, label, touch):
        label.text = 'ID: %s\nPos: (%d, %d)\nClass: %s' % (
            touch.id,
            touch.x,
            touch.y,
            touch.__class__.__name__
        )
        label.pos = touch.pos
        label.size = label.texture_size[0] + 20, label.texture_size[1] + 20


class TouchdebugApp(App):
    def build(self):
        return Touchdebug()

if __name__ == '__main__':
    TouchdebugApp().run()
