from kivy.app import App
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout

class TestApp(App):
    def build(self):
        layout = GridLayout(rows=10,cols=10,spacing=20)
        for i in range(100):
            btn = Button(text=str(i))
            layout.add_widget(btn)

        root = ScrollView(size_hint=(None, None))
        root.size = (480,320)
        root.center = Window.center
        root.add_widget(layout)

        return root

if __name__ == '__main__':
    TestApp().run()
