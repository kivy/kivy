.. _packaging_ios_compile:

Compiling for IOS
=================

(work in progess - not referenced from external links)

Creating your distribution
--------------------------

Kivy uses a shell script to build your distribution and package all it's
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

These downloaded packages are stored in a hidden *.cache* subfolder. It may
happen that an interrupted download will leave corrupt files in your cache.
Additionally, the build process will also create various other subfolders,
such as *build* and *tmp*, in your *kivy-ios* folder.
 
If you wish to force a fresh build of all the packages, you should delete all
of these other folders (including *.cache*, but not *src* and *tools*) and
re-run the 'build_all.sh' script.

Troubleshooting
---------------

The kivy-ios project is still a "work-in-progress" and uses many libraries which
may change and break things independently of kivy. It may thus sometimes be
necessary to remove any packages which do not compile in order to complete your
build.

# TODO: Add instructions on steps editing/isolating errors

If you encounter an issue which you cannot resolve, remember you can always
:ref:`contact us <contact>` for help.