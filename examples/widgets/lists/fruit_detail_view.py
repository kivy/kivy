from kivy.controllers.objectcontroller import ObjectController
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image

from fixtures import fruit_data_attributes
from fixtures import fruit_data


# Used in list_cascade.py example.
#
class FruitDetailView(GridLayout):
    fruit_name = StringProperty('', allownone=True)

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        self.fruit_name = kwargs.get('fruit_name', '')
        super(FruitDetailView, self).__init__(**kwargs)
        if self.fruit_name:
            self.redraw()

    def redraw(self, *args):
        self.clear_widgets()
        if self.fruit_name:
            self.add_widget(Label(text="Name:", halign='right'))
            self.add_widget(Label(text=self.fruit_name))
            for attribute in fruit_data_attributes:
                self.add_widget(Label(text="{0}:".format(attribute),
                                      halign='right'))
                self.add_widget(
                    Label(text=str(fruit_data[self.fruit_name][attribute])))

    def fruit_changed(self, list_adapter, *args):
        if len(list_adapter.selection) == 0:
            self.fruit_name = None
        else:
            selected_object = list_adapter.selection[0]

            if type(selected_object) is str:
                self.fruit_name = selected_object
            else:
                self.fruit_name = selected_object.text

        self.redraw()


class FruitObserverDetailView(GridLayout):
    name = StringProperty('')

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(FruitObserverDetailView, self).__init__(**kwargs)
        self.bind(name=self.redraw)

    def redraw(self, *args):
        self.clear_widgets()
        if self.name:
            self.add_widget(Label(text="Name:", halign='right'))
            self.add_widget(Label(text=self.name))
            for attribute in fruit_data_attributes:
                self.add_widget(Label(text="{0}:".format(attribute),
                                      halign='right'))
                if self.name == '':
                    self.add_widget(Label(text=''))
                else:
                    self.add_widget(Label(
                        text=str(fruit_data[self.name][attribute])))

    def update(self, object_adapter, *args):
        if object_adapter.obj is None:
            return

        if type(object_adapter.obj) is str:
            self.name = object_adapter.obj
        else:
            self.name = str(object_adapter.obj)

        self.redraw()


# Used in list_cascade_images.py example.
#
class FruitImageDetailView(BoxLayout):
    name = StringProperty('', allownone=True)

    def __init__(self, **kwargs):
        kwargs['orientation'] = 'vertical'
        self.name = kwargs.get('fruit_name', '')
        super(FruitImageDetailView, self).__init__(**kwargs)
        if self.name:
            self.redraw()

    def redraw(self, *args):
        self.clear_widgets()

        if self.name:
            self.add_widget(Image(
                source="fruit_images/{0}.256.jpg".format(self.name),
                size=(256, 256)))

            container = GridLayout(cols=2)
            container.add_widget(Label(text="Name:", halign='right'))
            container.add_widget(Label(text=self.name))
            for attribute in fruit_data_attributes:
                container.add_widget(Label(text="{0}:".format(attribute),
                                      halign='right'))
                container.add_widget(
                        Label(text=str(fruit_data[self.name][attribute])))
            self.add_widget(container)

    def fruit_changed(self, list_adapter, *args):
        if len(list_adapter.selection) == 0:
            self.name = None
        else:
            selected_object = list_adapter.selection[0]

            # [TODO] Would we want touch events for the composite, as well as
            #        the components? Just the components? Just the composite?
            #
            # Is selected_object an instance of ThumbnailedListItem (composite)?
            #
            # Or is it a ListItemButton?
            #
            if hasattr(selected_object, 'name'):
                self.name = selected_object.name
            else:
                self.name = selected_object.fruit_name

        self.redraw()
