from kivy.uix.windowmanager import KivyWindowManager
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

class WindowManagerApp(KivyWindowManager):
    def __init__(self, *args):
        super(WindowManagerApp, self).__init__(*args)

        self.add_window_callback(self.add_window, name='glxgears')

    def add_window(self, window):
        self.root.add_widget(window)

    def build(self):
        layout = GridLayout(cols=2)
        layout.add_widget(Label(text='Kivy Window Manager'))
        return layout

if __name__ == '__main__':
    WindowManagerApp().run()

