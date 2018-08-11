#cython: binding=True

from kivy.uix.widget import Widget
from kivy.lang.compiler import KV, KVCtx

class MyWidget(Widget):

    @KV()
    def apply_kv(self):
        with KVCtx():
            self.x @= self.y
