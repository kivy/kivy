=====================================
 Installing Kivy devel with MacPorts
=====================================

Install `MacPorts <http://www.macports.org/>`_ in ``/opt/local`` (the default
directory for MacPorts).

Base software requirements
==========================

Install base software and Kivy requirements (note that you may prefer Python 2.7
to Python 2.6) ::

  $ sodo port install git-core
  $ sudo port install python26
  $ sudo port install py26-virtualenvwrapper
  $ sudo port install py26-game
  $ sudo port install libsdl
  $ sudo port install libsdl-devel


Use a virtualenv ?
==================

From there you may prefer to install Kivy in a Python virtualenv.

Read more about Virtualenv an Virtualenvwrapper to setup your environment here
http://www.doughellmann.com/projects/virtualenvwrapper/

You can skip this section if you prefer a global installation of Kivy ::

  $ mkvirtualenv kivy

Note that if you installed and activated a virtualenv you may omit the ``sudo``
of the various commands mentioned below in this document.

Install kivy
============

From the ``osx-branch`` ::

  $ git clone -b osx-support https://github.com/splanquart/kivy.git kivy-devel
  $ cd kivy-devel
  $ export USE_MACPORTS && python setup.py install
