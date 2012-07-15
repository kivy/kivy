from kivy.properties import ListProperty
from kivy.lang import Builder
from kivy.uix.mixins.selection import SelectionSupport
from kivy.adapters.adapter import Adapter


class ListAdapter(SelectionSupport, Adapter):
    '''Adapter around a simple Python list
    '''
    data = ListProperty([])

    def __init__(self, data, **kwargs):
        if type(data) not in (tuple, list):
            raise Exception('ListAdapter: input must be a tuple or list')
        super(ListAdapter, self).__init__(**kwargs)

        # Reset and update selection, in SelectionSupport, if data
        # gets reset.
        self.bind(data=self.initialize_selection)

        # Do the initial set -- triggers initialize_selection()
        self.data = data

    def get_count(self):
        return len(self.data)

    def get_item(self, index):
        if index < 0 or index >= len(self.data):
            return None
        return self.data[index]

    def get_view(self, index):
        item = self.get_item(index)
        if item is None:
            return None

        item_args = None
        if self.args_converter:
            item_args = self.args_converter(item)
        else:
            item_args = item

        if self.cls:
            print 'CREATE VIEW FOR', index
            instance = self.cls(self, **item_args)
            return instance
        else:
            return Builder.template(self.template, **item_args)

    # [TODO] Things to think about:
    #
    # There are other possibilities:
    #
    #         Additional possibilities, to those stubbed out in
    #         methods below.
    #
    #             - a boolean for whether or not editing of item_view_instances
    #               is allowed
    #
