from kivy.app import App
from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.models import SelectableDataItem
from kivy.controllers.listcontroller import ListController
from kivy.controllers.objectcontroller import ObjectController
from kivy.properties import AliasProperty
from kivy.properties import ObjectProperty
from kivy.selection import SelectionTool
from kivy.selection import selection_schemes
from kivy.selection import selection_update_methods
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.listview import ListItemButton
from kivy.uix.listview import ListView

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

class FruitDetailView(GridLayout):

    name = ObjectProperty('', allownone=True)

    def __init__(self, **kwargs):
        kwargs['cols'] = 2

        controller = None

        if isinstance(kwargs['name'], ObjectController):
            controller = kwargs['name']
            kwargs['name'] = controller.name

        super(FruitDetailView, self).__init__(**kwargs)

        if controller:
            controller.bind(name=self.setter('name'))

        self.bind(name=self.redraw)

        self.redraw()

    def redraw(self, *args):
        self.clear_widgets()
        if self.name:
            self.add_widget(Label(text="Name:", halign='right'))
            self.add_widget(Label(text=self.name))
            for attribute in fruit_data_attributes:
                self.add_widget(Label(text="{0}:".format(attribute),
                                      halign='right'))
                self.add_widget(
                    Label(text=str(fruit_data[self.name][attribute])))


#################
#  CONTROLLERS

# Controllers (three list controllers and one object controller):

class FruitCategoriesController(ListController):

    def load_data(self):
        # To instantiate CategoryItem instances, we use the dictionary- style
        # fixtures data in fruit_categegories (See import above), which is also
        # used by other list examples. The double asterisk usage here is for
        # setting arguments from a dict in calls to instantiate the custom data
        # item classes defined above.

        # fruit_categories is a dict of dicts.
        self.data = \
            [CategoryItem(**fruit_categories[c]) for c in sorted(fruit_categories)]



class FruitsController(ListController):

    def load_data(self):

        # fruit_data_list_of_dicts is a list of dicts, already sorted.
        self.data = \
            [FruitItem(**fruit_dict) for fruit_dict in fruit_data_list_of_dicts]


class CurrentFruitsController(ListController):

    def update(self, *args):

        fruit_categories_adapter = args[0]

        if len(fruit_categories_adapter.selection) == 0:
            self.data = []
            return

        category = \
                fruit_categories[fruit_categories_adapter.selection[0].text]

        # We are responsible with resetting the data. In this example, we are
        # using lists of instances of the classes defined below, CategoryItem
        # and FruitItem. We assume that the names of the fruits are unique,
        # so we look up items by name.
        #
        app = App.get_running_app()
        self.data = \
            [f for f in app.fruits_controller.data if f.name in category['fruits']]

        # Also, see the examples that use dict records.


class CurrentFruitController(ObjectController):

    def get_name(self):
        if self.data:
            return self.data.name
        else:
            return ''

    name = AliasProperty(get_name, None, bind=('data', ))

    def update(self, *args):

        list_adapter = args[0]

        fruits_selection = args[1]

        if not fruits_selection:
            self.data = None
            return

        fruit_view = fruits_selection[0]

        # Or, above, use this convenience method:
        # fruit_view = list_adapter.get_first_selected()

        self.data = list_adapter.data[fruit_view.index]


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

        app = App.get_running_app()

        list_item_args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
                                               'size_hint_y': None,
                                               'height': 25}

        # Add a fruit categories list on the left. We use ListAdapter, for
        # which we set the data argument to the list of CategoryItem
        # instances from above. The args_converter only pulls the name
        # property from these instances, adding also size_hint_y and height.
        # selection_mode is single, because this list will "drive" the second
        # list defined below. allow_empty_selection is False, because we
        # always want a selected category, so that the second list will be
        # populated. Finally, we instruct ListAdapter to build list item views
        # using the provided cls, ListItemButton.
        #
        # We take some defaults here, including the selection scheme used in
        # the adapter. The default is VIEW_ON_DATA, which means that any
        # selection state available in the data is read on the initial creation
        # of item view instances that represent the data, but selection of the
        # data items is updated afterwards. (You can get the selected view
        # instances from fruit_categories_list_adapter.selection, and from
        # their index values find the corresponding data items).
        #
        fruit_categories_list_adapter = \
            ListAdapter(
                    data=app.fruit_categories_controller,
                    args_converter=list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=False,
                    cls=ListItemButton)

        fruit_categories_list_view = \
                ListView(adapter=fruit_categories_list_adapter,
                         size_hint=(.2, 1.0))

        self.add_widget(fruit_categories_list_view)

        # Add a fruits list in the middle. The items in the list depend on the
        # selected fruit category in the first list, so we set a
        # list controller to hold fruits based on the category selection.
        #
        fruit_categories_list_adapter.bind(selection=app.current_fruits_controller.update)

        fruits_adapter = ListAdapter(
                        data=app.current_fruits_controller,
                        args_converter=list_item_args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        cls=ListItemButton)

        fruits_view = \
                ListView(adapter=fruits_adapter, size_hint=(.2, 1.0))

        self.add_widget(fruits_view)

        fruits_adapter.bind(selection=app.current_fruit_controller.update)

        # Add a Detail view, for a given fruit, on the right:
        #
        detail_view = FruitDetailView(
                name=app.current_fruit_controller,
                size_hint=(.6, 1.0))

        self.add_widget(detail_view)

        # Load the data.

        # Load the fruits_controller first. It does not trigger the cascade,
        # (loading the fruit_categories_controller does that), but the fruits
        # data should be loaded and ready.
        app.fruits_controller.load_data()

        # Now load the fruit categories controller to initiate the cascade.
        app.fruit_categories_controller.load_data()


############
# The App

class CascadeApp(App):

    def __init__(self, **kwargs):
        super(CascadeApp, self).__init__(**kwargs)

        # Instantiate controllers, but do not load data into them yet.
        self.fruit_categories_controller = FruitCategoriesController()
        self.fruits_controller = FruitsController()
        self.current_fruits_controller = CurrentFruitsController()
        self.current_fruit_controller = CurrentFruitController()

    def build(self):

        return CascadingView(width=800)

if __name__ in ('__main__'):
    CascadeApp().run()
