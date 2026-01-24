from kivy.app import App
from kivy.eventmanager.hover import HoverManager
from kivy.lang import Builder
from kivy.uix.behaviors import HoverBehavior
from kivy.uix.label import Label

Builder.load_string("""
<RootWidget>:
    halign: 'left'
    text_size: self.width, None
    padding: '10dp', 0
    canvas.before:
        Color:
            rgba: [0, 0.5, 0, 1] if self.hovered else [0.5, 0.5, 0.5, 1]
        Rectangle:
            pos: self.pos
            size: self.size
""")


class RootWidget(HoverBehavior, Label):

    def on_hover_enter(self, me):
        super().on_hover_enter(me)
        self.text = f'Enter: {me.pos}'

    def on_hover_update(self, me):
        super().on_hover_update(me)
        self.text = f'Update: {me.pos}'

    def on_hover_leave(self, me):
        super().on_hover_leave(me)
        self.text = f'Leave: {me.pos}'


class SimpleHoverApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hover_manager = HoverManager()

    def build(self):
        return RootWidget(size_hint=(0.5, 0.5),
                          pos_hint={'center_x': 0.5, 'center_y': 0.5})

    def on_start(self):
        super().on_start()
        self.root_window.register_event_manager(self.hover_manager)

    def on_stop(self):
        super().on_stop()
        self.root_window.unregister_event_manager(self.hover_manager)


if __name__ == '__main__':
    SimpleHoverApp().run()
