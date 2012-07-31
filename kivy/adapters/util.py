'''
The default list item args converter for list adapters is this simple function
that takes a string and returns the string as the text argument in a dict,
along with two properties suited for simple text items with height of 25.

[TODO] Might there be other useful converters to put here, with descriptive
names?
'''
list_item_args_converter = lambda x: {'text': x,
                                      'size_hint_y': None,
                                      'height': 25}
