.. _packaging_ios_prerequisites:

iOS Prerequisites
=================

The following guide assumes:

    * Xcode 13.2.1 or above
    * macOS 11.6 or above

Your experience may vary with different versions.

Getting started
---------------

In order to submit any application to the iTunes store, you will need an
`iOS Developer License <https://developer.apple.com/programs/ios/>`_. For
testing, you can use a physical device or the Xcode iOS emulator.

Please note that in order to test on the device, you need to register these
devices and install your "provisioning profile" on them. Please refer to the
Apple's
`Getting started <https://help.apple.com/developer-account/>`_
guide for more information.

Homebrew
--------

We use the `Homebrew <https://brew.sh/>`_ package manager for macOS to install
some of the dependencies and tools used by Kivy. It's a really helpful tool
and is an Open Source project hosted on
`Github <https://github.com/Homebrew>`_.

Due to the nature of package management (complications with versions and
Operating Systems), this process can be error prone and cause
failures in the build process. The **Missing requirement: <pkg> is not
installed!** message is typically such an error.

The first thing is to ensure you have run the following commands:

.. parsed-literal::

    $ brew install autoconf automake libtool pkg-config
    $ brew link libtool
    $ pip install |cython_install|

If you still receive build errors, check your Homebrew is in a healthy state::

    brew doctor

For further help, please refer to the
`Homebrew docs <https://docs.brew.sh>`_.

The last, final and desperate step to get things working might be to remove
Homebrew altogether, get the latest version, install that and then re-install
the dependencies.

    `How do I uninstall Homebrew?
    <https://docs.brew.sh/FAQ#how-do-i-uninstall-homebrew>`_
