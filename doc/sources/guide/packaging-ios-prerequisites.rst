.. _packaging_ios_prerequisites:

IOS Prerequisites
=================

The following guide assumes:

    * XCode 5.1
    * MacOSX 10.9
    
Your experience may vary with different versions.

Homebrew
--------

We use the `Homebrew <http://brew.sh/>`_ package mananger for OSX to install
some of the dependencies and tools used by Kivy. It's a really helpful tool and
is an Open Source project hosted on
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

The last, final and desperate step to get things working might be to remove
Homebrew altogether, get the lastest version, install that and then re-install
the dependencies.

    `How to Uninstall and Remove Homebrew for Mac OSX <http://www.curvve.com/blog/guides/2013/uninstall-homebrew-mac-osx/>`_

