from kivy.app import App
from kivy.binding import DataBinding
from kivy.controllers.listcontroller import ListController
from kivy.enums import binding_modes


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
