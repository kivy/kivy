from kivy.app import App
from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.objectadapter import ObjectAdapter
from kivy.models import SelectableDataItem
from kivy.binding import Binding
from kivy.controllers.listcontroller import ListController
from kivy.controllers.objectcontroller import ObjectController
from kivy.controllers.transformcontroller import TransformController
from kivy.enums import binding_modes
from kivy.enums import binding_transforms
from kivy.properties import StringProperty
from kivy.selection import SelectionTool
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.listview import ListItemButton
from kivy.uix.listview import ListView
from kivy.uix.listview import SelectableView
from kivy.uix.objectview import ObjectView

from fixtures import fruit_categories
from fixtures import fruit_data
from fixtures import fruit_data_attributes
from fixtures import fruit_data_list_of_dicts

# This is an expansion on the "master-detail" example to illustrate cascading
# from the selection of one list view to another. In this example there are two
# lists, each restricted to single selection. There is a list on the left for
# fruit categories, a list in the middle for fruits within the selected
# category, and a detail panel on the right. The fruit categories list uses a
# list controller that holds the base data from which the other user interface
# elements update in a cascade. The list in the middle uses a list controller
# that is filled based on the selection in the first list.  The DetailView on
# the right uses an object controller that is updated from the selection of the
# middle list.

##########
#  DATA

# The adapters and controllers used below have Selection mixed in, automating
# the updating of a subset list of selected items.  Selection requires that
# individual data items perform selection operations.  It is not difficult to
# make your own data items that provide this functionality. Define custom data
# item classes that subclass SelectableDataItem:


class CategoryItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(CategoryItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.fruits = kwargs.get('fruits', [])

        self.ksel = SelectionTool(False)


class FruitItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(FruitItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.serving_size = kwargs.get('Serving Size', '')

        # The data here is the raw fruit data about individual fruits.
        self.data = kwargs.get('data', [])

        self.ksel = SelectionTool(False)

# Each of the SelectableDataItem subclasses above have the important ksel
# attribute as an instance of SelectionTool().


###########
# VIEWS

class FruitDetailView(GridLayout, SelectableView):

    text = StringProperty('')

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        kwargs['size_hint'] = (1, None)

        super(FruitDetailView, self).__init__(**kwargs)

        self.bind(minimum_height=self.setter('height'))

        self.add_widget(Label(text="Name:",
                              size_hint_y=None,
                              height=50,
                              halign='right'))

        self.add_widget(Label(text=self.text,
                              size_hint_y=None,
                              height=50))

        for attribute in fruit_data_attributes:
            self.add_widget(Label(text="{0}:".format(attribute),
                                  size_hint_y=None,
                                  height=50,
                                  halign='right'))
            self.add_widget(
                Label(text=str(fruit_data[self.text][attribute]),
                      size_hint_y=None,
                      height=50))

##################
# The Main View


class CascadingView(GridLayout):
    '''Implementation of a master-detail style view, with a scrollable list of
    fruit categories on the left, a list of fruits for the selected category in
    the middle, and a detail view of the selected fruit on the right.

    This example uses :class:`ListAdapter`. See an equivalent treatment that
    uses :class:`DictAdapter` in list_cascade_dict.py.
    '''

    def __init__(self, **kwargs):
        kwargs['cols'] = 3
        super(CascadingView, self).__init__(**kwargs)

        app = App.app()

        # For the fruit categories list on the left, we use a ListAdapter, for
        # which we set the data to the list of CategoryItem instances.
        #
        # The args_converter only pulls the name property from these instances,
        # adding also size_hint_y and height.
        #
        # The adapters are on auto-selection (allow_empty_selection=False).
        #
        self.add_widget(ListView(adapter=app.fruit_categories_list_adapter,
                                 size_hint=(.2, 1.0)))
        self.add_widget(ListView(adapter=app.current_fruits_adapter,
                                 size_hint=(.2, 1.0)))
        self.add_widget(ObjectView(adapter=app.current_fruit_adapter,
                                   size_hint=(.6, 1.0)))

############
# The App

class CascadeApp(App):

    def __init__(self, **kwargs):
        super(CascadeApp, self).__init__(**kwargs)

        self.fruit_categories_data = \
                [CategoryItem(**fruit_categories[c])
                        for c in sorted(fruit_categories)]

        self.fruit_data = \
                [FruitItem(**fruit_dict)
                        for fruit_dict in fruit_data_list_of_dicts]

        ######################
        #  CONTROLLER LAYER

        # Build the app's controller and adapter system (the "controller" layer
        # of the app) as instances on the app, so they will be generally
        # avaiable throught the app. In this small app, they are just needed in
        # the main views, but in a larger app, there could be multiple uses.

        list_item_args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
                                               'size_hint_y': None,
                                               'height': 25}

        # NOTE: In a real app (larger), these controllers and adapters would
        #       contain more code, and would probably be held in controllers
        #       and adapters directories within the app file structure.
        #
        #       There is a flow from one to the next, reflecting the cascade of
        #       connections, involving the data and selection properties of
        #       controllers and adapters, and of accessory transform
        #       properties.

        self.fruits = ListController(
                data=self.fruit_data,
                allow_empty_selection=False)

        self.fruit_categories = ListController(
                data=self.fruit_categories_data,
                allow_empty_selection=False)

        self.fruit_categories_list_adapter = ListAdapter(
                data=Binding(source=self.fruit_categories, prop='data'),
                args_converter=list_item_args_converter,
                selection_mode='single',
                allow_empty_selection=False,
                cls=ListItemButton)

        self.current_category_view = ObjectController(
                data=Binding(source=self.fruit_categories_list_adapter,
                             prop='selection',
                             mode=binding_modes.FIRST_ITEM))

        self.current_category = TransformController(
                data=Binding(source=self.current_category_view,
                             prop='data',
                             transform=lambda v: App.app().fruit_categories_data[v.index]))

        def fruits_for_category(category):
            # TODO: The lambda commented out below has the reference to
            #       App.app().current_category.data.fruits inside a list
            #       comprehension, which results in repeated calls. Here we do
            #       the call once, and use the result in the comprehension.
            #       Also tried the lambda with a generator.
            cat_fruits = App.app().current_category.data.fruits
            return [f for f in App.app().fruit_data if f.name in cat_fruits]

        self.category_fruits = TransformController(
                data=Binding(source=self.current_category,
                             prop='data',
                             transform=(binding_transforms.TRANSFORM, fruits_for_category)))
                                 #lambda fruits: [f for f in App.app().fruits.data if f.name in App.app().current_category.data.fruits])))

        self.current_fruits_adapter = ListAdapter(
                data=Binding(source=self.category_fruits, prop='data'),
                args_converter=list_item_args_converter,
                selection_mode='single',
                allow_empty_selection=False,
                cls=ListItemButton)

        self.current_fruit = TransformController(
                data=Binding(source=self.current_fruits_adapter,
                             prop='selection',
                             mode=binding_modes.FIRST_ITEM,
                             transform=(binding_transforms.TRANSFORM,
                                        lambda v: App.app().current_fruits_adapter.data[v.index])))

        self.current_fruit_adapter = ObjectAdapter(
                data=Binding(source=self.current_fruit,
                             prop='data'),
                args_converter=lambda row_index, fruit: {'text': fruit.name},
                cls=FruitDetailView)

        # selection_mode is single for both list adapters.
        # allow_empty_selection is False, because we always want a selected
        # category, so that the second list will be populated, and likewise, we
        # always want a fruit to be selected, so that detail view on the right
        # is updated. We instruct the list adapters to build list item views
        # using the provided cls, ListItemButton.

    def build(self):
        return CascadingView(width=800)


if __name__ in ('__main__'):
    CascadeApp().run()
