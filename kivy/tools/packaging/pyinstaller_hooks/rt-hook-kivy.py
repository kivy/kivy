import os
import sys

root = os.path.join(sys._MEIPASS, 'kivy_install')

os.environ['KIVY_DATA_DIR'] = os.path.join(root, 'data')
os.environ['KIVY_MODULES_DIR'] = os.path.join(root, 'modules')
os.environ['GST_PLUGIN_PATH'] = '{};{}'.format(
    sys._MEIPASS, os.path.join(sys._MEIPASS, 'gst-plugins'))
os.environ['GST_REGISTRY'] = os.path.join(sys._MEIPASS, 'registry.bin')

sys.path += [os.path.join(root, '_libs')]

if sys.platform == 'darwin':
    sitepackages = os.path.join(sys._MEIPASS, 'sitepackages')
    sys.path += [sitepackages, os.path.join(sitepackages, 'gst-0.10')]
    os.putenv('GST_REGISTRY_FORK', 'no')
