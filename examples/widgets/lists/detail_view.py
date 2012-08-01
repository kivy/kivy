from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.properties import StringProperty

from fruit_data import descriptors
from fruit_data import fruit_data


class DetailView(GridLayout):
    fruit_name = StringProperty('')

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(DetailView, self).__init__(**kwargs)

    def redraw(self, *args):
        self.clear_widgets()
        self.add_widget(Label(text="Name:", halign='right'))
        self.add_widget(Label(text=self.fruit_name))
        for category in descriptors:
            self.add_widget(Label(text="{0}:".format(category),
                                  halign='right'))
            self.add_widget(
                    Label(text=str(fruit_data[self.fruit_name][category])))

    def on_selection_change(self, list_adapter, *args):
        if len(list_adapter.selection) == 0:
            return

        selected_object = list_adapter.selection[0]

        if type(selected_object) is str:
            self.fruit_name = selected_object
        else:
            self.fruit_name = str(selected_object)

        self.redraw()
