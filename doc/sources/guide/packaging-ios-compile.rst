.. _packaging_ios_compile:

Compiling for IOS
=================

(work in progess)

Creating your distribution
--------------------------

Kivy uses a shell script to build your distribution and package all its
contents such that it can be used by XCode to compile your final iOS program
(an *.ipa* file).

This process involves running all the required code and libraries through a
compiler and linker in order to create a single, stand-alone set of binaries
and source files. These files comprize you *distribution*.

Using the "build_all.sh" script
-------------------------------

The kivy-ios package provides a generic script, "tools/build_all.sh", that
creates a complete distribution for you.

You may want edit/copy this file in order to customize your distribution for
various reasons::

* Minimize the size of your package by removing unused libraries
* Customize the packing by adding/removing script items
* Troubleshooting

The minimizing and customizing options are obviously desirable and relativly
simple as the build script is a standard
`bash shell script <http://en.wikipedia.org/wiki/Bash_%28Unix_shell%29>`_.

The build process
-----------------

Initially, your kivy-ios checkout will contain two folders: *tools* and *src*.
The first time you run it, the script will download the latest versions of
the packages kivy-ios uses. This means it might fail if any packages are not
available or cannot be downloaded.

These downloaded packages are stored in a hidden *.cache* subfolder. The build
process then extracts these files to a *tmp* subfolder, builds the packages and
places the build in the *build* subfolder. Be careful: if this process is
interrupted, it might leave corrupt files in any of these locations.
 
If you wish to force a fresh build of all the packages, you should delete all
of these other folders (*.cache*, *tmp* and *build*) and re-run the
'build_all.sh' script.

Troubleshooting
---------------

Isolating problems
^^^^^^^^^^^^^^^^^^

The kivy-ios project uses many libraries which
may change and break things independently of kivy. It may thus sometimes be
necessary to remove any packages which do not compile in order to complete your
build or isolate the offending package.

The 'build-all.sh' script assembles many sub-scripts into one, comprehensive
build script. If you open this file, you will see something similar to::

    #!/bin/bash
    
    . $(dirname $0)/environment.sh
    
    try $(dirname $0)/build-libffi.sh
    try $(dirname $0)/build-python.sh
    try $(dirname $0)/reduce-python.sh
    ...

You can comment out problematic scripts using the hash (#) symbol. Some scripts
are essential (e.g. *build-python.sh*), but others can be safely removed if your
application does not require them.
    
We hope you never have to care about this, but if you encounter an error which
you cannot resolve, this may help. Remember, you can always
:ref:`contact us <contact>` for help.

Clang compiler issues
^^^^^^^^^^^^^^^^^^^^^

Some dependencies for compiling cython with pip on OSX may fail to compile with
the Clang (Apple's C) compiler displaying the message::

    clang: error: unknown argument: '-mno-fused-madd' [-Wunused-command-line-argument-hard-error-in-future]
    clang: note: this will be a hard error (cannot be downgraded to a warning) in the future
    error: command 'cc' failed with exit status 1

Here is a workaround::

    export CFLAGS=-Qunused-arguments
    sudo -E pip install cython

The -E flag passes the environment to the sudo shell.

Further reading
---------------

Kivy iOS support is a work-in-progress and we are busy trying to improve
and document this process. Until such time as this is complete, you may
find the following links useful.

* `iOS Tips <https://groups.google.com/forum/#!topic/kivy-users/X8sItpeoZPQ>`_
* `HTTPS (SSL) support <https://groups.google.com/forum/#!searchin/kivy-users/iOS/kivy-users/Qt4x2dB0Xpw/u8jlTMS8Y1MJ>`_

