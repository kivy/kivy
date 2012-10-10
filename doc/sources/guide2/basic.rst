.. _basic:

Basic Kivy
==========

Installation of Kivy environment
--------------------------------

Kivy depends on multiples dependencies, such as pygame, gstreamer, PIL, cairo,
and more. All of them are not required, but depending the platform you're
working on, it can be a pain to install them. For Windows and MacOSX, we
provide a portable package that you can just unzip and use.

.. toctree::
    :maxdepth: 1

    /installation/installation-windows.rst
    /installation/installation-macosx.rst
    /installation/installation-linux.rst

If you want to install everything yourself, ensure that you have at least
`Cython <http://cython.org>`_, `Pygame <http://pygame.org>`. A typical pip
installation look like::

    pip install cython
    pip install hg+http://bitbucket.org/pygame/pygame
    pip install kivy

The `development version <https://github.com/kivy/kivy>`_ can be installed with
git::

    git clone https://github.com/kivy/kivy
    make


Create an application
---------------------

Running the application
-----------------------

Customize the application
-------------------------

Platform specifics
------------------

