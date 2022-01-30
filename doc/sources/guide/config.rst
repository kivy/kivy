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
- macOS: ``/Users/tito/.kivy/config.ini``
- Linux: ``/home/tito/.kivy/config.ini``

On Android, this defaults to::

    <ANDROID_APP_PATH>/.kivy/config.ini

If your app is named "org.kivy.launcher", the file will be here::

    /data/data/org.kivy.launcher/files/.kivy/config.ini

On iOS, this defaults to::

    <HOME_DIRECTORY>/Documents/.kivy/config.ini


Local configuration
-------------------

Sometimes it's desired to change configuration only for certain applications
or during testing of a separate part of Kivy for example input providers.
To create a separate configuration file you can simply use these commands::

    from kivy.config import Config

    Config.read(<file>)
    # set config
    Config.write()

When a local configuration of single ``.ini`` file isn't enough, e.g. when
you want to have separate environment for `garden`, kivy logs and other things,
you'll need to change the ``KIVY_HOME`` environment variable in your
application to get desired result::

    import os
    os.environ['KIVY_HOME'] = <folder>

or before each run of the application change it manually in the console:

#. Windows::

    set KIVY_HOME=<folder>

#. Linux & OSX::

    export KIVY_HOME=<folder>

After the change of ``KIVY_HOME``, the folder will behave exactly the same
as the default ``.kivy/`` folder mentioned above.

Understanding config tokens
---------------------------

All the configuration tokens are explained in the :mod:`kivy.config`
module.
