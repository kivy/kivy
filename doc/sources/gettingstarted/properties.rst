Properties
----------

Kivy introduces a new way of declaring properties within a class.
Before::

    class MyClass(object):
        def __init__(self):
            super(MyClass, self).__init__()
            self.numeric_var = 1

After, using Kivy's properties::

    class MyClass(EventDispatcher):
        numeric_var = NumericProperty(1)

Theses properties implement the `Observer pattern
<http://en.wikipedia.org/wiki/Observer_pattern>`_. They help you to:

- Easily manipulate widgets defined in the :doc:`/guide/lang`
- Automatically observe any changes and dispatch functions/code accordingly
- Check and validate values
- Optimize memory management


To use them, **you have to declare them at class level**. That is, directly in
the class, not in any method of the class. A property is a class attribute
that will automatically create instance attributes. Each property by default
provides an ``on_<propertyname>`` event that is called whenever the property's
state/value changes.

Kivy provides the following properties:
    :mod:`~kivy.properties.NumericProperty`,
    :mod:`~kivy.properties.StringProperty`,
    :mod:`~kivy.properties.ListProperty`,
    :mod:`~kivy.properties.ObjectProperty`,
    :mod:`~kivy.properties.BooleanProperty`,
    :mod:`~kivy.properties.BoundedNumericProperty`,
    :mod:`~kivy.properties.OptionProperty`,
    :mod:`~kivy.properties.ReferenceListProperty`,
    :mod:`~kivy.properties.AliasProperty`,
    :mod:`~kivy.properties.DictProperty`,

For an in-depth explaination, take a look at :doc:`/api-kivy.properties`.
