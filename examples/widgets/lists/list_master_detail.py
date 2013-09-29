from kivy.app import App
from kivy.binding import DataBinding
from kivy.controllers.listcontroller import ListController
from kivy.enums import binding_modes
from kivy.enums import binding_transforms
from kivy.models import SelectableDataItem
from kivy.properties import StringProperty
from kivy.properties import TransformProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.listview import ListView
from kivy.uix.listview import ListItemButton
from kivy.uix.objectview import ObjectView

from fixtures import fruit_data

from fruit_detail_view import FruitDetailView
from fixtures import fruit_data_attributes
from fixtures import fruit_data_list_of_dicts


##############################################################################
#
#    Data
#
#        Data items must have a ksel object, which is a Kivy Selection object
#        used to tie selection of individual items to the selection machinery
#        of ListView and other similar views. Subclass SelectableDataItem for
#        an easy way to get this functionality. Note that self.data here is
#        in internal scope within FruitItem, and should not to be confused
#        with the formal data property of controllers.

class FruitItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(FruitItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.serving_size = kwargs.get('Serving Size', '')
        self.data = kwargs.get('data', [])


############################################################################
#
#    Controllers
#
#        In a real app, a good practice is to put controllers in their own
#        directory called controllers/, and have one controller per python
#        module, imported into your App class, so you can refer to them as
#        app.fruits_controller, app.categories_controller, etc. Controllers
#        are typically shared in different parts of a larger application.

class FruitsController(ListController):

    # A ListController has built-in methods such as all(), first(), last(),
    # and others, but you can add your own "computed properties" using this
    # TransformProperty, or the similar AliasProperty, and/or make custom
    # methods as needed. This names property is not used in this example, but
    # illustrates what you might do. Consider filter methods that could be
    # used instead of the lambda (func=self.some_filter_function).
    names = TransformProperty(subject='data',
                              op=binding_transforms.TRANSFORM,
                              func=lambda data: [item.name for item in data])

    def __init__(self, **kwargs):
        kwargs['selection_mode'] = 'single'
        kwargs['allow_empty_selection'] = False
        super(FruitsController, self).__init__(**kwargs)

# In this example, we are building a python-only view system. See other
# examples for using the kv language.

class FruitDetailView(GridLayout):
    fruit_name = StringProperty('', allownone=True)

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(FruitDetailView, self).__init__(**kwargs)

        if self.fruit_name:
            self.add_widget(Label(
                text="Name:",
                size_hint_y=None,
                height=25,
                halign='right'))
            self.add_widget(Label(
                text=self.fruit_name,
                size_hint_y=None,
                height=25))
            for attribute in fruit_data_attributes:
                self.add_widget(Label(
                    text="{0}:".format(attribute),
                    size_hint_y=None,
                    height=25,
                    halign='right'))
                self.add_widget(Label(
                    text=str(fruit_data[self.fruit_name][attribute]),
                    size_hint_y=None,
                    height=25))


class MasterDetailView(GridLayout):
    '''Implementation of an master-detail view with a vertical scrollable list
    on the left (the master, or source list) and a detail view on the right.
    When selection changes in the master list, the content of the detail view
    is updated.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(MasterDetailView, self).__init__(**kwargs)

        app = App.app()

        list_item_class_args = \
                lambda row_index, fruit: {'text': fruit.name,
                                          'size_hint_y': None,
                                          'height': 25}

        self.add_widget(ListView(
                data_binding=DataBinding(
                    source=app.fruits_controller),
                args_converter=list_item_class_args,
                list_item_class=ListItemButton,
                size_hint=(.3, 1.0)))

        self.add_widget(ObjectView(
                data_binding=DataBinding(
                    source=app.fruits_controller,
                    prop='selection',
                    mode=binding_modes.FIRST_ITEM),
                args_converter=lambda row_index, fruit: {'fruit_name': fruit.name},
                list_item_class=FruitDetailView,
                size_hint=(.7, 1.0)))


class MasterDetailApp(App):

    def __init__(self, **kwargs):
        super(MasterDetailApp, self).__init__(**kwargs)

        self.fruits_controller = FruitsController()

        # In this example, instead of using the FruitsController subclass,
        # which is used here to illustreate the names transform property, we
        # could have simply used ListController directly, as with:
        #
        # self.fruits_controller = ListController(
        #     selection_mode='single',
        #     allow_empty_selection=False)

    def build(self):
        self.master_detail_view = MasterDetailView(width=800)
        return self.master_detail_view

    def on_start(self):

        # Load data into controllers. Put some thinking into when you want or
        # need to load data into controllers. Here we illustrate how the app
        # can be initialized with empty controllers, only to be filled later,
        # in this case on app start up.

        # fruit_data_list_of_dicts is a list of dicts, already sorted.
        self.fruits_controller.data = \
            [FruitItem(**fruit_dict) for fruit_dict in fruit_data_list_of_dicts]


if __name__ in ('__main__'):
    MasterDetailApp().run()
