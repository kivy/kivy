from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ConfigParserProperty

KV = '''
FloatLayout:
    BoxLayout:
        size_hint: .5, .5
        pos_hint: {'center': (.5, .5)}

        orientation: 'vertical'

        TextInput:
            text: app.text
            on_text: app.text = self.text

        Slider:
            min: 0
            max: 100
            value: app.number
            on_value: app.number = self.value
'''


class ConfigApp(App):
    number = ConfigParserProperty(
        0, 'general', 'number',
        'app', val_type=float
    )
    text = ConfigParserProperty(
        '', 'general', 'text',
        'app', val_type=str
    )

    def build_config(self, config):
        config.setdefaults(
            'general',
            {
                'number': 0,
                'text': 'test'
            }
        )

    def build(self):
        return Builder.load_string(KV)


if __name__ == '__main__':
    ConfigApp().run()
