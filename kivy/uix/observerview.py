'''
ObserverView
============

.. versionadded:: 1.5

:class:`ObserverView` is a container for a view that observes an object held
by an :class:`ObjectAdapter` instance. It is similar to :class:`ListView` in
the way an adapter and view instance are held, and in the way a get_view()
method works in concert with the adapter. It only has to manage one object,
however, so is a bit simpler. The update() method is the analog of the
populate() method in :class:`ListView`.

A binding is created between the :class:`ObjectAdapter` obj and self.update().
When obj changes, update() will add the contained view anew and, in turn, will
call its update() method for refreshing on the obj value.
'''

from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout


class ObserverView(BoxLayout):

    adapter = ObjectProperty(None)
    '''This is always an :class:`ObjectAdapter` instance. The obj value in the
    object adapter is at the heart of operations here. This is the observed
    value whose changes trigger refreshing of the contained view.
    '''

    view_instance = ObjectProperty(None, allownone=True)
    '''The view_instance property holds the present contained view.
    '''

    def __init__(self, **kwargs):
        super(ObserverView, self).__init__(**kwargs)
        self.adapter.bind(obj=self.update)
        self.update(self.adapter)

    def set_view(self, view):
        self.view_instance = view

    def get_view(self):
        return self.view_instance

    def update(self, object_adapter, *args):
        self.clear_widgets()
        self.view_instance = object_adapter.get_view()
        v = self.get_view()
        if v is not None:
            self.add_widget(v)
            v.update(object_adapter, *args)
