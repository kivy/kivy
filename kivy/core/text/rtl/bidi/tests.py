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
"""BiDi algorithm unit tests"""

import unittest
from bidi.algorithm import get_display, get_empty_storage, get_embedding_levels

class TestBidiAlgorithm(unittest.TestCase):
    "Tests the bidi algorithm (based on GNU fribidi ones)"

    def test_surrogate(self):
        """Test for storage and base levels in case of surrogate pairs"""

        storage = get_empty_storage()

        text = u'HELLO \U0001d7f612'
        get_embedding_levels(text, storage, upper_is_rtl=True)

        # should return 9, not 10 even in --with-unicode=ucs2
        self.assertEqual(len(storage['chars']), 9)

        # Is the expected result ? should be EN
        _ch = storage['chars'][6]
        self.assertEqual(_ch['ch'], u'\U0001d7f6')
        self.assertEqual(_ch['type'], 'EN')

        display = get_display(text, upper_is_rtl=True)
        self.assertEqual(display, u'\U0001d7f612 OLLEH')

    def test_implict_with_upper_is_rtl(self):
        '''Implicit tests'''

        tests = (
            (u'car is THE CAR in arabic', u'car is RAC EHT in arabic'),
            (u'CAR IS the car IN ENGLISH', u'HSILGNE NI the car SI RAC'),
            (u'he said "IT IS 123, 456, OK"', u'he said "KO ,456 ,123 SI TI"'),
            (u'he said "IT IS (123, 456), OK"', u'he said "KO ,(456 ,123) SI TI"'),
            (u'he said "IT IS 123,456, OK"', u'he said "KO ,123,456 SI TI"'),
            (u'he said "IT IS (123,456), OK"', u'he said "KO ,(123,456) SI TI"'),
            (u'HE SAID "it is 123, 456, ok"', u'"it is 123, 456, ok" DIAS EH'),
            (u'<H123>shalom</H123>', u'<123H/>shalom<123H>'),
            (u'<h123>SAALAM</h123>', u'<h123>MALAAS</h123>'),
            (u'HE SAID "it is a car!" AND RAN', u'NAR DNA "!it is a car" DIAS EH'),
            (u'HE SAID "it is a car!x" AND RAN', u'NAR DNA "it is a car!x" DIAS EH'),
            (u'SOLVE 1*5 1-5 1/5 1+5', u'1+5 1/5 1-5 5*1 EVLOS'),
            (u'THE RANGE IS 2.5..5', u'5..2.5 SI EGNAR EHT'),
            (u'-2 CELSIUS IS COLD', u'DLOC SI SUISLEC 2-'),
        )

        for storage, display in tests:
            self.assertEqual(get_display(storage, upper_is_rtl=True), display)

    def test_override_base_dir(self):
        """Tests overriding the base paragraph direction"""

        # normaly the display should be :MOLAHS be since we're overriding the
        # base dir the colon should be at the end of the display
        storage = u'SHALOM:'
        display = u'MOLAHS:'

        self.assertEqual(get_display(storage, upper_is_rtl=True, base_dir='L'), display)



    def test_output_encoding(self):
        """Make sure the display is in the same encdoing as the incoming text"""

        storage = '\xf9\xec\xe5\xed'        # Hebrew word shalom in cp1255
        display = '\xed\xe5\xec\xf9'

        self.assertEqual(get_display(storage, encoding='cp1255'), display)


    def test_explicit_with_upper_is_rtl(self):
        """Explicit tests"""
        tests = (
            (u'this is _LJUST_o', u'this is JUST'),
            (u'a _lsimple _RteST_o th_oat', u'a simple TSet that'),
            (u'HAS A _LPDF missing', u'PDF missing A SAH'),
            (u'AnD hOw_L AbOuT, 123,987 tHiS_o', u'w AbOuT, 123,987 tHiSOh DnA'),
            (u'a GOOD - _L_oTEST.', u'a TSET - DOOG.'),
            (u'here_L is_o_o_o _R a good one_o', u'here is eno doog a'),
            (u'THE _rbest _lONE and', u'best ENO and EHT'),
            (u'A REAL BIG_l_o BUG!', u'!GUB GIB LAER A'),
            (u'a _L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_L_Rbug', u'a gub'),
            (u'AN ARABIC _l_o 123-456 NICE ONE!', u'!ENO ECIN 456-123  CIBARA NA'),
            (u'AN ARABIC _l _o 123-456 PAIR', u'RIAP   123-456 CIBARA NA'),
            (u'this bug 67_r_o89 catched!', u'this bug 6789 catched!'),
        )

        # adopt fribidi's CapRtl encoding
        mappings = {
            u'_>': u"\u200E",
            u'_<': u"\u200F",
            u'_l': u"\u202A",
            u'_r': u"\u202B",
            u'_o': u"\u202C",
            u'_L': u"\u202D",
            u'_R': u"\u202E",
            u'__': '_',
        }

        for storage, display in tests:
            for key, val in mappings.items():
                storage = storage.replace(key, val)
            self.assertEqual(get_display(storage, upper_is_rtl=True), display)


if __name__ == '__main__':
    unittest.main()
