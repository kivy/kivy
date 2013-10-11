from kivy.app import App
from kivy.binding import DataBinding
from kivy.controllers.objectcontroller import ObjectController
from kivy.enums import binding_modes


class CurrentFruitController(ObjectController):

    def __init__(self, **kwargs):
        kwargs['data_binding'] = DataBinding(
                source=App.app().current_fruits_controller,
                prop='selection',
                mode=binding_modes.FIRST_ITEM)
        super(CurrentFruitController, self).__init__(**kwargs)
