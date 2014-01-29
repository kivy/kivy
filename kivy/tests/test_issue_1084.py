#
# Bug fixed:
# - put utf-8 in string, and validate -> no more crash due to str() encoding
# - put utf-8 in string, validate, close, open the app and edit the value -> no
# more weird space due to ascii->utf8 encoding.
# - create an unicode directory, and select it with Path. -> no more crash at
# validation.
# - create an unicode directory, and select it with Path and restart -> the path
# is still correct.

from kivy.app import App
from kivy.uix.settings import Settings

data = '''
[
    {
        "type": "string",
        "title": "String",
        "desc": "-",
        "section": "test",
        "key": "string"
    },
    {
        "type": "path",
        "title": "Path",
        "desc": "-",
        "section": "test",
        "key": "path"
    }
]
'''


class UnicodeIssueSetting(App):
    def build_config(self, config):
        config.add_section('test')
        config.setdefault('test', 'string', 'Hello world')
        config.setdefault('test', 'path', '/')

    def build(self):
        s = Settings()
        s.add_json_panel('Test Panel', self.config, data=data)
        return s

if __name__ == '__main__':
    UnicodeIssueSetting().run()
