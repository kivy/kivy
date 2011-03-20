from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.uix.treeview import TreeView, TreeViewLabel


class ShowcaseApp(App):

    def on_select_node(self, instance, value):
        self.content.clear_widgets()
        value = value['widget'].text
        w = getattr(self, 'show_%s' % value.lower().replace(' ', '_'))()
        self.content.add_widget(w)

    def build(self):
        root = BoxLayout(orientation='horizontal', padding=20, spacing=20)
        tree = TreeView(size_hint=(None, 1), width=200)
        tree.root['widget'].text = 'Widget list'
        tree.bind(selected_node=self.on_select_node)
        tree.add_node(TreeViewLabel(text='Buttons'))
        tree.add_node(TreeViewLabel(text='Toggle Buttons'))
        tree.add_node(TreeViewLabel(text='Sliders'))
        tree.add_node(TreeViewLabel(text='Textinput'))
        root.add_widget(tree)
        self.content = content = BoxLayout()
        root.add_widget(content)
        return root

    def show_buttons(self):
        col = BoxLayout(spacing=10)
        col.add_widget(Button(text='Hello world'))
        col.add_widget(Button(text='Hello world', state='down'))
        return col

    def show_toggle_buttons(self):
        col = BoxLayout(spacing=10)
        col.add_widget(ToggleButton(text='Option 1', group='t1'))
        col.add_widget(ToggleButton(text='Option 2', group='t1'))
        col.add_widget(ToggleButton(text='Option 3', group='t1'))
        return col

    def show_sliders(self):
        col = BoxLayout(spacing=10)
        vbox = BoxLayout(orientation='vertical', spacing=10)
        col.add_widget(vbox)
        vbox.add_widget(Slider())
        vbox.add_widget(Slider(value=50))
        hbox = BoxLayout(spacing=10)
        col.add_widget(hbox)
        hbox.add_widget(Slider(orientation='vertical'))
        hbox.add_widget(Slider(orientation='vertical', value=50))
        return col

    def show_textinput(self):
        return TextInput()


if __name__ == '__main__':
    ShowcaseApp().run()
