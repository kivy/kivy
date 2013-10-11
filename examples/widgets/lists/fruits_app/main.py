from kivy.app import App
from kivy.binding import DataBinding
from kivy.controllers.listcontroller import ListController
from kivy.controllers.objectcontroller import ObjectController
from kivy.enums import binding_modes
from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout

from fixtures import fruit_categories
from fixtures import fruit_data_list_of_dicts

from controllers.categories import CategoriesController
from controllers.current_category import CurrentCategoryController
from controllers.current_fruit import CurrentFruitController
from controllers.current_fruits import CurrentFruitsController
from controllers.fruits import FruitsController

from models.category import CategoryItem
from models.fruit import FruitItem

from views.attribute_label import AttributeLabel
from views.attribute_value_label import AttributeValueLabel
from views.cascading_view import CascadingView
from views.fruit_category_list_item_button import FruitCategoryListItemButton
from views.fruit_detail_view import FruitDetailView
from views.fruit_list_item import FruitListItem

# See the list_cascade.py example for a single-file version of this app. Here
# we break everything out into files, which is a more likely approach for a
# larger app.

# This example illustrates a cascading connection from the selection of one
# list view to another. In this example the lists are restricted to single
# selection. The list on the left is a simple list view using a simple list
# controller. The list in the middle has a special list controller which
# observes the selection in the first list and uses that selected item in a
# transform filter method to get the current fruit items.  The view on the
# right is an ObjectView that uses an ObjectController tied to the selection of
# the middle list.

class CascadeApp(App):

    def __init__(self, **kwargs):
        super(CascadeApp, self).__init__(**kwargs)

        self.fruits_controller = FruitsController()
        self.categories_controller = CategoriesController()
        self.current_category_controller = CurrentCategoryController()
        self.current_fruits_controller = CurrentFruitsController()
        self.current_fruit_controller = CurrentFruitController()

    def build(self):
        self.cascading_view = CascadingView(width=800)
        return self.cascading_view

    def on_start(self):

        # Load data into controllers. Put some thinking into when you want or
        # need to load data into controllers. Here we illustrate how the app
        # can be initialized with empty controllers, only to be filled later,
        # in this case on app start up.

        # fruit_data_list_of_dicts is a list of dicts, already sorted.
        self.fruits_controller.data = \
            [FruitItem(**fruit_dict) for fruit_dict in fruit_data_list_of_dicts]

        # fruit_categories is a dict of dicts.
        self.categories_controller.data = \
            [CategoryItem(**fruit_categories[c]) for c in sorted(fruit_categories)]


if __name__ in ('__main__'):
    CascadeApp().run()
