from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.behaviors import CompoundSelectionBehavior
from kivy.uix.behaviors import FocusBehavior
from kivy.app import runTouchApp
from kivy.core.window import Window


class SelectableGrid(FocusBehavior, CompoundSelectionBehavior, GridLayout):

    def __init__(self, **kwargs):
        super(SelectableGrid, self).__init__(**kwargs)

        def print_selection(*l):
            print('selected: ', [x.text for x in self.selected_nodes])
        self.bind(selected_nodes=print_selection)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        if super(SelectableGrid, self).keyboard_on_key_down(
            window, keycode, text, modifiers):
            return True
        if self.select_with_key_down(window, keycode, text, modifiers):
            return True
        return False

    def keyboard_on_key_up(self, window, keycode):
        if super(SelectableGrid, self).keyboard_on_key_up(window, keycode):
            return True
        if self.select_with_key_up(window, keycode):
            return True
        return False

    def goto_node(self, key, last_node, last_node_idx):
        ''' This function is used to go to the node by typing the number
        of the text of the button.
        '''
        node, idx = super(SelectableGrid, self).goto_node(key, last_node,
                                                          last_node_idx)
        if node != last_node:
            return node, idx

        items = list(enumerate(self.get_selectable_nodes()))
        '''If self.nodes_order_reversed (the default due to using
        self.children which is reversed), the index is counted from the
        starts of the selectable nodes, like normal but the nodes are traversed
        in the reverse order.
        '''
        # start searching after the last selected node
        if not self.nodes_order_reversed:
            items = items[last_node_idx + 1:] + items[:last_node_idx + 1]
        else:
            items = items[:last_node_idx][::-1] + items[last_node_idx:][::-1]

        for i, child in items:
            if child.text.startswith(key):
                return child, i
        return node, idx


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


root = SelectableGrid(cols=5, up_count=5, multiselect=True, scroll_count=1)
for i in range(40):
    c = Button(text=str(i))
    c.bind(on_touch_down=root.do_touch)
    root.add_widget(c)

runTouchApp(root)
