'''
A form generator, using random data, but can be data driven (json or whatever)

Shows that you can use the key_viewclass attribute of RecycleView to select a
different Widget for each item.
'''

from random import choice, choices
from string import ascii_lowercase

from kivy.app import App
from kivy.lang import Builder
from kivy import properties as P


KV = r'''
<RVTextInput,RVCheckBox,RVSpinner>:
    size_hint_y: None
    height: self.minimum_height
    index: None
    title: ''


<RVTextInput@BoxLayout>:
    value: ''
    Label:
        text: root.title
        size_hint_y: None
        height: self.texture_size[1]
    TextInput:
        text: root.value
        on_text: app.handle_update(self.text, root.index)
        size_hint_y: None
        height: dp(40)
        multiline: False


<RVCheckBox@BoxLayout>:
    value: False
    Label:
        text: root.title
        size_hint_y: None
        height: self.texture_size[1]
    CheckBox:
        active: root.value
        on_active: app.handle_update(self.active, root.index)
        size_hint_y: None
        height: dp(40)


<RVSpinner@BoxLayout>:
    value: ''
    values: []
    Label:
        text: root.title
        size_hint_y: None
        height: self.texture_size[1]
    Spinner:
        text: root.value
        values: root.values
        size_hint_y: None
        height: dp(40)
        on_text: app.handle_update(self.text, root.index)


FloatLayout:
    RecycleView:
        id: rv
        data: app.data
        key_viewclass: 'widget'
        size_hint_x: 1
        RecycleBoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            default_size_hint: 1, None

'''


class Application(App):
    '''A form manager demonstrating the power of RecycleView's key_viewclass
    property.
    '''
    data = P.ListProperty()

    def build(self):
        root = Builder.load_string(KV)
        rv = root.ids.rv
        self.data = [
            self.create_random_input(rv, index)
            for index in range(20)
        ]

        return root

    def handle_update(self, value, index):
        if None not in (index, value):
            self.data[index]['value'] = value

    def create_random_input(self, rv, index):
        return choice((
            self.create_textinput,
            self.create_checkbox,
            self.create_spinner
        ))(rv, index)

    def create_spinner(self, rv, index):
        """
        create a dict of data for a spinner
        """
        return {
            'index': index,
            'widget': 'RVSpinner',
            'value': '',
            'values': [
                letter * 5
                for letter in ascii_lowercase[:5]
            ],
            'ready': True,
        }

    def create_checkbox(self, rv, index):
        """
        create a dict of data for a checkbox
        """
        return {
            'index': index,
            'widget': 'RVCheckBox',
            'value': choice((True, False)),
            'title': ''.join(choices(ascii_lowercase, k=10)),
            'ready': True,
        }

    def create_textinput(self, rv, index):
        """
        create a dict of data for a textinput
        """
        return {
            'index': index,
            'widget': 'RVTextInput',
            'value': ''.join(choices(ascii_lowercase, k=10)),
            'title': ''.join(choices(ascii_lowercase, k=10)),
            'ready': True,
        }


if __name__ == "__main__":
    Application().run()
