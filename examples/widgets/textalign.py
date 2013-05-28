from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty


class BoundedLabel(Label):
    pass


class Selector(FloatLayout):
    app = ObjectProperty(None)
    grid = ObjectProperty(None)


class TextAlignApp(App):

    def select(self, case):
        for _child in self.selector.grid.children[:]:
            self.selector.grid.remove_widget(_child)
        for valign in ('bottom', 'middle', 'top'):
            for halign in ('left', 'center', 'right'):
                label = BoundedLabel(text='V: %s\nH: %s' % (valign, halign),
                               size_hint=(None, None),
                               size=(150, 150),
                               halign=halign, valign=valign)
                if case == 0:
                    label.text_size = (None, None)
                elif case == 1:
                    label.text_size = (label.width, None)
                elif case == 2:
                    label.text_size = (None, label.height)
                else:
                    label.text_size = label.size
                self.selector.grid.add_widget(label)

        self.selector.grid.bind(minimum_size=self.selector.grid.setter('size'))

    def build(self):
        self.root = FloatLayout()
        self.selector = Selector(app=self)
        self.root.add_widget(self.selector)
        self.grid = None
        self.select(0)
        return self.root


TextAlignApp().run()
