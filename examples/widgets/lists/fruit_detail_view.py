from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty

from fruit_data import descriptors
from fruit_data import fruit_data


class FruitDetailView(GridLayout):
    fruit_name = StringProperty('')

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(FruitDetailView, self).__init__(**kwargs)

    def redraw(self, *args):
        self.clear_widgets()
        self.add_widget(Label(text="Name:", halign='right'))
        self.add_widget(Label(text=self.fruit_name))
        for category in descriptors:
            self.add_widget(Label(text="{0}:".format(category),
                                  halign='right'))
            self.add_widget(
                    Label(text=str(fruit_data[self.fruit_name][category])))

    def fruit_changed(self, list_adapter, *args):
        if len(list_adapter.selection) == 0:
            return

        selected_object = list_adapter.selection[0]

        if type(selected_object) is str:
            self.fruit_name = selected_object
        else:
            self.fruit_name = str(selected_object)

        self.redraw()


class FruitImageDetailView(BoxLayout):
    fruit_name = StringProperty('')

    def __init__(self, **kwargs):
        kwargs['orientation'] = 'vertical'
        super(FruitImageDetailView, self).__init__(**kwargs)

    def redraw(self, *args):
        self.clear_widgets()

        self.add_widget(Image(
            source="fruit_images/{0}.256.jpg".format(self.fruit_name),
            size=(256, 256)))

        container = GridLayout(cols=2)
        container.add_widget(Label(text="Name:", halign='right'))
        container.add_widget(Label(text=self.fruit_name))
        for category in descriptors:
            container.add_widget(Label(text="{0}:".format(category),
                                  halign='right'))
            container.add_widget(
                    Label(text=str(fruit_data[self.fruit_name][category])))
        self.add_widget(container)

    def fruit_changed(self, list_adapter, *args):
        if len(list_adapter.selection) == 0:
            return

        selected_object = list_adapter.selection[0]

        # [TODO] Would we want touch events for the composite, as well as
        #        the components? Just the components? Just the composite?
        #
        # Is selected_object an instance of ThumbnailedListItem (composite)?
        #
        # Or is it a ListItemButton?
        # 
        if hasattr(selected_object, 'fruit_name'):
            self.fruit_name = selected_object.fruit_name
        else:
            self.fruit_name = selected_object.text

        self.redraw()
