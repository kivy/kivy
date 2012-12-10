#!/bin/bash
SCRIPT_PATH="${BASH_SOURCE[0]}";
if([ -h "${SCRIPT_PATH}" ]) then
  while([ -h "${SCRIPT_PATH}" ]) do SCRIPT_PATH=`readlink "${SCRIPT_PATH}"`; done
fi
SCRIPT_PATH=`dirname ${SCRIPT_PATH}`

export PYTHONPATH=${SCRIPT_PATH}/kivy:${SCRIPT_PATH}/lib/sitepackages:$PYTHONPATH
export DYLD_FALLBACK_LIBRARY_PATH=${SCRIPT_PATH}/lib:$DYLD_FALLBACK_LIBRARY_PATH
export LD_PRELOAD_PATH=${SCRIPT_PATH}/lib:$LD_PRELOAD_PATH
export GST_PLUGIN_PATH=${SCRIPT_PATH}/lib/gst-plugins:$GST_PLUGIN_PATH

# It has to be -S or pygame's egg will do some funny site magic and break eventually
# That'd mean however that other libraries can't be found anymore. So if the user has
# a broken pygame installation, it's not our fault...
#
# Also, hardcode the link to python 2.6 for now. If you don't want that, just adjust it.
# We're doing that because the situation of Python on OSX is less than ideal and users
# tend to install Python from arbitrary resources. To ensure smooth execution, we're
# enforcing the usage of the Python version that we actually built against.
# If you know what you're doing you can easily change this.
exec /System/Library/Frameworks/Python.framework/Versions/2.6/bin/python2.6 "$@"
