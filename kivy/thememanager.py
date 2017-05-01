# -*- coding: UTF-8 -*-

'''
A basic theme manager for Kivy. A Kivy theme allows you to redefine
the default values for any property on any widget that ships with Kivy.
You can change background images, fonts, colors, sizes. If it is defined
in a Kivy property on the class, the theme manager can set it.

Theming in Kivy is relatively
simple. If you want to use theming, your root project directory
should have a "themes" folder and putting separate folders for
each theme inside that folder.

The directory structure might look like this:
.
├── main.py
├── themed.kv
└── themes
    ├── blue-theme
    │   ├── images
    │   │   ├── blue-theme-0.png
    │   │   ├── blue-theme.atlas
    │   └── theme.json
    └── red-theme
        ...

The themes directory resides in your project directory
at the same level as your main.py and associated kv file.

Each theme lives in a folder inside the themes directory.
It is comprised of a mandatory theme.json and any associated
content that may need to be included with the theme -- most
likely Kivy atlas images to replace the default atlas.

The json file should have this basic format:

{
    "human_readable_name": "Blue Theme",
    "widgets": {
        "Button": {
            "background_normal": "atlas://images/custom_atlas/dark_circle",
            "background_down": "atlas://images/custom_atlas/light_circle",
            "font_size": 30,
            "border": [20, 30, 40, 50]
        }
    }
}

There should be a dict with metadata (currently only 'human_redabale_name')
and a 'widgets': dict pair. The widgets dict contains a bunch of key value pairs
where the key is the name of a class in Kivy. This is to say, the same name that
would be used in a kv-language file, which is the name passed into a kivy Factory.
The value for each widget is yet another dict that maps property names on that
widget to new default values for the same widget.

The example above customizes only one widget, the Button class. It sets two
properties that are defined on Button itself: background_normal and background_down.
It also redefines two values for properties inherited from label: font_size and border.

Note that atlas urls are mapped relative to the theme directory. This is done seemlessly
for anything that starts with atlas://

Also, if you set an attribute on a class that is a baseclass of another class, that value
will be set for all of them. For example, font_size on a Label, would also set the same size
on a Button. However, you can override the font_size on a Button so that it only applies
to the Button.

Once you have defined one or more themes, you can enable that theme on your app at
startup by setting the theme property on the App class:

from kivy.app import App


class ThemedApp(App):
    pass


if __name__ == '__main__':
    app = ThemedApp()
    app.theme = "blue-theme"
    app.run()


You can also set it directly on the subclass as follows:

class ThemedApp(App):
    theme = "blue-theme"


'''

import os.path
import json
from kivy.factory import Factory, FactoryException
from kivy.properties import NumericProperty, StringProperty
from kivy.logger import Logger


def switch_theme(theme_name):
    '''
    Set the theme name in a directory described as in the module
    documentation. This is typically called only on application startup.
    '''
    theme_path = os.path.join("themes", theme_name,  "theme.json")

    with open(theme_path) as file:
        theme = json.load(file)

    # Discover about Kivy logging
    Logger.info("Loading theme %s" % theme['human_readable_name'])

    for widget_name, properties in theme['widgets'].items():
        for property_name, value in properties.items():
            patch_widget(theme_name, widget_name, property_name, value)


def patch_widget(theme_name, widget_name, property_name, value):
    '''
    For the class named widget_name, get the class from the Factory
    and change the default value for property_name to value.

    The theme_name is used to translate atlas locations to be relative to
    the theme directory instead of the working directory.
     '''
    try:
        widget_class = Factory.get(widget_name)
        kv_class = getattr(widget_class, property_name).__class__
        value = patch_special_cases(
            kv_class,
            value,
            theme_name=theme_name)
        setattr(widget_class, property_name, kv_class(value))

    except (FactoryException, KeyError) as e:
        import traceback
        traceback.print_exc(e)
        print("Unable to set property %s on %s to %s" % (
            property_name, widget_name, value))


def patch_special_cases(kv_class, value, theme_name=None):
    '''
    Try to abstract all the ugly special cases from patch_widget into their own method.

    I expect more of these will need to be defined, going forward.
    '''
    # Special case: If NumericProperty gets a string such as "50dp"
    # then it chokes on uincode. Correct fix may be to let NumericProperty
    # test on basestring?
    if kv_class is NumericProperty and isinstance(value, unicode):
        value = str(value)

    # We want atlas paths to be relative to the theme, not the cwd
    # But this is kinda horrible cause the property just arbitrary string.
    if kv_class is StringProperty and value.startswith("atlas://"):
        value = "atlas://" + os.path.join('themes', theme_name, value[8:])

    return value

