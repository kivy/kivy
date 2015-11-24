.. _configure kivy:

Configure Kivy
==============

The configuration file for kivy is named `config.ini`, and adheres
to the `standard INI <http://en.wikipedia.org/wiki/INI_file>`_ format.

Locating the configuration file
-------------------------------

The location of the configuration file is controlled by the
environment variable `KIVY_HOME`::

    <KIVY_HOME>/config.ini

On desktop, this defaults to::

    <HOME_DIRECTORY>/.kivy/config.ini

Therefore, if your user is named "tito", the file will be here:

- Windows: ``C:\Users\tito\.kivy\config.ini``
- OS X: ``/Users/tito/.kivy/config.ini``
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
