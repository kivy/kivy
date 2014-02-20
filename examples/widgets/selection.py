from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.behaviors import SelectionBehavior
from kivy.app import runTouchApp
from kivy.core.window import Window


class SelectableGrid(SelectionBehavior, GridLayout):

    def __init__(self, **kwargs):
        super(SelectableGrid, self).__init__(**kwargs)
        keyboard = Window.request_keyboard(None, self)
        keyboard.bind(on_key_down=self.select_with_key_down,
                      on_key_up=self.select_with_key_up)

        def print_selection(*l):
            print [x.text for x in self.selected_nodes]
        self.bind(selected_nodes=print_selection)

    def select_node(self, node):
        node.background_color = (1, 0, 0, 1)
        return super(SelectableGrid, self).select_node(node)

    def deselect_node(self, node):
        node.background_color = (1, 1, 1, 1)
        super(SelectableGrid, self).deselect_node(node)

    def do_touch(self, instance, touch):
        if ('button' in touch.profile and touch.button in
            ('scrollup', 'scrolldown', 'scrollleft', 'scrollright')) or\
            instance.collide_point(*touch.pos):
            self.select_with_touch(instance, touch)
        else:
            return False
        return True


root = SelectableGrid(cols=5, up_count=5, multiselect=True,
                      keyboard_select=True)
for i in range(40):
    c = Button(text=str(i))
    c.bind(on_touch_down=root.do_touch)
    root.add_widget(c)

runTouchApp(root)
