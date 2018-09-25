'''
List Item View Argument Converters
==================================

.. versionadded:: 1.5

.. deprecated:: 1.10.0
    The feature has been deprecated.

The default list item args converter for list adapters is a function (shown
below) that takes a row index and a string. It returns a dict with the string
as the *text* item, along with two properties suited for simple text items with
a height of 25.

Simple Usage
------------

Argument converters may be normal functions or, as in the case of the default
args converter, lambdas::

    list_item_args_converter = lambda row_index, x: {'text': x,
                                                     'size_hint_y': None,
                                                     'height': 25}

Advanced Usage
--------------

Typically, having the argument converter perform a simple mapping suffices.
There are times, however, when more complex manipulation is required. When
using :class:`~kivy.uix.listview.CompositeListItem`, it is possible to specify
a list of cls dictionaries. This allows you to compose a single view item
out of multiple classes, each of which can receive their own class constructor
arguments via the *kwargs* keyword::

    args_converter = lambda row_index, rec: \\
            {'text': rec['text'],
             'size_hint_y': None,
             'height': 25,
             'cls_dicts': [{'cls': ListItemButton,
                            'kwargs': {'text': rec['text']}},
                           {'cls': ListItemLabel,
                            'kwargs': {'text': rec['text'],
                                       'is_representing_cls': True}},
                           {'cls': ListItemButton,
                            'kwargs': {'text': rec['text']}}]}

Please see the `list_composite.py <https://github.com/\
kivy/kivy/tree/master/examples/widgets/lists/list_composite.py>`_ for a
complete example.

'''
list_item_args_converter = lambda row_index, x: {'text': x,
                                                 'size_hint_y': None,
                                                 'height': 25}
