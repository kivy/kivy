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
                     on one of the available operations for list
                     adapters: scroll_to, trim_to_sel, trim_left_of_sel, etc.
                     At the top is a display that shows individual items
                     selected across the seven lists, along with a total of
                     all selected items for the lists.

