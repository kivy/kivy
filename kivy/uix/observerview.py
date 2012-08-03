from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout


class ObserverView(BoxLayout):
    adapter = ObjectProperty(None)
    view_instance = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ObserverView, self).__init__(**kwargs)
        self.adapter.bind(obj=self.update)
        self.update(self.adapter)

    def set_view(self, view):
        self.view_instance = view

    def get_view(self):
        return self.view_instance

    def update(self, object_adapter, *args):
        self.clear_widgets()
        self.view_instance = object_adapter.get_view()
        self.add_widget(self.get_view())
        self.view_instance.update(object_adapter, *args)
