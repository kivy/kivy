from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.properties import StringProperty
from kivy.uix.image import Image

from fruit_data import descriptors
from fruit_data import fruit_data


class ImageDetailView(BoxLayout):
    fruit_name = StringProperty('')

    def __init__(self, **kwargs):
        kwargs['orientation'] = 'vertical'
        super(ImageDetailView, self).__init__(**kwargs)

    def redraw(self, *args):
        self.clear_widgets()

        self.add_widget(Image(source=filename, size=(256, 256)))

        container = GridLayout(cols=2)
        container.add_widget(Label(text="Name:", halign='right'))
        container.add_widget(Label(text=self.fruit_name))
        for category in descriptors:
            container.add_widget(Label(text="{0}:".format(category),
                                  halign='right'))
            container.add_widget(
                    Label(text=str(fruit_data[self.fruit_name][category])))
        self.add_widget(container)

    def on_selection_change(self, list_adapter, *args):
        if len(list_adapter.selection) == 0:
            return

        selected_object = list_adapter.selection[0]

        if type(selected_object) is str:
            self.fruit_name = selected_object
        else:
            self.fruit_name = str(selected_object)

        self.redraw()
