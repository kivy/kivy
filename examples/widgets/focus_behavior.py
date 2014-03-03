from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import FocusBehavior
from kivy.graphics import Color, Rectangle


class FocusWithColor(FocusBehavior):
    ''' Class that when focused, changes its background color to red.
    '''

    _color = None
    _rect = None

    def __init__(self, **kwargs):
        super(FocusWithColor, self).__init__(**kwargs)
        with self.canvas:
            self._color = Color(1, 1, 1, .2)
            self._rect = Rectangle(size=self.size, pos=self.pos)
            self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self._rect.pos = instance.pos
        self._rect.size = instance.size

    def on_focused(self, instance, value, *largs):
        self._color.rgba = [1, 0, 0, .2] if value else [1, 1, 1, .2]


class FocusLabel(FocusWithColor, Label):
    '''A label, which in addition to turn red when focused, it also sets the
    keyboard input to the text of the label.
    '''

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        '''We call super before doing anything else to enable tab cycling
        by FocusBehavior. If we wanted to use tab for ourselves, we could just
        not call it, or call it if we didn't need tab.
        '''
        if super(FocusLabel, self).keyboard_on_key_down(window, keycode,
                                                         text, modifiers):
            return True
        self.text = keycode[1]
        return True


class FocusGridLayout(FocusWithColor, GridLayout):
    pass


class FocusBoxLayout(FocusWithColor, BoxLayout):
    pass


class FocusApp(App):

    def build(self):
        root = FocusBoxLayout(padding=[10, 10], spacing=10)
        self.grid1 = grid1 = FocusGridLayout(cols=4, padding=[10, 10],
                                             spacing=10)
        self.grid2 = grid2 = FocusGridLayout(cols=4, padding=[10, 10],
                                             spacing=10)
        root.add_widget(FocusLabel(text='Left', size_hint_x=0.4))
        root.add_widget(grid1)
        root.add_widget(grid2)
        root.add_widget(FocusLabel(text='Right', size_hint_x=0.4))

        for i in range(40):
            grid1.add_widget(FocusLabel(text='l' + str(i)))
        for i in range(40):
            grid2.add_widget(FocusLabel(text='r' + str(i)))

        # make elements 29, 9 un-focusable. The widgets are displayed in
        # reverse order, so 9 = 39 - 10
        grid2.children[30].text = grid1.children[14].text =\
            grid2.children[15].text = grid1.children[34].text = 'Skip me'
        grid2.children[15].is_focusable = False
        grid2.children[30].is_focusable = False
        # similarly, make 39 - 14 = 25, and 5 un-focusable
        grid1.children[14].is_focusable = False
        grid1.children[34].is_focusable = False
        # don't move focus passed this element
        grid2.children[35].focus_next = StopIteration
        grid2.children[35].text = 'Stop forward'

        # exchange the links between the sides so that it'll skip to the other
        # side in the middle. Remember that children are displayed reversed
        # in layouts.
        grid1.children[10].focus_next = grid2.children[9]
        grid2.children[10].focus_next = grid1.children[9]
        grid1.children[10].text = '-->'
        grid2.children[10].text = '<--'
        return root


if __name__ == '__main__':
    FocusApp().run()
