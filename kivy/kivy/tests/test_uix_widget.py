from kivy.tests.common import GraphicUnitTest


class UIXWidgetTestCase(GraphicUnitTest):

    def test_default_widgets(self):
        from kivy.uix.button import Button
        from kivy.uix.slider import Slider
        r = self.render
        r(Button())
        r(Slider())

    def test_button_properties(self):
        from kivy.uix.button import Button
        r = self.render
        # test label attribute inside button
        r(Button(text='Hello world'))
        r(Button(text='Multiline\ntext\nbutton'))
        r(Button(text='Hello world', font_size=42))
        r(Button(text='This is my first line\nSecond line', halign='center'))

    def test_slider_properties(self):
        from kivy.uix.slider import Slider
        r = self.render
        r(Slider(value=25))
        r(Slider(value=50))
        r(Slider(value=100))
        r(Slider(min=-100, max=100, value=0))
        r(Slider(orientation='vertical', value=25))
        r(Slider(orientation='vertical', value=50))
        r(Slider(orientation='vertical', value=100))
        r(Slider(orientation='vertical', min=-100, max=100, value=0))

    def test_image_properties(self):
        from kivy.uix.image import Image
        from os.path import dirname, join
        r = self.render
        filename = join(dirname(__file__), 'test_button.png')
        r(Image(source=filename))

    def test_add_widget_index_0(self):
        from kivy.uix.widget import Widget
        from kivy.uix.button import Button
        r = self.render
        root = Widget()
        a = Button(text='Hello')
        b = Button(text='World', pos=(50, 10))
        c = Button(text='Kivy', pos=(10, 50))
        root.add_widget(a)
        root.add_widget(b)
        root.add_widget(c, 0)
        r(root)

    def test_add_widget_index_1(self):
        from kivy.uix.widget import Widget
        from kivy.uix.button import Button
        r = self.render
        root = Widget()
        a = Button(text='Hello')
        b = Button(text='World', pos=(50, 10))
        c = Button(text='Kivy', pos=(10, 50))
        root.add_widget(a)
        root.add_widget(b)
        root.add_widget(c, 1)
        r(root)

    def test_add_widget_index_2(self):
        from kivy.uix.widget import Widget
        from kivy.uix.button import Button
        r = self.render
        root = Widget()
        a = Button(text='Hello')
        b = Button(text='World', pos=(50, 10))
        c = Button(text='Kivy', pos=(10, 50))
        root.add_widget(a)
        root.add_widget(b)
        root.add_widget(c, 2)
        r(root)

    def test_widget_root_from_code_with_kv(self):
        from kivy.lang import Builder
        from kivy.factory import Factory
        from kivy.properties import StringProperty
        from kivy.uix.floatlayout import FloatLayout

        Builder.load_string("""
<UIXWidget>:
    Label:
        text: root.title

<BaseWidget>:
    CallerWidget:
""")

        class CallerWidget(FloatLayout):

            def __init__(self, **kwargs):
                super(CallerWidget, self).__init__(**kwargs)
                self.add_widget(UIXWidget(title="Hello World"))

        class NestedWidget(FloatLayout):
            title = StringProperty('aa')

        class UIXWidget(NestedWidget):
            pass

        class BaseWidget(FloatLayout):
            pass

        Factory.register('UIXWidget', cls=UIXWidget)
        Factory.register('CallerWidget', cls=CallerWidget)

        r = self.render
        root = BaseWidget()
        r(root)

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
