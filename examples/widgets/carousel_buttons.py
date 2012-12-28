'''
Carousel example with button inside.
This is a tiny test for testing the scroll distance/timeout
And ensure the down/up are dispatched if no gesture is done.
'''
from kivy.uix.carousel import Carousel
from kivy.uix.gridlayout import GridLayout
from kivy.app import App
from kivy.lang import Builder

Builder.load_string('''
<Page>:
    cols: 3
    Label:
        text: str(id(root))
    Button
    Button
    Button
    Button
    Button
    Button
    Button
    Button
''')

class Page(GridLayout):
    pass

class TestApp(App):
    def build(self):
        root = Carousel()
        for x in range(10):
            root.add_widget(Page())
        return root

if __name__ == '__main__':
    TestApp().run()
