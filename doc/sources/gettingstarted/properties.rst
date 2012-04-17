Properties
----------

Kivy properties are an implementation of the observer pattern, they give you a way to bind events to the changing of their value.

To use them, you have to create them at class level, they will take care of their instanciation when the class is instanciated.

class MyWidget(Widget):
    # definition at class level
    my_property = StringProperty('world')

    # create a callback for when the property is changed,
    # due to its name, it will be bound to my_property
    # you can bind any callback to the property using my_property.bind(callback)

    def on_my_property(self, value, \*others):
        print 'hello',self.my_property

Kivy’s Properties are not to be confused with Python’s properties (i.e. the @property decorator and the <property> type).

Kivy’s property classes support:

    Value Checking / Validation
        When you assign a new value to a property, the value is checked to pass some constraints implemented in the class. I.e., validation is performed. 
        For example, an OptionProperty will make sure that the value is in a predefined list of possibilities. A NumericProperty will check that your value is a numeric type, 
        i.e. int, float, etc. This prevents many errors early on.
    Observer Pattern
        You can specify what should happen when a property’s value changes. You can bind your own function as a callback to changes of a Property. 
        If, for example, you want a piece of code to be called when a widget’s pos property changes, you can bind a function to it.
    Better Memory Management
        The same instance of a property is shared across multiple widget instances.

Each property by default provides a ``on_property`` event in the class it is defined in.

For a in-depth look into kivy properties look in http://kivy.org/docs/api-kivy.properties.html
