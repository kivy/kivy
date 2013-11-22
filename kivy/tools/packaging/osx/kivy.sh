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
export GST_PLUGIN_SCANNER=${SCRIPT_PATH}/lib/bin/gst-plugin-scanner
export GST_REGISTRY_FORK="no"

exec $(python -c "import os, sys; print os.path.normpath(sys.prefix)")/bin/python2.7 "$@"
