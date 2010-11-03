export KIVY_PORTABLE_ROOT=$1

if [ ! -d $KIVY_PORTABLE_ROOT ]; then
	echo "Usage: kivyenv.sh <root directory of portable package>"
	exit 1
fi

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

export PYTHONPATH=$KIVY_PORTABLE_ROOT/kivy:$PYTHONPATH
echo PYTHONPATH is $PYTHONPATH

export KIVY_PATHS_INITIALIZED=1
echo ##################################

fi

echo done bootstraping kivy...have fun!
echo
