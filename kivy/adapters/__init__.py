'''
Adapters
========

.. versionadded:: 1.5.0

.. note::

    The feature has been deprecated.

An adapter is a mediating controller-type class that processes and presents
data for use in views. It does this by generating models, generally lists of
:class:`~kivy.uix.selectableview.SelectableView` items, that are consumed and
presented by views. Views are top-level widgets, such as a
:class:`~kivy.uix.listview.ListView`, that allow users to scroll through
and (optionally) interact with your data.

The Concept
-----------

Kivy adapters are modelled on the
`Adapter design pattern <http://en.wikipedia.org/wiki/Adapter_pattern>`_.
Conceptually, they play the role of a 'controller' between you data and views
in a `Model-View-Controller
<https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller>`_
type architecture.

The role of an adapter can be depicted as follows:

.. image:: images/adapters.png


The Components
--------------

The components involved in this process are:

- **Adapters**: The adapter plays a mediating role between the user interface
  and your data. It manages the creation of the view elements for the model
  using the args_converter to prepare the contructor arguments for your
  cls/template view items.

  The base :class:`Adapter` is subclassed by the
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
  suitable for instantiating views. In effect, they take each row of your data
  and create dictionaries that are passed into the constructors of your
  cls/template which are then used populate your View.

    :doc:`api-kivy.adapters.args_converters`.

- **Views**: Models of your data are presented to the user via views. Each of
  your data items create a corresponding view subitem (the cls or template)
  presented in a list by the View. The base :class:`AbstractView` currently has
  one concrete implementation: the :class:`ListView`.

    :doc:`api-kivy.uix.abstractview`,
    :doc:`api-kivy.uix.listview`.

----
'''
