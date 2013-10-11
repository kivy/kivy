from kivy.app import App
from kivy.binding import DataBinding
from kivy.controllers.objectcontroller import ObjectController
from kivy.enums import binding_modes


class CurrentCategoryController(ObjectController):

    def __init__(self, **kwargs):
        kwargs['data_binding'] = DataBinding(
                source=App.app().categories_controller,
                prop='selection',
                mode=binding_modes.FIRST_ITEM)
        super(CurrentCategoryController, self).__init__(**kwargs)
