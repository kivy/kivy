from kivy.app import App
from kivy.uix.combobox import ComboBox
from kivy.uix.floatlayout import FloatLayout

class ComboBoxTest(App):

    def build(self):
        f = FloatLayout()
        c = ComboBox(
                values=['a', 'b', 'c', 'd'],
                pos_hint={'center_x': .5, 'center_y': .7},
                size_hint=(None, None),
                size=(200, 40),
                selected_color=(1, .2, .2, 1))

        c.bind(text=self.text_changed,
               current_index=self.index_changed,
               highlight_index=self.on_highlight)

        f.add_widget(c)
        return f

    def text_changed(self, instance, value):
        print 'Text changed: %s' % value

    def index_changed(self, instance, value):
        print 'Index changed: %d' % value

    def on_highlight(self, instance, value):
        print 'On Highlight: %s' % value


if __name__ in ('__android__', '__main__'):
    ComboBoxTest().run()
