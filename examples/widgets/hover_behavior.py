from random import randint

from kivy.config import Config

Config.set('graphics', 'width', 1200)

from kivy.app import App
from kivy.base import EventLoop
from kivy.input.managers.hover import HoverEventManager
from kivy.lang import Builder
from kivy.properties import StringProperty, ColorProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.behaviors.hover import HoverBehavior, StencilViewHoverMixin
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior

kv = '''
<HoverButton>:
    canvas.before:
        Color:
            rgba: self.background_color
        Rectangle:
            pos: self.pos
            size: self.size


<XHoverButton>:
    text_size: self.size
    valign: 'center'
    normal_color: 0, 0, 0, 0
    size_hint_y: None
    height: '30dp'
    padding_x: '10dp'


<IconButton>:
    source: 'data/logo/kivy-icon-32.png'
    canvas.before:
        Color:
            rgba: self.hovered_color if self.hovered else self.normal_color
        Rectangle:
            pos: self.pos
            size: self.size


<ChatItem>:
    spacing: '5dp'
    hover_mode: 'all'
    canvas:
        Color:
            rgb: [0.4, 0.4, 0.4] if self.hovered else [0.2, 0.2, 0.2]
        Rectangle:
            pos: self.pos
            size: self.size
    AnchorLayout:
        anchor_y: 'top'
        size_hint_x: None
        width: '50dp'
        IconButton:
            source: 'data/logo/kivy-icon-64.png'
            size_hint_y: None
            height: '50dp'
    BoxLayout:
        padding: 0, '2dp', 0, 0
        spacing: '2dp'
        orientation: 'vertical'
        HoverLabel:
            text: root.name
            size_hint: None, None
            bold: True
            font_size: '16sp'
            size: self.texture_size
            valign: 'center'
        Label:
            text: root.message
            text_size: self.size
            valign: 'top'


<UserButton>:
    spacing: '5dp'
    padding: '2dp', 0, '5dp', 0
    canvas:
        Color:
            rgba: [0.3, 0.3, 0.3, 1.0]
        Rectangle:
            pos: self.pos
            size: self.size
    Image:
        size_hint_x: None
        width: '50dp'
        source: root.icon
    BoxLayout:
        Label:
            text: root.name
            text_size: self.size
            valign: 'center'
        BoxLayout:
            padding: 0, '15dp'
            spacing: '5dp'
            IconButton:
                hovered_color: [0.4, 0.4, 0.4, 1.0]
            IconButton:
                hovered_color: [0.4, 0.4, 0.4, 1.0]
            IconButton:
                hovered_color: [0.4, 0.4, 0.4, 1.0]


<UserItem>:
    hover_mode: 'all'
    spacing: '5dp'
    padding: 0, 0, '5dp', 0
    canvas:
        Color:
            rgba: self.hovered_color if self.hovered else self.normal_color
        Rectangle:
            pos: self.pos
            size: self.size
    IconButton:
        size_hint_x: None
        width: '50dp'
        source: root.icon
    Label:
        text: root.name
        text_size: self.size
        valign: 'center'


<TopicItem>:
    hover_mode: 'self'
    spacing: '5dp'
    canvas:
        Color:
            rgba: self.hovered_color if self.hovered else self.normal_color
        Rectangle:
            pos: self.pos
            size: self.size
    Image:
        size_hint_x: None
        width: '30dp'
        source: 'data/logo/kivy-icon-16.png'
    Label:
        text: root.name
        text_size: self.size
        valign: 'center'


<MenuDropDownContainer>:
    cols: 1
    size_hint_y: None
    height: self.minimum_height
    spacing: '2dp'
    padding: 0, '5dp', 0, 0
    canvas:
        Color:
            rgba: 0.1, 0.1, 0.1, 1
        Rectangle:
            pos: self.pos
            size: self.size


<RootWidget>:
    BoxLayout:
        size_hint_x: None
        width: '80dp'
        orientation: 'vertical'
        padding: 0, 0, '2dp', 0
        HoverButton:
            size_hint_y: None
            height: '80dp'
            text: 'HOME'
        HoverRecycleView:
            id: side_menu
            viewclass: 'HoverButton'
            RecycleGridLayout:
                cols: 1
                default_size: None, dp(56)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
    BoxLayout:
        id: main_content
        canvas:
            Color:
                rgba: [0.17, 0.17, 0.17, 1.0]
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            id: project_menu
            orientation: 'vertical'
            size_hint_x: None
            width: '250dp'
            HoverButton:
                id: project_title
                size_hint_y: None
                height: '60dp'
                text: 'Workspace'
            HoverRecycleView:
                id: project_topics
                viewclass: 'TopicItem'
                effect_cls: 'ScrollEffect'
                RecycleGridLayout:
                    cols: 1
                    default_size: None, dp(30)
                    default_size_hint: 1, None
                    size_hint_y: None
                    height: self.minimum_height
            UserButton:
                id: user_menu
                size_hint_y: None
                height: '60dp'
        BoxLayout:
            orientation: 'vertical'
            BoxLayout:
                size_hint_y: None
                height: '60dp'
                AnchorLayout:
                    padding: '5dp', 0
                    anchor_x: 'left'
                    HoverLabel:
                        id: topic_title
                        text: 'Topic (click for description)'
                        size_hint: None, None
                        size: self.texture_size
                        bold: True
                        font_size: '18sp'
                BoxLayout:
                    size_hint_x: None
                    width: '340dp'
                    padding: '12dp'
                    spacing: '2dp'
                    IconButton:
                        size_hint_x: None
                        width: '40dp'
                    IconButton:
                        size_hint_x: None
                        width: '40dp'
                    IconButton:
                        size_hint_x: None
                        width: '40dp'
                    TextInput:
                        multiline: False
                        font_size: '18sp'
                    IconButton:
                        size_hint_x: None
                        width: '40dp'
                    IconButton:
                        size_hint_x: None
                        width: '40dp'
            BoxLayout:
                BoxLayout:
                    padding: '5dp', 0
                    orientation: 'vertical'
                    HoverRecycleView:
                        id: rv_chat
                        viewclass: 'ChatItem'
                        effect_cls: 'ScrollEffect'
                        scroll_y: 0
                        RecycleGridLayout:
                            cols: 1
                            spacing: '2dp'
                            default_size: None, dp(80)
                            default_size_hint: 1, None
                            size_hint_y: None
                            height: self.minimum_height
                    BoxLayout:
                        size_hint_y: None
                        height: '60dp'
                        padding: 0, '10dp'
                        HoverButton:
                            size_hint_x: None
                            width: '40dp'
                        TextInput:
                            id: message_input
                            font_size: '18sp'
                            multiline: False
                HoverRecycleView:
                    id: users_list
                    size_hint_x: None
                    width: '240dp'
                    viewclass: 'UserItem'
                    effect_cls: 'ScrollEffect'
                    RecycleGridLayout:
                        cols: 1
                        spacing: '2dp'
                        default_size: None, dp(50)
                        default_size_hint: 1, None
                        size_hint_y: None
                        height: self.minimum_height
'''

Builder.load_string(kv)


class RootWidget(BoxLayout):
    pass


class HoverButton(HoverBehavior, ButtonBehavior, Label):

    background_color = ColorProperty([0.3, 0.3, 0.3, 1.0])
    normal_color = ColorProperty([0.3, 0.3, 0.3, 1.0])
    down_color = ColorProperty([0.5, 0.5, 1.0, 1.0])
    hovered_color = ColorProperty([0.5, 0.5, 0.5, 1.0])

    def __init__(self, **kwargs):
        self.fbind('hovered', self._update_background_color)
        self.fbind('state', self._update_background_color)
        super().__init__(**kwargs)
        self.background_color = self.normal_color

    def _update_background_color(self, *args):
        if self.state == 'down':
            self.background_color = self.down_color
        else:
            if self.hovered and self.state == 'normal':
                self.background_color = self.hovered_color
            elif self.state == 'normal':
                self.background_color = self.normal_color


class XHoverButton(HoverButton):

    def on_hovered(self, button, hovered):
        self.padding_x = '20dp' if hovered else '10dp'


class HoverLabel(HoverBehavior, ButtonBehavior, Label):

    text_color = ColorProperty([1, 1, 1, 1.0])
    hovered_color = ColorProperty([1, 1, 0, 1.0])

    def on_hovered(self, label, hovered):
        self.color = self.hovered_color if hovered else self.text_color


class IconButton(HoverBehavior, ButtonBehavior, Image):

    normal_color = ColorProperty([0.5, 0.5, 0.5, 0.0])
    hovered_color = ColorProperty([0.3, 0.3, 0.3, 1.0])


class UserButton(HoverBehavior, BoxLayout):

    icon = StringProperty('data/logo/kivy-icon-64.png')
    name = StringProperty('Username')


class TopicItem(HoverBehavior, BoxLayout):

    name = StringProperty()
    normal_color = ColorProperty([0.5, 0.5, 0.5, 0.0])
    hovered_color = ColorProperty([0.3, 0.3, 0.3, 1.0])


class ChatItem(HoverBehavior, RecycleDataViewBehavior, BoxLayout):

    name = StringProperty()
    message = StringProperty()

    def refresh_view_attrs(self, rv, index, data):
        self.name = data.get('name', '')
        self.message = data.get('message', '')


class UserItem(HoverBehavior, RecycleDataViewBehavior, BoxLayout):

    icon = StringProperty('data/logo/kivy-icon-64.png')
    name = StringProperty()
    normal_color = ColorProperty([0.2, 0.2, 0.2, 1.0])
    hovered_color = ColorProperty([0.4, 0.4, 0.4, 1.0])


class HoverRecycleView(StencilViewHoverMixin, RecycleView):
    pass


class MenuDropDownContainer(GridLayout):
    pass


class HoverBehaviorApp(App):

    def build(self):
        EventLoop.add_event_manager(HoverEventManager())
        root = RootWidget()
        root.ids.side_menu.data = self.build_side_menu_data()
        root.ids.project_topics.data = self.build_project_topics_data()
        root.ids.rv_chat.data = self.build_chat_data()
        root.ids.users_list.data = self.build_users_list_data()
        root.ids.project_title.bind(on_release=self.show_project_dropdown)
        root.ids.topic_title.bind(on_release=self.show_topic_description)
        return root

    def build_side_menu_data(self):
        return [{'text': 'Work %d' % i} for i in range(4)]

    def build_project_topics_data(self):
        return [{'name': 'Topic %d' % i} for i in range(20)]

    def build_chat_data(self):
        return [
            {'name': 'User %d' % randint(0, 6),
             'message': 'Message'}
            for i in range(50)
        ]

    def build_users_list_data(self):
        return [{'name': 'User %d' % i} for i in range(60)]

    def show_project_dropdown(self, button):
        dp = DropDown()
        cnt = MenuDropDownContainer()
        dp.add_widget(cnt)
        for i in range(10):
            item = XHoverButton(text='Option %d' % i)
            item.bind(on_release=lambda btn: dp.select(btn.text))
            cnt.add_widget(item)
        dp.container.padding = ['10dp', 0]
        dp.open(button)

    def show_topic_description(self, button):
        content = Label(text='Topic Description')
        popup = Popup(size_hint=(None, None),
                      size=(500, 200),
                      title='Topic',
                      content=content)
        popup.open()

    def on_start(self):
        self.root_window.clearcolor = (0.12, 0.12, 0.12, 1.0)


if __name__ == '__main__':
    HoverBehaviorApp().run()
