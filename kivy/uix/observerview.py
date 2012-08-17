'''
ObserverView
============

.. versionadded:: 1.5

:class:`ObserverView` is a container for a view that observes an object held
by an :class:`SelectionAdapter` instance. It is similar to :class:`ListView`
in the way an adapter and view instance are held, and in the way a get_view()
method works in concert with the adapter. It only has to manage one object,
however, so is a bit simpler. The update() method is the analog of the
populate() method in :class:`ListView`.
'''

from kivy.adapters.selectionadapter import SelectionAdapter
from kivy.adapters.collectionadapter import CollectionAdapter
from kivy.properties import ObjectProperty, ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout


class ObserverView(BoxLayout):

    adapter = ObjectProperty(None)
    '''This is always a :class:`SelectionAdapter` instance. The obj value in
    the object adapter is at the heart of operations here. This is the
    observed value whose changes trigger refreshing of the contained view.
    '''

    view_instance = ObjectProperty(None, allownone=True)
    '''The view_instance property holds the present contained view.
    '''

    target_property_name = StringProperty('')

    def __init__(self, **kwargs):
        if not 'observed' in kwargs:
            raise Exception("ObserverView: observed object required")
        if not 'target_property_name' in kwargs:
            raise Exception("ObserverView: target_property_name required")
        if not 'adapter' in kwargs:
            if isinstance(kwargs['observed'], CollectionAdapter):
                kwargs['adapter'] = SelectionAdapter(**kwargs)

        print kwargs
        super(ObserverView, self).__init__(**kwargs)

        if isinstance(self.adapter.observed, CollectionAdapter):
            self.adapter.bind(obj=self.update)

        self.update(self.adapter)

    def set_view(self, view):
        self.view_instance = view

    def get_view(self):
        return self.view_instance

    def update(self, adapter, *args):
        print 'ObserverView, update', adapter
        self.clear_widgets()
        self.view_instance = adapter.get_view()
        v = self.get_view()
        if v is not None:
            if type(self.adapter) is SelectionAdapter:
                self.adapter.bind(obj=v.setter(self.target_property_name))
            self.add_widget(v)
