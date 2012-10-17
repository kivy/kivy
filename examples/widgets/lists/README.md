Programming for lists is a common task in a wide variety of applications.
An attempt is made here to present a good set of samples.

These include:

    - list_simple.py -- The simplest of examples, using the simplest list
                        adapter, :class:`SimpleListAdapter`. Only the names of
                        the fruits in the fixtures data are used to make list
                        item view instances from a custom class. There is no
                        selection -- it is a bare-bones list of strings.

    - list_cascade.py -- Fruit categories on the left, fruit selection within
                         a fruit category in the middle, and a fruit detail
                         view on the right. Selection cascades from left to
                         right, from the category selection, to the fruit
                         selection, to the detail view.

                         The list views use :class:`ListAdapter` and a custom
                         subclass of :class:`ListItemButton` for the list
                         item class. Data for fruits comes from a fixtures.py
                         file that is used in several of the examples.

    - list_cascade_dict.py -- Exactly the same layout and functionality as
                              list_cascade.py, except the list views use
                              :class:`DictAdapter` and the fixtures data is
                              used in an appropriate way for dictionaries.

    - list_cascade_images.py -- Same as the list_cascade_dict.py example, but
                                with thumbnail images of fruits shown in
                                custom list item view class instances, and in
                                the detail view.

    - list_master_detail.py -- Uses a :class:`DictAdapter`. Simpler than the
                               cascade examples. Illustrates use of the terms.

    - list_kv.py -- A simple example to show use of a kv template.

    - list_composite.py -- Uses :class:`CompositeListItem` for list item views
                           comprised by two :class:`ListItemButton`s and one
                           :class:`ListItemLabel`. Illustrates how to construct
                           the fairly involved args_converter used with
                           :class:`CompositeListItem`.

    - list_two_up -- Presents two list views, each using :class:`DictAdapter`.
                     list view on the left is configured for multiple
                     selection. As selection changes in the left list, the
                     selected items form the content for the list on the
                     right, which is constantly updated.

    - list_ops.py -- Seven list views are shown at the bottom, each focusing
                     on one of the available operations for collection
                     adapters: scroll_to, trim_to_sel, trim_left_of_sel, etc.
                     At the top is a display that shows individual items
                     selected across the seven lists, along with a total of
                     all selected items for the lists.
 
#[TODO LIST for kivy uix-listview]:
#
#    - *** FIXED *** Initial selection is apparently working in the associated
#      ListAdapter but the listview display does not show the initial
#      selection (red, in example code). After the listview has been clicked
#      for the first manual selection, the updating of selected items (in red)
#      works.
#
#    - Explain why multiple levels of abstraction are needed. (Adapter,
#      ListAdapter, AbstractView, ListView) -- Tie discussion to inspiration
#      for Adapter and related classes:
#
#          http://developer.android.com/reference/android/\
#              widget/Adapter.html#getView(int,%20android/\
#              .view.View,%20android.view.ViewGroup)
#
#      There is now an ASCII drawing of the relationship between ListView and
#      ListAdapter, as it is now, in the docs below.
#
#    - Divider isn't used (yet).
#
#    - *** DONE *** Consider adding an associated SortableDataItem mixin, to
#                   be used by list item classes in a manner similar to the
#                   SelectableView mixin.
#
#    - *** DONE *** (By adding DictAdapter, which as a sorted_keys argument)
#
#                   Consider a sort_by property. Review the use of the items
#                   property.
#
#    - Work on [TODO]s in the code.
#
#    Examples (in examples/widgets):
#
#    - Improve examples:
#        - *** DONE *** Add fruit images.
#
#    - Add an example where selection doesn't just change background color
#      or font, but animates.
#
#    Other Possibilities:
#
#    - Consider a horizontally scrolling variant.
#
#    - Is it possible to have dynamic item_view height, for use in a
#      master-detail listview in this manner?
#
#        http://www.zkoss.org/zkdemo/grid/master_detail
#
#      (Would this be a new widget called MasterDetailListView, or would the
#       listview widget having a facility for use in this way?)
#
#      (See the list_disclosure.py file as a start.)
#
#    - Make a separate master-detail example that works like an iphone-style
#      animated "source list" that has "disclosure" buttons per item_view, on
#      the right, that when clicked will expand to fill the entire listview
#      area (useful on mobile devices especially). Similar question as above --
#      would listview be given expanded functionality or would this become
#      another kind of "master-detail" widget?)

Notes from Adapter.py:

    - Explain the design philosophy used here -- something like model-view-
      adapter (MVA) as described here:

          http://en.wikipedia.org/wiki/Model-view-adapter (and link to
            basis article about Java Swing design)

      Using background in references like these, compare to MVC terminology,
      and how Kivy operates to fulfill the roles of mediating and coordinating
      controllers, especially (terminology from the world of Cocoa).

    - *** DONE *** Consider an associated "object adapter" (a.k.a., "object
      controller") that is bound to selection. It can also subclass Adapter?

    - *** DONE *** Yes, the new ObjectAdapter subclasses Adapter.

