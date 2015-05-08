'''
Demonstrates using kv language to create some simple buttons and a
label, with each button modifying the label text.
'''

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

Builder.load_string('''
<MainWidget>:
    BoxLayout:
        orientation: 'vertical'
        Button:
            text: 'some string '
            on_press: the_right_pane.text += self.text
        Button:
            text: 'one two three four '
            on_press: the_right_pane.text += self.text
        Button:
            text: 'follow the yellow brick road '
            on_press: the_right_pane.text += self.text
        Button:
            text: 'five six seven eight '
            on_press: the_right_pane.text += self.text
        Button:
            text: 'CLEAR LABEL'
            on_press: the_right_pane.text = ''
    Label:
        id: the_right_pane
        text: ''
        text_size: self.size
        halign: 'center'
        valign: 'middle'
''')


class MainWidget(BoxLayout):
    pass


class ExampleApp(App):
    def build(self):
        return MainWidget()

ExampleApp().run()

