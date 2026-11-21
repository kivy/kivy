import os
import sys

root = os.path.join(sys._MEIPASS, 'kivy_install')

os.environ['KIVY_DATA_DIR'] = os.path.join(root, 'data')
os.environ['KIVY_MODULES_DIR'] = os.path.join(root, 'modules')
os.environ['GST_PLUGIN_PATH'] = '{}{}{}'.format(
    sys._MEIPASS, os.pathsep, os.path.join(sys._MEIPASS, 'gst-plugins'))
os.environ['GST_REGISTRY'] = os.path.join(sys._MEIPASS, 'registry.bin')

# kivy.lib.gstplayer opens GStreamer at run time rather than linking it, so
# point it at the GStreamer libraries the hook bundled next to the app.
for _name in ('gstreamer-1.0-0.dll', 'libgstreamer-1.0-0.dll',
              'libgstreamer-1.0.so.0'):
    if os.path.isfile(os.path.join(sys._MEIPASS, _name)):
        os.environ.setdefault('KIVY_GSTREAMER_ROOT', sys._MEIPASS)
        break

sys.path += [os.path.join(root, '_libs')]

if sys.platform == 'darwin':
    sitepackages = os.path.join(sys._MEIPASS, 'sitepackages')
    sys.path += [sitepackages, os.path.join(sitepackages, 'gst-0.10')]
    os.putenv('GST_REGISTRY_FORK', 'no')
