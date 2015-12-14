.. _kivy_android_vm:

The Kivy Android Virtual Machine
================================

Introduction
------------

Currently, Kivy Android applications can only be built in a Linux
environment configured with python-for-android, the Android SDK and the
Android NDK. As this environment in not only tricky to setup but also
impossible on Windows or OS X operating systems, we provide a fully configured
`VirtualBox <http://www.virtualbox.org>`_ disk image to ease your building
woes.

If you are not familiar with virtualization, we encourage you to read the
`Wikipedia Virtualization page. <http://en.wikipedia.org/wiki/Virtualization>`_

Getting started
---------------

#. Download the disc image from `here <http://kivy.org/#download>`_, in the
   *Virtual Machine* section. The download is >2GB (6GB after extracted).
   Extract the file and remember the location of the extracted vdi file.

#. Download the version of VirtualBox for your machine from the
   `VirtualBox download area <https://www.virtualbox.org/wiki/Downloads>`_
   and install it.

#. Start VirtualBox, click on "New" in the left top. Then select "linux" and
   "Ubuntu 64-bit".

#. Under "Hard drive", choose "Use an existing virtual hard drive file".
   Search for your vdi file and select it.

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

Hints and tips
--------------

#. Shared folders

    Generally, your development environment and toolset are set up on your
    host machine but the APK is build in your guest. VirtualBox has a feature
    called 'Shared folders' which allows your guest direct access to a folder
    on your host.

    If it often convenient to use this feature (usually with 'Permanent' and
    'Auto-mount' options) to copy the built APK to the host machine so it can
    form part of your normal dev environment. A simple script can easily
    automate the build and copy/move process.

#. Copy and paste

    By default, you will not be able to share clipboard items between the host
    and the guest machine. You can achieve this by enabling the
    "bi-directional" shared clipboard option under
    "Settings -> General -> Advanced".

#. Snapshots

    If you are working on the Kivy development branch, pulling the latest
    version can sometimes break things (as much as we try not to). You can
    guard against this by taking a snapshot before pulling. This allows you
    to easily restore your machine to its previous state should you have the
    need.

#. Insufficient memory

    Assigning the Virtual Machine insufficient memory may result in the
    compile failing with cryptic errors, such as:

        arm-linux-androideabi-gcc: Internal error: Killed (program cc1)

    If this occurs, please check the amount of free memory in the Kivy VM and
    increase the amount of RAM allocated to it if required.
