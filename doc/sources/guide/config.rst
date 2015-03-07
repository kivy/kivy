.. _configuring kivy:

Configuring Kivy
==============

There are three ways to configure Kivy and they can be used in combination.

* Setting :ref:`environment variables` starting with **KIVY_**.  Environment variables can also be set by
  a program before importing the kivy module.
* Passing options on the command line.  Importing the kivy module parses command line
  options, unless KIVY_NO_ARGS is set.  If the option "*--*" is found, parsing stops
  and remaining options can be parsed the program.  Use *--help* for a list of command
  line options.
* Using the kivy configuration file, named `config.ini`.  This adheres
  to the `standard INI <http://en.wikipedia.org/wiki/INI_file>`_ format.

Generally, environment variables override the command line options which override the configuration
file settings which override the defaults.


Locating the configuration file
-------------------------------

The location of the configuration file is controlled by the
environment variable `KIVY_HOME`::

    <KIVY_HOME>/config.ini

On desktop, this defaults to::

    <HOME_DIRECTORY>/.kivy/config.ini

Therefore, if your user is named "tito", the file will be here:

- Windows: ``C:\Users\tito\.kivy\config.ini``
- MacOSX: ``/Users/tito/.kivy/config.ini``
- Linux: ``/home/tito/.kivy/config.ini``

On Android, this defaults to::

    <ANDROID_APP_PATH>/.kivy/config.ini

If your app is named "org.kivy.launcher", the file will be here::

    /data/data/org.kivy.launcher/files/.kivy/config.ini

On iOS, this defaults to::

    <HOME_DIRECTORY>/Documents/.kivy/config.ini


Understanding config tokens
---------------------------

All the configuration tokens are explained in the :mod:`kivy.config`
module.

