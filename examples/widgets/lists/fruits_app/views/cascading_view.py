from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder


Builder.load_string("""
#:import DataBinding kivy.binding.DataBinding
#:import FruitCategoryListItemButton views.fruit_category_list_item_button.FruitCategoryListItemButton
#:import FruitListItem views.fruit_list_item.FruitListItem
#:import FruitDetailView views.fruit_detail_view.FruitDetailView


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
