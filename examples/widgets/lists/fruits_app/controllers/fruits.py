from kivy.controllers.listcontroller import ListController


class FruitsController(ListController):

    def __init__(self, **kwargs):
        kwargs['allow_empty_selection'] = False
        super(FruitsController, self).__init__(**kwargs)
