from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty

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
    fruit_name = StringProperty('')

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(FruitObserverDetailView, self).__init__(**kwargs)
        self.bind(fruit_name=self.redraw)

    def redraw(self, *args):
        self.clear_widgets()
        if self.fruit_name:
            self.add_widget(Label(text="Name:", halign='right'))
            self.add_widget(Label(text=self.fruit_name))
            for attribute in fruit_data_attributes:
                self.add_widget(Label(text="{0}:".format(attribute),
                                      halign='right'))
                if self.fruit_name == '':
                    self.add_widget(Label(text=''))
                else:
                    self.add_widget(Label(
                        text=str(fruit_data[self.fruit_name][attribute])))

    def update(self, object_adapter, *args):
        if object_adapter.obj is None:
            return

        if type(object_adapter.obj) is str:
            self.fruit_name = object_adapter.obj
        else:
            self.fruit_name = str(object_adapter.obj)

        self.redraw()


# Used in list_cascade_images.py example.
#
class FruitImageDetailView(BoxLayout):
    fruit_name = StringProperty('', allownone=True)

    def __init__(self, **kwargs):
        kwargs['orientation'] = 'vertical'
        self.fruit_name = kwargs.get('fruit_name', '')
        super(FruitImageDetailView, self).__init__(**kwargs)
        if self.fruit_name:
            self.redraw()

    def redraw(self, *args):
        self.clear_widgets()

        if self.fruit_name:
            self.add_widget(Image(
                source="fruit_images/{0}.256.jpg".format(self.fruit_name),
                size=(256, 256)))

            container = GridLayout(cols=2)
            container.add_widget(Label(text="Name:", halign='right'))
            container.add_widget(Label(text=self.fruit_name))
            for attribute in fruit_data_attributes:
                container.add_widget(Label(text="{0}:".format(attribute),
                                      halign='right'))
                container.add_widget(
                        Label(text=str(fruit_data[self.fruit_name][attribute])))
            self.add_widget(container)

    def fruit_changed(self, list_adapter, *args):
        if len(list_adapter.selection) == 0:
            self.fruit_name = None
        else:
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
