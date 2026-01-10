from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ColorProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from kivy.uix.behaviors.hover import HoverBehavior

Builder.load_string("""
#:import MotionCollideBehavior kivy.uix.behaviors.motion.MotionCollideBehavior

<HoverButton>:
    canvas.before:
        Color:
            rgba: self.background_color
        Rectangle:
            pos: self.pos
            size: self.size

<HoverRecycleLabel>:
    size_hint_y: None
    height: 100
    halign: 'center'
    valign: 'middle'
    text_size: self.size
    canvas.before:
        Color:
            rgba: self.bg_color
        Rectangle:
            pos: self.pos
            size: self.size

<SimpleHoverWidget>:
    canvas.before:
        Color:
            rgba: self.background_color
        Rectangle:
            pos: self.pos
            size: self.size

<HoverOpaqueButton@MotionBlockBehavior+Button>:
    opacity: 0.75

<HoverRecycleView@MotionCollideBehavior+RecycleView>:
    viewclass: 'HoverRecycleLabel'
    RecycleBoxLayout:
        default_size: None, 100
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
        spacing: 15

<SimpleScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 15

        Label:
            text: 'Simple Hover Test'
            size_hint_y: 0.1
            font_size: '20sp'

        SimpleHoverWidget:
            size_hint: 0.5, 0.8
            pos_hint: {'center_x': 0.5}

        Button:
            text: 'Switch to Complex Demo'
            size_hint_y: 0.1
            on_press: root.manager.current = 'complex'

<ComplexScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 15

        Label:
            text: 'Complex Hover Demo (RecycleView)'
            size_hint_y: 0.1
            font_size: '20sp'

        BoxLayout:
            spacing: 25
            size_hint_y: 0.2

            HoverButton:
                text: 'Button 1'
            HoverButton:
                text: 'Button 2'
            HoverButton:
                text: 'Button 3'

        HoverRecycleView:
            id: rv
            size_hint_y: 0.6

    HoverOpaqueButton:
        text: 'Switch to Simple Demo'
        size_hint_y: 0.2
        on_press: root.manager.current = 'simple'
""")


class HoverButton(HoverBehavior, ButtonBehavior, Label):
    background_color = ColorProperty([0.2, 0.2, 0.2, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.original_color = self.background_color[:]

    def on_state(self, _, state):
        if state == "down":
            self.background_color = [0.8, 0.8, 0, 1]
        else:
            self.background_color = (
                [0.8, 0, 0.8, 1] if self.hovered else [0.2, 0.2, 0.2, 1]
            )

    def on_hover_enter(self, me):
        if self.state != "down":
            self.background_color = [0.8, 0.2, 0.2, 1]

    def on_hover_leave(self, me):
        if self.state != "down":
            self.background_color = [0.2, 0.2, 0.2, 1]


class HoverRecycleLabel(RecycleDataViewBehavior, HoverBehavior, Label):
    bg_color = ColorProperty([0.1, 0.1, 0.1, 1])
    base_text = StringProperty("")

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.base_text = data.get("text", "")
        return super().refresh_view_attrs(rv, index, data)

    def on_hover_enter(self, me):
        self.bg_color = [0.2, 0.4, 0.2, 1]
        self.text = f"{self.base_text}\n[HOVER]"

    def on_hover_leave(self, me):
        self.bg_color = [0.1, 0.1, 0.1, 1]
        self.text = self.base_text

    def on_hover_update(self, me):
        self.text = f"{self.base_text}\n({int(me.x)}, {int(me.y)})"


class SimpleHoverWidget(HoverBehavior, Label):
    background_color = ColorProperty([0, 0.5, 0, 1])

    def on_hover_enter(self, me):
        self.text = f"Enter: {int(me.x)}, {int(me.y)}"

    def on_hover_update(self, me):
        self.text = f"Update: {int(me.x)}, {int(me.y)}"

    def on_hover_leave(self, me):
        self.text = f"Leave: {int(me.x)}, {int(me.y)}"


class SimpleScreen(Screen):
    pass


class ComplexScreen(Screen):
    def on_enter(self):
        rv = self.ids.get("rv")
        if rv and not rv.data:
            rv.data = [{"text": f"Scrollable Label {i + 1}"} for i in range(50)]


class HoverDemoApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(SimpleScreen(name="simple"))
        sm.add_widget(ComplexScreen(name="complex"))
        return sm


if __name__ == "__main__":
    HoverDemoApp().run()
