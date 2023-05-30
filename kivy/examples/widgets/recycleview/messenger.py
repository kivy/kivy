from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import ListProperty
from kivy.animation import Animation
from kivy.metrics import dp

KV = '''
#:import RGBA kivy.utils.rgba

<ImageButton@ButtonBehavior+Image>:
    size_hint: None, None
    size: self.texture_size

    canvas.before:
        PushMatrix
        Scale:
            origin: self.center
            x: .75 if self.state == 'down' else 1
            y: .75 if self.state == 'down' else 1

    canvas.after:
        PopMatrix

BoxLayout:
    orientation: 'vertical'
    padding: dp(5), dp(5)
    RecycleView:
        id: rv
        data: app.messages
        viewclass: 'Message'
        do_scroll_x: False

        RecycleBoxLayout:
            id: box
            orientation: 'vertical'
            size_hint_y: None
            size: self.minimum_size
            default_size_hint: 1, None
            # magic value for the default height of the message
            default_size: 0, 38
            key_size: '_size'

    FloatLayout:
        size_hint_y: None
        height: 0
        Button:
            size_hint_y: None
            height: self.texture_size[1]
            opacity: 0 if not self.height else 1
            text:
                (
                'go to last message'
                if rv.height < box.height and rv.scroll_y > 0 else
                ''
                )
            pos_hint: {'pos': (0, 0)}
            on_release: app.scroll_bottom()

    BoxLayout:
        size_hint: 1, None
        size: self.minimum_size
        TextInput:
            id: ti
            size_hint: 1, None
            height: min(max(self.line_height, self.minimum_height), 150)
            multiline: False

            on_text_validate:
                app.send_message(self)

        ImageButton:
            source: 'data/logo/kivy-icon-48.png'
            on_release:
                app.send_message(ti)

<Message@FloatLayout>:
    message_id: -1
    bg_color: '#223344'
    side: 'left'
    text: ''
    size_hint_y: None
    _size: 0, 0
    size: self._size
    text_size: None, None
    opacity: min(1, self._size[0])

    Label:
        text: root.text
        padding: 10, 10
        size_hint: None, 1
        size: self.texture_size
        text_size: root.text_size

        on_texture_size:
            app.update_message_size(
            root.message_id,
            self.texture_size,
            root.width,
            )

        pos_hint:
            (
            {'x': 0, 'center_y': .5}
            if root.side == 'left' else
            {'right': 1, 'center_y': .5}
            )

        canvas.before:
            Color:
                rgba: RGBA(root.bg_color)
            RoundedRectangle:
                size: self.texture_size
                radius: dp(5), dp(5), dp(5), dp(5)
                pos: self.pos

        canvas.after:
            Color:
            Line:
                rounded_rectangle: self.pos + self.texture_size + [dp(5)]
                width: 1.01
'''


class MessengerApp(App):
    messages = ListProperty()

    def build(self):
        return Builder.load_string(KV)

    def add_message(self, text, side, color):
        # create a message for the recycleview
        self.messages.append({
            'message_id': len(self.messages),
            'text': text,
            'side': side,
            'bg_color': color,
            'text_size': [None, None],
        })

    def update_message_size(self, message_id, texture_size, max_width):
        # when the label is updated, we want to make sure the displayed size is
        # proper
        if max_width == 0:
            return

        one_line = dp(50)  # a bit of  hack, YMMV

        # if the texture is too big, limit its size
        if texture_size[0] >= max_width * 2 / 3:
            self.messages[message_id] = {
                **self.messages[message_id],
                'text_size': (max_width * 2 / 3, None),
            }

        # if it was limited, but is now too small to be limited, raise the limit
        elif texture_size[0] < max_width * 2 / 3 and \
                texture_size[1] > one_line:
            self.messages[message_id] = {
                **self.messages[message_id],
                'text_size': (max_width * 2 / 3, None),
                '_size': texture_size,
            }

        # just set the size
        else:
            self.messages[message_id] = {
                **self.messages[message_id],
                '_size': texture_size,
            }

    @staticmethod
    def focus_textinput(textinput):
        textinput.focus = True

    def send_message(self, textinput):
        text = textinput.text
        textinput.text = ''
        self.add_message(text, 'right', '#223344')
        self.focus_textinput(textinput)
        Clock.schedule_once(lambda *args: self.answer(text), 1)
        self.scroll_bottom()

    def answer(self, text, *args):
        self.add_message('do you really think so?', 'left', '#332211')

    def scroll_bottom(self):
        rv = self.root.ids.rv
        box = self.root.ids.box
        if rv.height < box.height:
            Animation.cancel_all(rv, 'scroll_y')
            Animation(scroll_y=0, t='out_quad', d=.5).start(rv)


if __name__ == '__main__':
    MessengerApp().run()
