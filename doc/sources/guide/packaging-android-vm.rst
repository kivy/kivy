.. _kivy_android_vm:

The Kivy Android Virtual Machine
================================

Introduction
------------

Currently, Kivy Android applications can only be built in a Linux
enironment configured with python-for-android, the Android SDK and the
Android NDK. As this enviroment in not only tricky to setup but also
impossible on Windows or MacOSX operating systems, we provide a fully configured
`VirtualBox <http://www.virtualbox.org>`_ disk image to ease your building 
woes.

Getting started
---------------

#. Download the disc image from `here <http://kivy.org/#download>`_, in the
   *Virtual Machine* section. It is aproximately 1GB.
   Extract the file and remember the location of the extracted vdi file.

#. Download the version of VirtualBox for your machine from the
   `VirtualBox download area <https://www.virtualbox.org/wiki/Downloads>`_
   and install it.

#. Start VirtualBox, click on "New" in the left top. Then select "linux" and
   "Ubuntu 32".

#. Under "Hard drive", choose "Use an existing virtual hard drive file".
   Search for your vdi file and enter it there.

#. Go to the "Settings" for your virtual machine. In the
   "Display -> Video" section, increase video ram to 32mb or above.
   Enable 3d acceleration to improve the user experience.

#. Start the Virtual machine and follow the instructions in the readme file
   on the desktop.

Building the APK
----------------

Once the VM is loaded, you can follow the instructions from
:ref:`Packaging your application into APK`. You don't need to download
with `git clone` though, as python-for-android is already installed
and set up in the virtual machine home directory.
