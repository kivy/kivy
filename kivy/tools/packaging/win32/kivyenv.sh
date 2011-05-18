# Script to initialize the complete dev environment
# for Kivy. Use that when you want to develop :)
#
# This will give you an access to :
# - Python binaries (python, easy_install)
# - Cython binaries (cython)
# - A correct pythonpath (Kivy)
# - Gstreamer binaries (gst-inspect, ...)
#
# Usage: source /path/to/kivyenv.sh
#

# Get root directory of portable installation
tmp=$(dirname $BASH_SOURCE)
export KIVY_PORTABLE_ROOT=$(cd $tmp; pwd)

if [ ! -d $KIVY_PORTABLE_ROOT ]; then
	echo "Usage: source /path/to/kivyenv.sh"
	exit 1
fi

# bootstrapping
echo bootstrapping Kivy @ $KIVY_PORTABLE_ROOT

if [ "X$KIVY_PATHS_INITIALIZED" != "X1" ]; then

echo Setting Environment Variables:
echo #################################

export GST_REGISTRY=$KIVY_PORTABLE_ROOT/gstreamer/registry.bin
echo GST_REGISTRY is $GST_REGISTRY
echo ----------------------------------

export GST_PLUGIN_PATH=$KIVY_PORTABLE_ROOT/gstreamer/lib/gstreamer-0.10
echo GST_PLUGIN_PATH is $GST_PLUGIN_PATH
echo ----------------------------------

export PATH=$KIVY_PORTABLE_ROOT:$KIVY_PORTABLE_ROOT/Python:$KIVY_PORTABLE_ROOT/gstreamer/bin:$KIVY_PORTABLE_ROOT/MinGW/bin:$PATH
echo PATH is $PATH
echo ----------------------------------

echo 'Convert to windows path:' $KIVY_PORTABLE_ROOT
KIVY_PORTABLE_ROOT_PY=$(python -c 'import os, sys; print os.path.realpath(sys.argv[1])' $KIVY_PORTABLE_ROOT/kivy)
export PYTHONPATH=$KIVY_PORTABLE_ROOT_PY\;$PYTHONPATH
echo PYTHONPATH is $PYTHONPATH

export KIVY_PATHS_INITIALIZED=1
echo ##################################

fi

echo done bootstraping kivy...have fun!
echo
