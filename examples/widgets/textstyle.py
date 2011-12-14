from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.gridlayout import GridLayout


class TextStyleApp(App):

    def build(self):

        self.btn_bold = ToggleButton(text='Bold')
        self.btn_bold.bind(state=self._update_text)
        self.btn_italic = ToggleButton(text='Italic')
        self.btn_italic.bind(state=self._update_text)

        ctrls = GridLayout(cols=1, spacing=50, padding=50)
        ctrls.add_widget(self.btn_bold)
        ctrls.add_widget(self.btn_italic)

        root = GridLayout(cols=2)
        root.add_widget(ctrls)
        self.label = Label(text='Hello world', font_size=18)
        root.add_widget(self.label)

        return root

    def _update_text(self, *largs):
        self.label.bold = self.btn_bold.state == 'down'
        self.label.italic = self.btn_italic.state == 'down'


if __name__ == '__main__':

    TextStyleApp().run()
