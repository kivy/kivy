from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty


class BoundedLabel(Label):
    pass


class Selector(FloatLayout):
    app = ObjectProperty(None)


class TextAlignApp(App):

    def select(self, case):
        grid = GridLayout(rows=3, cols=3, spacing=10, size_hint=(None, None),
                          pos_hint={'center_x': .5, 'center_y': .5})
        for valign in ('bottom', 'middle', 'top'):
            for halign in ('left', 'center', 'right'):
                label = BoundedLabel(text='V: %s\nH: %s' % (valign, halign),
                              size_hint=(None, None),
                              halign=halign, valign=valign)
                if case == 0:
                    label.text_size = (None, None)
                elif case == 1:
                    label.text_size = (label.width, None)
                elif case == 2:
                    label.text_size = (None, label.height)
                else:
                    label.text_size = label.size
                grid.add_widget(label)

        if self.grid:
            self.root.remove_widget(self.grid)
        grid.bind(minimum_size=grid.setter('size'))
        self.grid = grid
        self.root.add_widget(grid)

    def build(self):
        self.root = FloatLayout()
        self.selector = Selector(app=self)
        self.root.add_widget(self.selector)
        self.grid = None
        self.select(0)
        return self.root


TextAlignApp().run()
