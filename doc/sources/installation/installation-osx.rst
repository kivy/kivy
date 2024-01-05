.. _installation_osx:

Installation on macOS
====================

To install Kivy on macOS using ``pip``, please follow the main
:ref:`installation guide<installation-canonical>`.
Otherwise, continue to the :ref:`Kivy.app instructions below<osx-app>`.

Installation components
-----------------------

Following, are additional information linked to from some of the steps in the
main :ref:`installation guide<installation-canonical>`, specific to macOS.

.. _install-python-osx:

Installing Python
^^^^^^^^^^^^^^^^^

Homebrew
~~~~~~~~

If you're using `Homebrew <https://brew.sh>`_, you can install Python with::

    brew install python3

MacPorts
~~~~~~~~

If you're using `Macports <https://www.macports.org>`_, you can install Python with::

    # Install and set e.g. Python 3.8 as the default
    port install python38
    port select --set python python38

    # Install and set pip as the default::
    port install py38-pip
    port select --set pip py38-pip

Frameworks
~~~~~~~~~~

To install frameworks Python on macOS, download it from the main
`Python website <https://www.python.org/downloads/macos/>`_ and follow the
installation steps. You can read more about the installation in the
`Python guide <https://docs.python.org/3/using/mac.html>`_.

.. _install-source-osx:

Source installation Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To install Kivy from source, please follow the :ref:`installation guide<kivy-wheel-install>` until you reach the
:ref:`Kivy install step<kivy-source-install>` and then install the additional dependencies
below before continuing.

**pkg-config**, **cmake**, **ninja** are required to build Kivy from source. If you're using ``brew`` as your
package manager, you can install it with::

    brew install pkg-config cmake ninja

Now that you have all the dependencies for kivy, you need to make sure
you have the command line tools installed::

    xcode-select --install

.. _osx-app:

Using The Kivy.app
------------------

.. note::

    Kivy.app is built with ``MACOSX_DEPLOYMENT_TARGET=10.9``.

You can find complete instructions to build and package apps with Kivy.app in the readme
of the `kivy-sdk-packager repo <https://github.com/kivy/kivy-sdk-packager/tree/master/osx>`_.

To install the Kivy virtualenv, you must:

    1. Navigate to the latest Kivy release on Kivy's `website <https://kivy.org/downloads/>`_ or
       `GitHub <https://github.com/kivy/kivy/releases>`_ and download ``Kivy.dmg``.
       You can also download a nightly snapshot of
       `Kivy.app <https://kivy.org/downloads/ci/osx/app/Kivy.dmg>`_.
    2. Open the dmg
    3. In the GUI copy the Kivy.app to /Applications by dragging the folder icon to the right.
    4. Optionally create a symlink by running the following command::

           ln -s /Applications/Kivy.app/Contents/Resources/script /usr/local/bin/kivy

       This creates the ``kivy`` binary that you can use instead of python to run scripts.
       I.e. instead of doing ``python my_script.py`` or ``python -m pip install <module name>``, write
       ``kivy my_script.py`` or ``kivy -m pip install <module name>`` to run it using the kivy
       bundled Python interpreter with the kivy environment.

       As opposed to activating the virtualenv below, running with ``kivy`` will use the virtualenv
       but also properly configure the script environment required to run a Kivy app (i.e. setting
       kivy's home path etc.).

Using the App Virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The path to the underlying virtualenv is ``/Applications/Kivy.app/Contents/Resources/venv``.
To activate it so you can use python, like any normal virtualenv, do::

        pushd /Applications/Kivy.app/Contents/Resources/venv/bin
        source activate
        source kivy_activate
        popd

.. warning::
    On the default mac (zsh) shell you **must** be in the bin directory containing ``activate`` to be
    able to ``activate`` the virtualenv, hence why we changed the directory temporarily.

``kivy_activate`` sets up the environment to be able to run Kivy, by setting the kivy home, and other variables.

Start any Kivy Application
^^^^^^^^^^^^^^^^^^^^^^^^^^

You can run any Kivy application by simply dragging the application's main file
onto the Kivy.app icon.
