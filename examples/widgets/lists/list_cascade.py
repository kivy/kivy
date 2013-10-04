from kivy.app import App
from kivy.binding import DataBinding
from kivy.controllers.listcontroller import ListController
from kivy.controllers.objectcontroller import ObjectController
from kivy.enums import binding_modes
from kivy.lang import Builder
from kivy.models import SelectableDataItem
from kivy.uix.gridlayout import GridLayout

from fixtures import fruit_categories
from fixtures import fruit_data_list_of_dicts

# This example illustrates a cascading connection from the selection of one
# list view to another. In this example the lists are restricted to single
# selection. The list on the left is a simple list view using a simple list
# controller. The list in the middle has a special list controller which
# observes the selection in the first list and uses that selected item in a
# transform filter method to get the current fruit items.  The view on the
# right is an ObjectView that uses an ObjectController tied to the selection of
# the middle list.

# It is not difficult to make your own data items, because you can define
# custom data item classes that subclass SelectableDataItem:


class CategoryItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(CategoryItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.fruits = kwargs.get('fruits', [])


class FruitItem(SelectableDataItem):
    def __init__(self, **kwargs):
        super(FruitItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.serving_size = kwargs.get('Serving Size', '')
        self.data = kwargs.get('data', [])

# Quote from ListView docs about data items: "They MUST be subclasses of
# SelectableDataItem, or the equivalent, because each data item needs an all
# important "Kivy selection" object, abbreviated **ksel** in internal coding.
# Without a ksel, a list item will not respond to user action, and will appear
# just as a dumb list item, along for the ride."

##############################################################################
#
#    Views, defined in kv language.
#
#        In a real app, a good practice is to put views in their own
#        directory, views/, using subdirectories as desired, with each view
#        defined in a .py file with the kv part as a Builder.load_string(),
#        as shown below, along with the python definition of associated classes.
#        This way you can import a given view where you need it in your app,
#        e.g., from views.screens.loading_screen import LoadingScreen (Don't
#        forget to put an empty __init__.py file in each directory).
#
#        NOTE the use of a dynamic classes for ThumbnailedListItem,
#        FruitDetailView, and a couple of others, which in Kivy versions prior
#        to 1.8 would have been defined as templates, now removed.
#
#        NOTE also the declaration of bindings to the controllers used by the
#        list views, in a declarative style of defining bindings.

Builder.load_string("""
#:import DataBinding kivy.binding.DataBinding
#:import binding_modes kivy.enums.binding_modes
#:import ListItemButton kivy.uix.listview.ListItemButton
#:import fruit_data fixtures.fruit_data

# This is a dynamic class.
<FruitCategoryListItemButton@ListItemButton>:
    size_hint_y: None
    height: 25
    args_converter: lambda index, data_item: {'text': data_item.name}

# This is a dynamic class.
<FruitListItem@SelectableView+BoxLayout>:
    index: self.index
    text: self.text
    size_hint_y: None
    height: 25
    args_converter: lambda index, data_item: {'text': data_item.name}
    Image
        source: "fruit_images/{0}.32.jpg".format(root.text) if root.text else ''
    ListItemButton:
        index: root.index
        text: root.text if root.text else ''
        on_release: self.parent.trigger_action(duration=0)

# This is a dynamic class.
<AttributeLabel@Label>:
    size_hint_y: None
    height: 50
    halign: 'right'

# This is a dynamic class.
<AttributeValue@Label>:
    size_hint_y: None
    height: 50

# This is a dynamic class.
<FruitDetailView@GridLayout+SelectableView>:
    cols: 2
    size_hint: 1, None
    text: root.text if root.text else ''
    args_converter: lambda index, data_item: {'text': data_item.name}

    AttributeLabel:
        text: 'Name:'
    Label:
        text: root.text
        size_hint_y: None
        height: 50

    AttributeLabel:
        text: 'Calories:'
    AttributeValue:
        text: str(fruit_data[root.text]['Calories']) if root.text else ''

    AttributeLabel:
        text: 'Calories from Fat:'
    AttributeValue:
        text: str(fruit_data[root.text]['Calories from Fat']) if root.text else ''

    AttributeLabel:
        text: 'Total Fat:'
    AttributeValue:
        text: str(fruit_data[root.text]['Total Fat']) if root.text else ''

    AttributeLabel:
        text: 'Sodium:'
    AttributeValue:
        text: str(fruit_data[root.text]['Sodium']) if root.text else ''

    AttributeLabel:
        text: 'Potassium:'
    AttributeValue:
        text: str(fruit_data[root.text]['Potassium']) if root.text else ''

    AttributeLabel:
        text: 'Total Carbo-hydrate:'
    AttributeValue:
        text: str(fruit_data[root.text]['Total Carbo-hydrate']) if root.text else ''

    AttributeLabel:
        text: 'Dietary Fiber:'
    AttributeValue:
        text: str(fruit_data[root.text]['Dietary Fiber']) if root.text else ''

    AttributeLabel:
        text: 'Sugars:'
    AttributeValue:
        text: str(fruit_data[root.text]['Sugars']) if root.text else ''

    AttributeLabel:
        text: 'Protein:'
    AttributeValue:
        text: str(fruit_data[root.text]['Protein']) if root.text else ''

    AttributeLabel:
        text: 'Vitamin A:'
    AttributeValue:
        text: str(fruit_data[root.text]['Vitamin A']) if root.text else ''

    AttributeLabel:
        text: 'Vitamin C:'
    AttributeValue:
        text: str(fruit_data[root.text]['Vitamin C']) if root.text else ''

    AttributeLabel:
        text: 'Calcium:'
    AttributeValue:
        text: str(fruit_data[root.text]['Calcium']) if root.text else ''

    AttributeLabel:
        text: 'Iron:'
    AttributeValue:
        text: str(fruit_data[root.text]['Iron']) if root.text else ''

# The main view for the app.
<CascadingView>:
    cols: 3
    fruit_categories_list_view: fruit_categories_list_view
    fruits_list_view: fruits_list_view
    fruit_view: fruit_view

    ListView:
        id: fruit_categories_list_view
        size_hint: .2, 1.0
        list_item_class: 'FruitCategoryListItemButton'
        DataBinding:
            source: app.categories_controller
            prop: 'data'

    ListView:
        id: fruits_list_view
        size_hint: .2, 1.0
        list_item_class: 'FruitListItem'
        DataBinding:
            source: app.current_fruits_controller
            prop: 'data'

    ObjectView:
        id: fruit_view
        size_hint: .6, 1.0
        list_item_class: 'FruitDetailView'
        DataBinding:
            source: app.current_fruit_controller
            prop: 'data'
""")


class CascadingView(GridLayout):
    '''Implementation of a master-detail style view, with a scrollable list
    of fruit categories on the left, a list of fruits for the selected
    category in the middle, and a detail view on the right.
    '''
    pass


############################################################################
#
#    Controllers
#
#        In a real app, a good practice is to put controllers in their own
#        directory called controllers/, and have one controller per file,
#        imported into your App class, so you can refer to them as
#        app.fruits_controller, app.categories_controller, etc. Controllers are
#        typically shared by different parts of a larger application.

class FruitsController(ListController):

    def __init__(self, **kwargs):
        kwargs['allow_empty_selection'] = False
        super(FruitsController, self).__init__(**kwargs)


class CategoriesController(ListController):

    def __init__(self, **kwargs):
        kwargs['allow_empty_selection'] = False
        super(CategoriesController, self).__init__(**kwargs)


class CurrentCategoryController(ObjectController):

    def __init__(self, **kwargs):
        kwargs['data_binding'] = DataBinding(
                source=App.app().categories_controller,
                prop='selection',
                mode=binding_modes.FIRST_ITEM)
        super(CurrentCategoryController, self).__init__(**kwargs)


class CurrentFruitsController(ListController):

    def get_current_fruits(self, category):
        if not category:
            return []
        all_fruits = App.app().fruits_controller.all()
        return [fruit for fruit in all_fruits
                if fruit.name in category.fruits]

    def __init__(self, **kwargs):
        kwargs['allow_empty_selection'] = False
        kwargs['data_binding'] = DataBinding(
                source=App.app().categories_controller,
                prop='selection',
                mode=binding_modes.FIRST_ITEM,
                transform=self.get_current_fruits)
        super(CurrentFruitsController, self).__init__(**kwargs)


class CurrentFruitController(ObjectController):

    def __init__(self, **kwargs):
        kwargs['data_binding'] = DataBinding(
                source=App.app().current_fruits_controller,
                prop='selection',
                mode=binding_modes.FIRST_ITEM)
        super(CurrentFruitController, self).__init__(**kwargs)


class CascadeApp(App):

    def __init__(self, **kwargs):
        super(CascadeApp, self).__init__(**kwargs)

        self.fruits_controller = FruitsController()
        self.categories_controller = CategoriesController()
        self.current_category_controller = CurrentCategoryController()
        self.current_fruits_controller = CurrentFruitsController()
        self.current_fruit_controller = CurrentFruitController()

    def list_item_class_args(self, row_index, selectable):
        return {'text': selectable.name,
                'size_hint_y': None,
                'height': 25}

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
