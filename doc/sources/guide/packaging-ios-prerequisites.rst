.. _packaging_ios:

IOS Prerequisites
=================

The following guide is based

    * XCode 5.1
    * MacOSX 10.9
    
You experience may vary with version changes.

Homebrew
--------

We use the `Homebrew <http://brew.sh/>`_ packet mananger on OSX to install some
of the dependencies and tools used by Kivy. It's a really helpful tool and
is an Open Source project hosted on
`Github <http://mxcl.github.com/homebrew/>`.

Due to the nature of package management (complications with versions and
Operating System upgradess), this process can be error prone. It can cause
failures in the build process. The **Missing requirement: <pkg> is not
installed!** is typically such an error.

The first is to ensure you have run the following commands::

    brew install autoconf automake libtool pkg-config mercurial
    brew link libtool
    brew link mercurial
    sudo easy_install pip
    sudo pip install cython

If you still receive build errors, check your Homebrew is in a healthy state.::

    brew doctor

The last, final and desperate step to get things working might be to remove
Homebrew altogether, get the last version, install that and then re-install
the dependencies.

    `How to Uninstall and Remove Homebrew for Mac OSX <http://www.curvve.com/blog/guides/2013/uninstall-homebrew-mac-osx/>`_

