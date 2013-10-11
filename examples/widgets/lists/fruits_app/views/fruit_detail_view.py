from kivy.lang import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import SelectableView


Builder.load_string("""
#:import AttributeLabel views.attribute_label.AttributeLabel
#:import AttributeValueLabel views.attribute_value_label.AttributeValueLabel
#:import fruit_data fixtures.fruit_data

# This is not a dynamic class. See list_cascade.py for the same view made as a
# dynamic class. We need python imports to work for the file system definitions
# of widgets used here.

<FruitDetailView>:
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
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Calories']) if root.text else ''

    AttributeLabel:
        text: 'Calories from Fat:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Calories from Fat']) if root.text else ''

    AttributeLabel:
        text: 'Total Fat:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Total Fat']) if root.text else ''

    AttributeLabel:
        text: 'Sodium:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Sodium']) if root.text else ''

    AttributeLabel:
        text: 'Potassium:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Potassium']) if root.text else ''

    AttributeLabel:
        text: 'Total Carbo-hydrate:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Total Carbo-hydrate']) if root.text else ''

    AttributeLabel:
        text: 'Dietary Fiber:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Dietary Fiber']) if root.text else ''

    AttributeLabel:
        text: 'Sugars:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Sugars']) if root.text else ''

    AttributeLabel:
        text: 'Protein:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Protein']) if root.text else ''

    AttributeLabel:
        text: 'Vitamin A:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Vitamin A']) if root.text else ''

    AttributeLabel:
        text: 'Vitamin C:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Vitamin C']) if root.text else ''

    AttributeLabel:
        text: 'Calcium:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Calcium']) if root.text else ''

    AttributeLabel:
        text: 'Iron:'
    AttributeValueLabel:
        text: str(fruit_data[root.text]['Iron']) if root.text else ''
""")



class FruitDetailView(GridLayout, SelectableView):
    pass
