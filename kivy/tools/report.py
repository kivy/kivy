'''
Report tool
===========

This tool is a helper for users. It can be used to dump information
for help during the debugging process.

'''

import os
import sys
import time
from time import ctime
from configparser import ConfigParser
from io import StringIO
from xmlrpc.client import ServerProxy

import kivy

report = []


def title(t):
    report.append('')
    report.append('=' * 80)
    report.append(t)
    report.append('=' * 80)
    report.append('')

# ----------------------------------------------------------
# Start output debugging
# ----------------------------------------------------------

title('Global')
report.append('OS platform     : %s' % sys.platform)
report.append('Python EXE      : %s' % sys.executable)
report.append('Python Version  : %s' % sys.version)
report.append('Python API      : %s' % sys.api_version)
report.append('Kivy Version    : %s' % kivy.__version__)
report.append('Install path    : %s' % os.path.dirname(kivy.__file__))
report.append('Install date    : %s' % ctime(os.path.getctime(kivy.__file__)))

title('OpenGL')
from kivy.core import gl
from kivy.core.window import Window
report.append('GL Vendor: %s' % gl.glGetString(gl.GL_VENDOR))
report.append('GL Renderer: %s' % gl.glGetString(gl.GL_RENDERER))
report.append('GL Version: %s' % gl.glGetString(gl.GL_VERSION))
ext = gl.glGetString(gl.GL_EXTENSIONS)
if ext is None:
    report.append('GL Extensions: %s' % ext)
else:
    report.append('GL Extensions:')
    for x in ext.split():
        report.append('\t%s' % x)
Window.close()

title('Core selection')
from kivy.core.audio import SoundLoader
report.append('Audio  = %s' % SoundLoader._classes)
from kivy.core.camera import Camera
report.append('Camera = %s' % Camera)
from kivy.core.image import ImageLoader
report.append('Image  = %s' % ImageLoader.loaders)
from kivy.core.text import Label
report.append('Text   = %s' % Label)
from kivy.core.video import Video
report.append('Video  = %s' % Video)
report.append('Window = %s' % Window)

title('Libraries')


def testimport(libname):
    try:
        l = __import__(libname)
        report.append('%-20s exist at %s' % (libname, l.__file__))
    except ImportError:
        report.append('%-20s is missing' % libname)

for x in (
    'gst',
    'pygame',
    'pygame.midi',
    'pyglet',
    'videocapture',
    'squirtle',
    'PIL',
    'opencv',
    'opencv.cv',
    'opencv.highgui',
    'cython'):
    testimport(x)

title('Configuration')
s = StringIO()
from kivy.config import Config
ConfigParser.write(Config, s)
report.extend(s.getvalue().split('\n'))

title('Input availability')
from kivy.input.factory import MotionEventFactory
for x in MotionEventFactory.list():
    report.append(x)

'''
title('Log')
for x in pymt_logger_history.history:
    report.append(x.message)
'''

title('Environ')
for k, v in os.environ.items():
    report.append('%s = %s' % (k, v))

title('Options')
for k, v in kivy.kivy_options.items():
    report.append('%s = %s' % (k, v))


report = '\n'.join(report)

print(report)
print()
print()

try:
    reply = input(
        'Do you accept to send report to paste.pocoo.org (Y/n) : ')
except EOFError:
    sys.exit(0)

if reply.lower().strip() in ('', 'y'):
    print('Please wait while sending the report...')

    s = ServerProxy('http://paste.pocoo.org/xmlrpc/')
    r = s.pastes.newPaste('text', report)

    print()
    print()
    print('REPORT posted at http://paste.pocoo.org/show/%s/' % r)
    print()
    print()
else:
    print('No report posted.')

# On windows system, the console leave directly after the end
# of the dump. That's not cool if we want get report url
input('Enter any key to leave.')
