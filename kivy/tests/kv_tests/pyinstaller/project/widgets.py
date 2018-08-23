
from kivy.uix.widget import Widget
from kivy.lang.compiler import kv, KvContext


class MyWidget(Widget):

    @kv()
    def apply_kv(self):
        with KvContext():
            self.x @= self.y
