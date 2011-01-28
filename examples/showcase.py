from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.slider import Slider


class ShowcaseApp(App):

    def build(self):
        root = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # button layout
        col = BoxLayout(spacing=10)
        root.add_widget(col)
        col.add_widget(Button(text='Hello world'))
        col.add_widget(Button(text='Hello world', state='down'))

        # toggle button
        col = BoxLayout(spacing=10)
        root.add_widget(col)
        col.add_widget(ToggleButton(text='Option 1', group='t1'))
        col.add_widget(ToggleButton(text='Option 2', group='t1'))
        col.add_widget(ToggleButton(text='Option 3', group='t1'))

        # sliders
        col = BoxLayout(spacing=10)
        root.add_widget(col)

        vbox = BoxLayout(orientation='vertical', spacing=10)
        col.add_widget(vbox)
        vbox.add_widget(Slider())
        vbox.add_widget(Slider(value=50))

        hbox = BoxLayout(spacing=10)
        col.add_widget(hbox)
        hbox.add_widget(Slider(orientation='vertical'))
        hbox.add_widget(Slider(orientation='vertical', value=50))

        return root


if __name__ == '__main__':
    ShowcaseApp().run()
