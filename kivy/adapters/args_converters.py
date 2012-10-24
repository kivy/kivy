'''
List Item View Argument Converters
==================================

.. versionadded:: 1.5


The default list item args converter for list adapters is this function
that takes a string and returns the string as the text argument in a dict,
along with two properties suited for simple text items with height of 25.

These may be normal functions or, in the case of the default args converter,
lambdas::

    list_item_args_converter = lambda x: {'text': x,
                                          'size_hint_y': None,
                                          'height': 25}
'''
list_item_args_converter = lambda x: {'text': x,
                                      'size_hint_y': None,
                                      'height': 25}
