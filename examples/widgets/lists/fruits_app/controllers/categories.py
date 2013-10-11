from kivy.controllers.listcontroller import ListController


class CategoriesController(ListController):

    def __init__(self, **kwargs):
        kwargs['allow_empty_selection'] = False
        super(CategoriesController, self).__init__(**kwargs)
