.. _migration:

Migrating from Kivy 2.x.x to Kivy 3.x.x
========================================

Introduction
------------

Kivy 3.x.x introduces several changes and improvements compared to Kivy 2.x.x. This guide will help you migrate your existing Kivy 2.x.x codebase to Kivy 3.x.x.

Renamed modules
---------------

*Migration from kivy.core.audio to kivy.core.audio_output*


In Kivy 3.x.x, the `kivy.core.audio` module has been renamed as `kivy.core.audio_output`. 

To migrate your code, you need to update the import statements in your codebase. For example, if you have the following import statement in your code:

.. code-block:: python

    from kivy.core.audio import SoundLoader

You need to update it to:

.. code-block:: python

    from kivy.core.audio_output import SoundLoader
