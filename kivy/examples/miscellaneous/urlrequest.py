from kivy.lang import Builder
from kivy.app import App
from kivy.network.urlrequest import UrlRequest
from kivy.properties import NumericProperty, StringProperty, DictProperty

import json


KV = '''
#:import json json
#:import C kivy.utils.get_color_from_hex

BoxLayout:
    orientation: 'vertical'
    Label:
        text: 'see https://httpbin.org for more information'

    TextInput:
        id: ti
        hint_text: 'type url or select from dropdown'
        size_hint_y: None
        height: 48
        multiline: False
        foreground_color:
            (
            C('000000')
            if (self.text).startswith('http') else
            C('FF2222')
            )

    BoxLayout:
        size_hint_y: None
        height: 48
        Spinner:
            id: spinner
            text: 'select'
            values:
                [
                'http://httpbin.org/ip',
                'http://httpbin.org/user-agent',
                'http://httpbin.org/headers',
                'http://httpbin.org/delay/3',
                'http://httpbin.org/image/jpeg',
                'http://httpbin.org/image/png',
                'https://httpbin.org/delay/3',
                'https://httpbin.org/image/jpeg',
                'https://httpbin.org/image/png',
                ]
            on_text: ti.text = self.text

        Button:
            text: 'GET'
            on_press: app.fetch_content(ti.text)
            disabled: not (ti.text).startswith('http')
            size_hint_x: None
            width: 50

    Label:
        text: str(app.status)

    TextInput:
        readonly: True
        text: app.result_text

    Image:
        source: app.result_image
        nocache: True

    TextInput
        readonly: True
        text: json.dumps(app.headers, indent=2)
'''


class UrlExample(App):
    status = NumericProperty()
    result_text = StringProperty()
    result_image = StringProperty()
    headers = DictProperty()

    def build(self):
        return Builder.load_string(KV)

    def fetch_content(self, url):
        self.cleanup()
        UrlRequest(
            url,
            on_success=self.on_success,
            on_failure=self.on_failure,
            on_error=self.on_error
        )

    def cleanup(self):
        self.result_text = ''
        self.result_image = ''
        self.status = 0
        self.headers = {}

    def on_success(self, req, result):
        self.cleanup()
        headers = req.resp_headers
        content_type = headers.get('content-type', headers.get('Content-Type'))
        if content_type.startswith('image/'):
            fn = 'tmpfile.{}'.format(content_type.split('/')[1])
            with open(fn, 'wb') as f:
                f.write(result)
            self.result_image = fn
        else:
            if isinstance(result, dict):
                self.result_text = json.dumps(result, indent=2)
            else:
                self.result_text = result
        self.status = req.resp_status
        self.headers = headers

    def on_failure(self, req, result):
        self.cleanup()
        self.result_text = result
        self.status = req.resp_status
        self.headers = req.resp_headers

    def on_error(self, req, result):
        self.cleanup()
        self.result_text = str(result)


if __name__ == '__main__':
    UrlExample().run()
