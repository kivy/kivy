from kivy.app import App
from kivy.adapters.listadapter import ListAdapter
from kivy.models import SelectableDataItem
from kivy.binding import Binding
from kivy.event import EventDispatcher
from kivy.properties import ListProperty
from kivy.properties import ObjectProperty
from kivy.properties import AliasProperty
from kivy.selection import SelectionTool
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
# list property that holds the base data from which the other user interface
# elements update in a cascade. The list in the middle uses a list property
# that is filled based on the selection in the first list.  The DetailView on
# the right uses an object property that is updated from the selection of the
# middle list.

##########
#  DATA

# The adapters and properties used below have Selection mixed in, automating
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

list_item_args_converter = \
                lambda row_index, selectable: {'text': selectable.name,
                                               'size_hint_y': None,
                                               'height': 25}

###########
# VIEWS


class FruitDetailView(GridLayout):

    name = ObjectProperty('', allownone=True)

    def __init__(self, **kwargs):
        kwargs['cols'] = 2

        prop_owner = None
        prop_name = None

        if isinstance(kwargs['name'], tuple):
            prop_owner, prop_name = kwargs['name']
            kwargs['name'] = getattr(prop_owner, prop_name)

        super(FruitDetailView, self).__init__(**kwargs)

        if prop_owner and prop_name:
            prop_owner.bind(**{prop_name: self.setter('name')})

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


#######################
# The Control System

class Control(EventDispatcher):

    fruit_categories_adapter = ObjectProperty()

    fruit_categories = ListProperty()
    fruits = ListProperty()

    category_selection = ListProperty()

    def get_current_fruits(self):
        if not self.category_selection:
            return []
        category_view = self.category_selection[0]
        category_item = self.fruit_categories[category_view.index]
        return [f for f in self.fruits if f.name in category_item.fruits]

    def set_current_fruits(self, value):
        self.current_fruits = value
    current_fruits = AliasProperty(get_current_fruits,
                                   set_current_fruits,
                                   bind=['category_selection', ])

    fruits_adapter = ObjectProperty()

    fruit_selection = ListProperty()

    def get_current_fruit_name(self):
        if not self.fruit_selection:
            return ''
        fruit_view = self.fruit_selection[0]
        return fruit_view.text if fruit_view else ''

    def set_current_fruit_name(self, value):
        self.current_fruit_name = value
    current_fruit_name = AliasProperty(get_current_fruit_name,
                                       set_current_fruit_name,
                                       bind=['fruit_selection'])

    def __init__(self, **kwargs):
        super(Control, self).__init__(**kwargs)

        self.fruit_categories_adapter = \
            ListAdapter(
                    data=Binding(source=self, prop='fruit_categories'),
                    args_converter=list_item_args_converter,
                    selection_mode='single',
                    allow_empty_selection=False,
                    cls=ListItemButton)

        self.fruit_categories_adapter.bind(
                selection=self.setter('category_selection'))

        self.fruits_adapter = ListAdapter(
                        data=Binding(source=self, prop='current_fruits'),
                        args_converter=list_item_args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        cls=ListItemButton)

        self.fruits_adapter.bind(
                selection=self.setter('fruit_selection'))


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

        control = Control()

        # Load the data, fruits first. It does not trigger the cascade, but needs to be loaded.
        control.fruits = [FruitItem(**fruit_dict) for fruit_dict in fruit_data_list_of_dicts]
        control.fruit_categories = [CategoryItem(**fruit_categories[c]) for c in sorted(fruit_categories)]

        self.add_widget(ListView(adapter=control.fruit_categories_adapter, size_hint=(.2, 1.0)))
        self.add_widget(ListView(adapter=control.fruits_adapter, size_hint=(.2, 1.0)))
        self.add_widget(FruitDetailView(name=(control, 'current_fruit_name'), size_hint=(.6, 1.0)))


############
# The App

class CascadeApp(App):

    def __init__(self, **kwargs):
        super(CascadeApp, self).__init__(**kwargs)

    def build(self):
        return CascadingView(width=800)

if __name__ in ('__main__'):
    CascadeApp().run()
