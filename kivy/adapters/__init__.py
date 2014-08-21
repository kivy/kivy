'''
Adapters
========

.. versionadded:: 1.5.0

An adapter is a mediating class that processes and presents data for use in
views. It does this by generating models, generally lists of
:class:`~kivy.uix.listview.SelectableView` items, that are consumed and
presented by views. Views are top-level widgets, such as a 
:class:`~kivy.uix.listview.ListView`, that allow users to scroll through
and (optionally) interact with your data.

Kivy adapters are modelled on the
`Adapter design pattern <http://en.wikipedia.org/wiki/Adapter_pattern>`_.

- **Adapters**: The base :class:`Adapter` is subclassed by the
  :class:`SimpleListAdapter` and :class:`ListAdapter`. The :class:`DictAdapter`
  is a more advanced and flexible subclass of :class:`ListAdapter`.

    :doc:`api-kivy.adapters.adapter`,
    :doc:`api-kivy.adapters.simplelistadapter`,
    :doc:`api-kivy.adapters.listadapter`,
    :doc:`api-kivy.adapters.dictadapter`.

- **Models**: The data for which an adapter serves as a bridge to views can be
  any sort of data. However, for convenience, model mixin classes can ease the
  preparation or shaping of data for use in the system. For selection
  operations, the :class:`SelectableDataItem` can optionally prepare data items
  to provide and receive selection information (data items are not required to
  be "selection-aware", but in some cases it may be desired).

    :doc:`api-kivy.adapters.models`.

- **Args Converters**: Argument converters are made by the application
  programmer to do the work of converting data items to argument dictionaries
  suitable for instantiating views.

    :doc:`api-kivy.adapters.args_converters`.

----
'''
