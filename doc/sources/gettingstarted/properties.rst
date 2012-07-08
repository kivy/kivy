Kivy Properties
---------------
.. container:: title

    Using Kivy's Properties

Kivy properties are an implementation of the `observer pattern
<http://en.wikipedia.org/wiki/Observer_pattern>`_ .
Kivy's properties are useful to:

- Allow manipulating your widgets in kv language more easily
- Automatically observe any changes and dispatch functions/code accordingly
- Check and validate values
- Optimize memory management


To use them, **you have to declare them at class level**. That is, directly in
the class, not în any method of the class. A property is a class attribute
that will automatically create instance attributes. Each property by default
provides an ``on_property`` event that is called whenever the property's
state/value changes .

Kivy provides the following properties:
    `NumericProperty <http://kivy.org/docs/api-kivy.properties.html?highlight=properties#kivy.properties.NumericProperty>`_, 
    `StringProperty <http://kivy.org/docs/api-kivy.properties.html?highlight=properties#kivy.properties.StringProperty>`_, 
    `ListProperty <http://kivy.org/docs/api-kivy.properties.html?highlight=properties#kivy.properties.ListProperty>`_, 
    `ObjectProperty <http://kivy.org/docs/api-kivy.properties.html?highlight=properties#kivy.properties.ObjectProperty>`_, 
    `BooleanProperty <http://kivy.org/docs/api-kivy.properties.html?highlight=properties#kivy.properties.BooleanProperty>`_, 
    `BoundedNumericProperty <http://kivy.org/docs/api-kivy.properties.html?highlight=properties#kivy.properties.BoundedNumericProperty>`_, 
    `OptionProperty <http://kivy.org/docs/api-kivy.properties.html?highlight=properties#kivy.properties.OptionProperty>`_, 
    `ReferenceListProperty <http://kivy.org/docs/api-kivy.properties.html?highlight=properties#kivy.properties.ReferenceListProperty>`_, 
    `AliasProperty <http://kivy.org/docs/api-kivy.properties.html?highlight=properties#kivy.properties.AliasProperty>`_, 
    `DictProperty <http://kivy.org/docs/api-kivy.properties.html?highlight=properties#kivy.properties.DictProperty>`_, 


For an in-depth look at how to use kivy properties, start `here. <http://kivy.org/docs/api-kivy.properties.html>`_
