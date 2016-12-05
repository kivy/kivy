.. _packaging_ios_prerequisites:

IOS Prerequisites
=================

The following guide assumes:

    * XCode 5.1 or above
    * OS X 10.9 or above

Your experience may vary with different versions.

Getting started
---------------

In order to submit any application to the iTunes store, you will need an
`iOS Developer License <https://developer.apple.com/programs/ios/>`_. For
testing, you can use a physical device or the XCode iOS emulator.

Please note that in order to test on the device, you need to register these
devices and install your "provisioning profile" on them. Please refer to the
Apple's
`Getting started <https://developer.apple.com/programs/ios/gettingstarted/>`_
guide for more information.

Homebrew
--------

We use the `Homebrew <http://brew.sh/>`_ package manager for OSX to install
some of the dependencies and tools used by Kivy. It's a really helpful tool
and is an Open Source project hosted on
`Github <https://github.com/Homebrew/homebrew>`_.

Due to the nature of package management (complications with versions and
Operating Systems), this process can be error prone and cause
failures in the build process. The **Missing requirement: <pkg> is not
installed!** message is typically such an error.

The first thing is to ensure you have run the following commands::

    brew install autoconf automake libtool pkg-config mercurial
    brew link libtool
    brew link mercurial
    sudo easy_install pip
    sudo pip install cython

If you still receive build errors, check your Homebrew is in a healthy state::

    brew doctor

For further help, please refer to the
`Homebrew wiki <https://github.com/Homebrew/homebrew/wiki>`_.

The last, final and desperate step to get things working might be to remove
Homebrew altogether, get the latest version, install that and then re-install
the dependencies.

    `How to Uninstall and Remove Homebrew for Mac OSX
    <http://www.curvve.com/blog/guides/2013/uninstall-homebrew-mac-osx/>`_
