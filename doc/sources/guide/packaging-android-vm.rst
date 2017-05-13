.. _kivy_android_vm:

The Kivy Android Virtual Machine
================================

.. note::

    The VM is now updated. Please check the `Kivy website <http://kivy.org/#download>`_
    for the latest version.

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

#. Download the `Kivy / Buildozer VM <http://kivy.org/#download>`_, in the
   *Virtual Machine* section. The download is 1.2GB.
   Extract the file and remember the location of the extracted directory.

#. Download the version of VirtualBox for your machine from the
   `VirtualBox download area <https://www.virtualbox.org/wiki/Downloads>`_
   and install it.

#. Start VirtualBox, click on "File", "Import Appliance".

#. Select the extracted directory, file should be named "Buildozer VM.ovf"

#. Start the Virtual machine and click on the "Buildozer" icon.

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

    Currently, VirtualBox doesn't allow symlink anymore in a shared folder.
    Adjust your buildozer.spec to build outside the shared folder.
    Also, ensure the `kivy` user is in the `vboxsf` group.

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

#. No space left

    Read the section about resizing the VM at https://github.com/kivy/buildozer#buildozer-virtual-machine
