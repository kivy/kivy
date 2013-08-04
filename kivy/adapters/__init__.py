'''
Adapters
========

.. versionadded:: 1.5.0

An adapter is an intermediating controller-type class that builds views for
top-level collection-type widgets, interacting with data as prescribed by
parameters.

- **Adapters**: The base :class:`~kivy.adapters.Adapter` is subclassed by
  :class:`~kivy.adapters.SimpleListAdapter`, :class:`~kivy.adapters.ListAdapter`, and
  :class:`~kivy.adapters.DictAdapter`.

    :doc:`api-kivy.adapters.adapter`,
    :doc:`api-kivy.adapters.simplelistadapter`,
    :doc:`api-kivy.adapters.listadapter`,
    :doc:`api-kivy.adapters.dictadapter`,

- **Models**: The data for which an adapter serves as a bridge to views can be
  any sort of data. However, as a convenience, model mixin classes can ease the
  preparation of data, or the shaping for use in the system. For selection
  operations, :class:`SelectableDataItem` can optionally prepare data items to
  provide and receive selection information (data items are not required to be
  "selection-aware", but in some cases it may be desired).

    :doc:`api-kivy.adapters.models`,

- **Args Converters**: Argument converters are made by the application
  programmer to do the work of converting data items to argument dictionaries
  suitable for instantiating views.

    :doc:`api-kivy.adapters.args_converters`,

----
'''
