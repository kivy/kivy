'''
Adapters
========

.. versionadded:: 1.5.0

An adapter is an intermediating controller-type class that builds views
for top-level widgets, interacting with data as prescribed by parameters.
Kivy adapters are modelled on the
`Adapter design pattern <http://en.wikipedia.org/wiki/Adapter_pattern>`_.
On the view side is an :class:`AbstractView`, which is the base view for a
:class:`ListView`.

- **Adapters**: The base :class:`Adapter` is subclassed by
  :class:`SimpleListAdapter` and by :class:`ListAdapter`. Further,
  :class:`DictAdapter` is subclass of :class:`ListAdapter`.

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
