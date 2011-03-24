from kivy.app import App
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout


class ScrollViewApp(App):

    def build(self):
        layout = GridLayout(cols=1, spacing=10, size_hint=(None, None),
                            width=500)
        for i in range(30):
            btn = Button(text=str(i), height=40, width=500)
            layout.add_widget(btn)

        root = ScrollView(size_hint=(None, None))
        root.size = (480, 320)
        root.center = Window.center
        root.add_widget(layout)

        return root

if __name__ == '__main__':
    ScrollViewApp().run()
