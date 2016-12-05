'''
Report tool
===========

This tool is a helper for users. It can be used to dump information
for help during the debugging process.

'''

import os
import sys
import platform as plf
from time import ctime

try:
    # PY3
    from configparser import ConfigParser
except ImportError:
    # PY2
    from ConfigParser import ConfigParser

try:
    from StringIO import StringIO
    input = raw_input
except ImportError:
    from io import StringIO

import kivy

report = []
report_dict = {}  # One key value pair for each title.


def title(t):
    report.append('')
    report.append('=' * 80)
    report.append(t)
    report.append('=' * 80)
    report.append('')

# This method sends report to gist(Different file in a single gist) and
# returns the URL


def send_report(dict_report):
    import requests
    import json

    gist_report = {
        "description": "Report",
        "public": "true",
        "files": {
            "Global.txt": {
                "content": "\n".join(dict_report['Global']),
                "type": 'text'
            },
            "OpenGL.txt": {
                "content": "\n".join(dict_report['OpenGL']),
                "type": 'text'

            },
            "Core selection.txt": {
                "content": "\n".join(dict_report['Core']),
                "type": 'text'
            },
            "Libraries.txt": {
                "content": "\n".join(dict_report['Libraries']),
                "type": 'text'
            },
            "Configuration.txt": {
                "content": "\n".join(dict_report['Configuration']),
                "type": 'text'
            },
            "Input Availablity.txt": {
                "content": "\n".join(dict_report['InputAvailablity']),
                "type": 'text'
            },
            "Environ.txt": {
                "content": "\n".join(dict_report['Environ']),
                "type": 'text'
            },
            "Options.txt": {
                "content": "\n".join(dict_report['Options']),
                "type": 'text'
            },
        }
    }
    report_json = json.dumps(gist_report)
    response = requests.post("https://api.github.com/gists", report_json)
    return json.loads(response.text)['html_url']

# ----------------------------------------------------------
# Start output debugging
# ----------------------------------------------------------

title('Global')
report.append('OS platform     : %s | %s' % (plf.platform(), plf.machine()))
report.append('Python EXE      : %s' % sys.executable)
report.append('Python Version  : %s' % sys.version)
report.append('Python API      : %s' % sys.api_version)
report.append('Kivy Version    : %s' % kivy.__version__)
report.append('Install path    : %s' % os.path.dirname(kivy.__file__))
report.append('Install date    : %s' % ctime(os.path.getctime(kivy.__file__)))
report_dict['Global'] = report
report = []

title('OpenGL')
from kivy.core import gl
from kivy.core.window import Window
report.append('GL Vendor: %s' % gl.glGetString(gl.GL_VENDOR))
report.append('GL Renderer: %s' % gl.glGetString(gl.GL_RENDERER))
report.append('GL Version: %s' % gl.glGetString(gl.GL_VERSION))
ext = None
try:
    gl.glGetString(gl.GL_EXTENSIONS)
except AttributeError:
    pass
if ext is None:
    report.append('GL Extensions: %s' % ext)
else:
    report.append('GL Extensions:')
    for x in ext.split():
        report.append('\t%s' % x)
Window.close()
report_dict['OpenGL'] = report
report = []

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
report_dict['Core'] = report
report = []

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
    'sdl2',
    'glew',
    'opencv',
    'opencv.cv',
    'opencv.highgui',
    'cython'):
    testimport(x)
report_dict['Libraries'] = report
report = []

title('Configuration')
s = StringIO()
from kivy.config import Config
ConfigParser.write(Config, s)
report.extend(s.getvalue().split('\n'))
report_dict['Configuration'] = report
report = []

title('Input availability')
from kivy.input.factory import MotionEventFactory
for x in MotionEventFactory.list():
    report.append(x)
report_dict['InputAvailablity'] = report
report = []

'''
title('Log')
for x in pymt_logger_history.history:
    report.append(x.message)
'''

title('Environ')
for k, v in os.environ.items():
    report.append('%s = %s' % (k, v))
report_dict['Environ'] = report
report = []

title('Options')
for k, v in kivy.kivy_options.items():
    report.append('%s = %s' % (k, v))
report_dict['Options'] = report
report = []

# Prints the entire Output
print('\n'.join(report_dict['Global'] + report_dict['OpenGL'] +
                report_dict['Core'] + report_dict['Libraries'] +
                report_dict['Configuration'] +
                report_dict['InputAvailablity'] +
                report_dict['Environ'] + report_dict['Options']))
print()
print()

try:
    print('The report will be sent as an anonymous gist.')
    reply = input(
        'Do you accept to send report to https://gist.github.com/ (Y/n) : ')
except EOFError:
    sys.exit(0)

if reply.lower().strip() in ('', 'y'):
    print('Please wait while sending the report...')

    paste_url = send_report(report_dict)

    print()
    print()
    print('REPORT posted at %s' % paste_url)
    print()
    print()
else:
    print('No report posted.')

# On windows system, the console leave directly after the end
# of the dump. That's not cool if we want get report url
input('Enter any key to leave.')
