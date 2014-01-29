'''
List Item View Argument Converters
==================================

.. versionadded:: 1.5


The default list item args converter for list adapters is a function (shown
below) that takes a row index and a string. It returns a dict with the string as
the *text* item, along with two properties suited for simple text items with
a height of 25.

Argument converters may be normal functions or, as in the case of the default
args converter, lambdas::

    list_item_args_converter = lambda row_index, x: {'text': x,
                                                     'size_hint_y': None,
                                                     'height': 25}
'''
list_item_args_converter = lambda row_index, x: {'text': x,
                                                 'size_hint_y': None,
                                                 'height': 25}
