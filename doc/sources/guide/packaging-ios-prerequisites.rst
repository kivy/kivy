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

For further help, please refer to the `Homebrew wiki <https://github.com/Homebrew/homebrew/wiki>`_.
    
The last, final and desperate step to get things working might be to remove
Homebrew altogether, get the lastest version, install that and then re-install
the dependencies.

    `How to Uninstall and Remove Homebrew for Mac OSX <http://www.curvve.com/blog/guides/2013/uninstall-homebrew-mac-osx/>`_

GCC Compiler issues
===================

Some dependencies for compiling cython with pip on OSX may fail to compile with
the clang (Apple's C) compiler displaying the message::

    clang: error: unknown argument: '-mno-fused-madd' [-Wunused-command-line-argument-hard-error-in-future]
    clang: note: this will be a hard error (cannot be downgraded to a warning) in the future
    error: command 'cc' failed with exit status 1

Here is a workaround::

    export CFLAGS=-Qunused-arguments
    sudo -E pip install cython

The -E flag passes the environment to the sudo shell.


