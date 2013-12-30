#!/usr/bin/env python
# This file is part of python-bidi
#
# python-bidi is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Copyright (C) 2008-2010 Yaacov Zamir <kzamir_a_walla.co.il>,
# Meir kriheli <meir@mksoft.co.il>

"""
Implementation of Unicode Bidirectional Algorithm
http://www.unicode.org/unicode/reports/tr9/
"""

VERSION = '0.3.4'

def main():
    """Will be used to create the console script"""

    import optparse
    import sys
    import codecs
    import locale
    from algorithm import get_display

    parser = optparse.OptionParser()

    parser.add_option('-e', '--encoding',
                      dest='encoding',
                      default='utf-8',
                      type='string',
                      help='Text encoding (default: utf-8)')

    parser.add_option('-u', '--upper-is-rtl',
                      dest='upper_is_rtl',
                      default=False,
                      action='store_true',
                      help="Treat upper case chars as strong 'R' "
                        'for debugging (default: False).')

    parser.add_option('-d', '--debug',
                      dest='debug',
                      default=False,
                      action='store_true',
                      help="Display the steps taken with the algorithm")

    parser.add_option('-b', '--base-dir',
                      dest='base_dir',
                      default=None,
                      type='string',
                      help="Override base direction [L|R]")

    options, rest = parser.parse_args()

    if options.base_dir and options.base_dir not in 'LR':
        parser.error('option -b can be L or R')

    # allow unicode in sys.stdout.write
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)

    if rest:
        lines = rest
    else:
        lines = sys.stdin

    for line in lines:
        display = get_display(line, options.encoding, options.upper_is_rtl,
                              options.base_dir, options.debug)
        # adjust the encoding as unicode, to match the output encoding
        if not isinstance(display, unicode):
            display = display.decode(options.encoding)

        sys.stdout.write(display)
