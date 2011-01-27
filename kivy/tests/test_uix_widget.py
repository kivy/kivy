from common import GraphicUnitTest


class UIXWidgetTestCase(GraphicUnitTest):

    def test_default_button(self):
        from kivy.uix.button import Button
        self.render(Button())
        self.render(Button(text='Hello world AHAHA'))

    def test_default_slider(self):
        from kivy.uix.slider import Slider
        self.render(Slider())
        self.render(Slider(value=25), 2)
        self.render(Slider(value=50), 2)
        self.render(Slider(value=100), 2)
        self.render(Slider(min=-100, max=100, value=0), 2)

    '''
    def test_default_label(self):
        from kivy.uix.label import Label
        self.render(Label())

    def test_button_state_down(self):
        from kivy.uix.button import Button
        self.render(Button(state='down'))

    def test_label_text(self):
        from kivy.uix.label import Label
        self.render(Label(text='Hello world'))

    def test_label_font_size(self):
        from kivy.uix.label import Label
        self.render(Label(text='Hello world', font_size=16))

    def test_label_font_size(self):
        from kivy.uix.label import Label
        self.render(Label(text='Hello world'))
    '''
