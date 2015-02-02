from kivy.uix.gridlayout import GridLayout
from kivy.app import App
from kivy.lang import Builder

Builder.load_string('''
<Demo>:
    cols: 1

    BoxLayout:
        orientation: 'vertical'
        Button:
            size_hint_x: 0.4
            pos_hint: {'x': 0}
            text: 'pos_hint: x=0'

        Button:
            size_hint_x: 0.2
            pos_hint: {'center_x': 0.5}
            text: 'pos_hint: center_x=0.5'

        Button:
            size_hint_x: 0.4
            pos_hint: {'right': 1}
            text: 'pos_hint: right=1'

    BoxLayout:
        Button:
            size_hint_y: 0.4
            pos_hint: {'y': 0}
            text: 'pos_hint: y=0'

        Button:
            size_hint_y: 0.2
            pos_hint: {'center_y': .5}
            text: 'pos_hint: center_y=0.5'

        Button:
            size_hint_y: 0.4
            pos_hint: {'top': 1}
            text: 'pos_hint: top=1'
''')


class Demo(GridLayout):
    pass


class DemoApp(App):
    def build(self):
        return Demo()

if __name__ == '__main__':
    DemoApp().run()
