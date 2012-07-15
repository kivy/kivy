from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.listview import ListView, ListAdapter
from kivy.uix.mixins.selection import SelectionObserver, SelectableItem
from kivy.properties import ListProperty, StringProperty, ObjectProperty
from kivy.clock import Clock
from kivy.graphics.instructions import Callback

# This is an expansion on the "master-detail" example to illustrate
# cascading from the selection of one list view to another.

# Generic list item will do fine for both list views:

class ListItem(SelectableItem, Button):
    selected_color = ListProperty([1., 0., 0., 1])
    deselected_color = None

    def __init__(self, list_adapter, **kwargs):
        self.list_adapter = list_adapter
        super(ListItem, self).__init__(**kwargs)

        # Set deselected_color to be default Button bg color.
        self.deselected_color = self.background_color

        self.bind(on_release=self.handle_selection)

    def handle_selection(self, button):
        self.list_adapter.handle_selection(self)

    def select(self, *args):
        print self.text, 'is now selected'
        self.background_color = self.selected_color

    def deselect(self, *args):
        print self.text, 'is now unselected'
        self.background_color = self.deselected_color

    def __repr__(self):
        return self.text


class FruitsListView(SelectionObserver, ListView):
    # The fruit categories list view can be a simple ListView,
    # but the fruits list, showing fruits for a given category,
    # will be a SelectionObserver, changing when fruit category
    # changes.
    def __init__(self, **kwargs):
        super(FruitsListView, self).__init__(**kwargs)

    # Observed selection is fruit categories list.
    def observed_selection_changed(self, observed_selection):
        if len(observed_selection.selection) == 0:
            return

        # Clear the previously built views.
        self.item_view_instances = {}

        # Single selection is operational for fruit categories list.
        selected_object = observed_selection.selection[0]

        if type(selected_object) is str:
            fruit_category = selected_object
        else:
            fruit_category = str(selected_object)

        # Reset data for the adapter. This will trigger a call
        # to self.adapter.initialize_selection().
        self.adapter.data = fruit_categories[fruit_category]

        #print self.adapter.selection[0], self.adapter.selection[0].background_color

        self.populate()

        self.canvas.ask_update()

        print 'just added or updated fruit category'


class DetailView(SelectionObserver, GridLayout):
    fruit_name = StringProperty('')

    def __init__(self, **kwargs):
        kwargs['cols'] = 2
        super(DetailView, self).__init__(**kwargs)
        self.bind(fruit_name=self.redraw)

    def redraw(self, *args):
        self.clear_widgets()
        self.add_widget(Label(text="Name:", halign='right'))
        self.add_widget(Label(text=self.fruit_name))
        for category in descriptors:
            self.add_widget(Label(text="{0}:".format(category),
                                  halign='right'))
            self.add_widget(
                    Label(text=str(fruit_data[self.fruit_name][category])))

    def observed_selection_changed(self, observed_selection):
        if len(observed_selection.selection) == 0:
            return

        selected_object = observed_selection.selection[0]

        if type(selected_object) is str:
            self.fruit_name = selected_object
        else:
            self.fruit_name = str(selected_object)
        print 'just added or updated detail label'


class CascadingView(GridLayout):
    '''Implementation of a master-detail style view, with a scrollable list
    of fruit categories on the left (source list), a list of fruits for the
    selected category in the middle, and a detail view on the right.
    '''

    fruit_categories_list_adapter = ObjectProperty(None)
    fruit_categories_list_view = ObjectProperty(None)

    fruits_list_adapter = ObjectProperty(None)
    fruits_list_view = ObjectProperty(None)

    detail_view = ObjectProperty(None)

    def __init__(self, fruit_categories, fruits, **kwargs):
        kwargs['cols'] = 3
        kwargs['size_hint'] = (1.0, 1.0)
        super(CascadingView, self).__init__(**kwargs)

        list_item_args_converter = lambda x: {'text': x,
                                              'size_hint_y': None,
                                              'height': 25}

        # Fruit categories list on the left:
        #
        self.fruit_categories_list_adapter = \
                ListAdapter(fruit_categories,
                        args_converter=list_item_args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        cls=ListItem)
        self.fruit_categories_list_view = \
                ListView(adapter=self.fruit_categories_list_adapter,
                         size_hint=(.2, 1.0))
        self.add_widget(self.fruit_categories_list_view)

        # Fruits, for a given category, in the middle:
        #
        self.fruits_list_adapter = \
                ListAdapter(fruits,
                        args_converter=list_item_args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        cls=ListItem)
        self.fruits_list_view = \
                FruitsListView(adapter=self.fruits_list_adapter,
                         size_hint=(.2, 1.0))
        self.add_widget(self.fruits_list_view)

        # Set the fruits_list_view as an observer of the selection of
        # the fruit category.
        self.fruit_categories_list_adapter.register_selection_observer(
                self.fruits_list_view)

        # Detail view, for a given fruit, on the right:
        #
        self.detail_view = DetailView(size_hint=(.6, 1.0))
        self.add_widget(self.detail_view)

        # Manually initialize detail view to show first object of list view,
        # which will be auto-selected, but the observed_selection_changed
        # call would have already fired.
        #
        self.fruits_list_adapter.register_selection_observer(self.detail_view)

# Data from http://www.fda.gov/Food/LabelingNutrition/\
#                FoodLabelingGuidanceRegulatoryInformation/\
#                InformationforRestaurantsRetailEstablishments/\
#                ucm063482.htm
fruit_categories = \
        {'Melons': ['Cantaloupe', 'Honeydew Melon', 'Watermelon'],
         'Tree Fruits': ['Apple', 'Avocado, California', 'Banana', 'Nectarine',
                         'Peach', 'Pear', 'Pineapple', 'Plums',
                         'Sweet Cherries'],
         'Citrus Fruits': ['Grapefruit', 'Lemon', 'Lime', 'Orange',
                           'Tangerine'],
         'Miscellaneous Fruits': ['Grapes', 'Kiwifruit', 'Strawberries']}
descriptors = """(gram weight/ ounce weight)	Calories	Calories from Fa
t	Total Fat	Sodium	Potassium	Total Carbo-hydrate	Dietary Fiber	Suga
rs	Protein	Vitamin A	Vitamin C	Calcium	Iron""".replace('\n', '')
descriptors = [item.strip() for item in descriptors.split('\t')]
units = """(g) 	(%DV)	(mg) 	(%DV)	(mg) 	(%DV)	 (g) 	(%DV)	 (g)
(%DV)	 (g) 	 (g) 	(%DV)	(%DV)	(%DV)	(%DV)""".replace('\n', '')
units = [item.strip() for item in units.split('\t')]
raw_fruit_data = [
{'name':'Apple',
 'Serving Size': '1 large (242 g/8 oz)',
 'data': [130, 0, 0, 0, 0, 0, 260, 7, 34, 11, 5, 20, 25, 1, 2, 8, 2, 2]},
{'name':'Avocado, California',
 'Serving Size': '1/5 medium (30 g/1.1 oz)',
 'data': [50, 35, 4.5, 7, 0, 0, 140, 4, 3, 1, 1, 4, 0, 1, 0, 4, 0, 2]},
{'name':'Banana',
 'Serving Size': '1 medium (126 g/4.5 oz)',
 'data': [110, 0, 0, 0, 0, 0, 450, 13, 30, 10, 3, 12, 19, 1, 2, 15, 0, 2]},
{'name':'Cantaloupe',
 'Serving Size': '1/4 medium (134 g/4.8 oz)',
 'data': [50, 0, 0, 0, 20, 1, 240, 7, 12, 4, 1, 4, 11, 1, 120, 80, 2, 2]},
{'name':'Grapefruit',
 'Serving Size': '1/2 medium (154 g/5.5 oz)',
 'data': [60, 0, 0, 0, 0, 0, 160, 5, 15, 5, 2, 8, 11, 1, 35, 100, 4, 0]},
{'name':'Grapes',
 'Serving Size': '3/4 cup (126 g/4.5 oz)',
 'data': [90, 0, 0, 0, 15, 1, 240, 7, 23, 8, 1, 4, 20, 0, 0, 2, 2, 0]},
{'name':'Honeydew Melon',
 'Serving Size': '1/10 medium melon (134 g/4.8 oz)',
 'data': [50, 0, 0, 0, 30, 1, 210, 6, 12, 4, 1, 4, 11, 1, 2, 45, 2, 2]},
{'name':'Kiwifruit',
 'Serving Size': '2 medium (148 g/5.3 oz)',
 'data': [90, 10, 1, 2, 0, 0, 450, 13, 20, 7, 4, 16, 13, 1, 2, 240, 4, 2]},
{'name':'Lemon',
 'Serving Size': '1 medium (58 g/2.1 oz)',
 'data': [15, 0, 0, 0, 0, 0, 75, 2, 5, 2, 2, 8, 2, 0, 0, 40, 2, 0]},
{'name':'Lime',
 'Serving Size': '1 medium (67 g/2.4 oz)',
 'data': [20, 0, 0, 0, 0, 0, 75, 2, 7, 2, 2, 8, 0, 0, 0, 35, 0, 0]},
{'name':'Nectarine',
 'Serving Size': '1 medium (140 g/5.0 oz)',
 'data': [60, 5, 0.5, 1, 0, 0, 250, 7, 15, 5, 2, 8, 11, 1, 8, 15, 0, 2]},
{'name':'Orange',
 'Serving Size': '1 medium (154 g/5.5 oz)',
 'data': [80, 0, 0, 0, 0, 0, 250, 7, 19, 6, 3, 12, 14, 1, 2, 130, 6, 0]},
{'name':'Peach',
 'Serving Size': '1 medium (147 g/5.3 oz)',
 'data': [60, 0, 0.5, 1, 0, 0, 230, 7, 15, 5, 2, 8, 13, 1, 6, 15, 0, 2]},
{'name':'Pear',
 'Serving Size': '1 medium (166 g/5.9 oz)',
 'data': [100, 0, 0, 0, 0, 0, 190, 5, 26, 9, 6, 24, 16, 1, 0, 10, 2, 0]},
{'name':'Pineapple',
 'Serving Size': '2 slices, 3" diameter, 3/4" thick (112 g/4 oz)',
 'data': [50, 0, 0, 0, 10, 0, 120, 3, 13, 4, 1, 4, 10, 1, 2, 50, 2, 2]},
{'name':'Plums',
 'Serving Size': '2 medium (151 g/5.4 oz)',
 'data': [70, 0, 0, 0, 0, 0, 230, 7, 19, 6, 2, 8, 16, 1, 8, 10, 0, 2]},
{'name':'Strawberries',
 'Serving Size': '8 medium (147 g/5.3 oz)',
 'data': [50, 0, 0, 0, 0, 0, 170, 5, 11, 4, 2, 8, 8, 1, 0, 160, 2, 2]},
{'name':'Sweet Cherries',
 'Serving Size': '21 cherries; 1 cup (140 g/5.0 oz)',
 'data': [100, 0, 0, 0, 0, 0, 350, 10, 26, 9, 1, 4, 16, 1, 2, 15, 2, 2]},
{'name':'Tangerine',
 'Serving Size': '1 medium (109 g/3.9 oz)',
 'data': [50, 0, 0, 0, 0, 0, 160, 5, 13, 4, 2, 8, 9, 1, 6, 45, 4, 0]},
{'name':'Watermelon',
 'Serving Size': '1/18 medium melon; 2 cups diced pieces (280 g/10.0 oz)',
 'data': [80, 0, 0, 0, 0, 0, 270, 8, 21, 7, 1, 4, 20, 1, 30, 25, 2, 4]}]

fruit_data = {}
descriptors_and_units = dict(zip(descriptors, units))
for row in raw_fruit_data:
    fruit_data[row['name']] = {}
    fruit_data[row['name']] = dict({'Serving Size': row['Serving Size']},
            **dict(zip(descriptors_and_units.keys(), row['data'])))

if __name__ == '__main__':

    from kivy.base import runTouchApp

    # All fruit categories will be shown in the left left (first argument),
    # and the first category will be auto-selected -- Melons. So, set the
    # second list to show the melon fruits (second argument).
    fruit_categories_detail = CascadingView(fruit_categories.keys(),
            fruit_categories['Melons'], width=800)

    runTouchApp(fruit_categories_detail)
