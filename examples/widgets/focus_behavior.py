from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.behaviors import FocusBehavior


class FocusButton(FocusBehavior, Button):
    '''A button, which when focused, turns red and sets the keyboard
    input to the text of the button.
    '''

    def on_focused(self, instance, value, *largs):
        self.background_color = [1, 0, 0, 1] if value else [1, 1, 1, 1]

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        '''We call super before doing anything else to enable tab cycling
        by FocusBehavior. If we wanted to use tab for ourselves, we could just
        not call it, or call it if we didn't need tab.
        '''
        if super(FocusButton, self).keyboard_on_key_down(window, keycode,
                                                         text, modifiers):
            return True
        self.text = keycode[1]
        return True


class FocusApp(App):

    def build(self):
        root = BoxLayout()
        self.grid1 = grid1 = GridLayout(cols=4)
        self.grid2 = grid2 = GridLayout(cols=4)
        root.add_widget(grid1)
        root.add_widget(grid2)

        for i in range(40):
            grid1.add_widget(FocusButton(text='l' + str(i)))
        for i in range(40):
            grid2.add_widget(FocusButton(text='r' + str(i)))

        # make elements 29, 9 un-focusable. The widgets are displayed in
        # reverse order, so 9 = 39 - 10
        grid2.children[10].is_focusable = False
        grid2.children[30].is_focusable = False
        # similarly, make 39 - 14 = 25, and 5 un-focusable
        grid1.children[14].is_focusable = False
        grid1.children[34].is_focusable = False

        # exchange the links between the sides so that it'll skip to the other
        # side in the middle. Remember that children are displayed reversed
        # in layouts.
        grid1.children[10].link_focus(next=grid2.children[9])
        grid2.children[10].link_focus(next=grid1.children[9])

        # autopopulate the rest, and complete the loop
        FocusBehavior.autopopulate_focus(grid1, previous=grid2.children[-1])
        # autopopulate the rest
        FocusBehavior.autopopulate_focus(grid2)
        # but now complete the loop directly, children[0] is the last element
        grid2.children[0].link_focus(next=grid1.children[-1])
        return root


if __name__ == '__main__':
    FocusApp().run()
