"""Sample codes of yaslha, serves also as test codes.

This example contains how to handle DECAY blocks.
"""

import logging
import unittest

from nose.tools import assert_raises, eq_, ok_, raises  # noqa: F401

from yaslha.parser import SLHAParser

logger = logging.getLogger("test_info")


class TestExampleDecayBlocks(unittest.TestCase):
    """Usage of DECAY blocks."""

    slha_string = """
Block SPINFO         # Program information
     1   SOFTSUSY    # spectrum calculator
     2   1.8.4       # version number
Block DCINFO          # Program information
     1    SDECAY       # Decay package
     2    1.0          # version number
Block gauge Q= 4.64649125e+02
     1     3.60872342e-01   # g'(Q)MSSM drbar
     2     6.46479280e-01   # g(Q)MSSM drbar
     3     1.09623002e+00   # g3(Q)MSSM drbar

#         PDG           Width
DECAY   1000023     1.95831641E-02   # chi_20
#    BR                NDA      ID1      ID2
     3.38444885E-02    2    -2000011        11   # BR(chi_20 -> ~e_R+ e- )
     3.38444885E-02    2     2000011       -11   # BR(chi_20 -> ~e_R- e+ )
     3.50457690E-02    2    -2000013        13   # BR(chi_20 -> ~mu_R+ mu- )
     3.50457690E-02    2     2000013       -13   # BR(chi_20 -> ~mu_R- mu+ )
     4.29284412E-01    2    -1000015        15   # BR(chi_20 -> ~tau_1+ tau- )
     4.29284412E-01    2     1000015       -15   # BR(chi_20 -> ~tau_1- tau+ )
     2.07507330E-06    2     1000022        22   # BR(chi_20 -> chi_10 photon )
#    BR                NDA      ID1      ID2       ID3
     1.75499602E-04    3     1000022         2        -2   # BR(chi_20 -> chi_10 u u )
     1.75229451E-04    3     1000022         4        -4   # BR(chi_20 -> chi_10 c c )
     2.33949042E-04    3     1000022         1        -1   # BR(chi_20 -> chi_10 d d )

DECAY   999     1.00E-02    # data for testing
     0.10    2    123      4                 # 0.0010
     0.15    2    123      5                 # 0.0015
     0.30    2    123   -123                 # 0.0030
     0.40    3    123    123    123          # 0.0040
     0.05    4      1      2      3      4   # 0.0005
"""

    def setUp(self):
        parser = SLHAParser()
        self.slha = parser.parse(self.slha_string)

    def test_read(self):
        # One can read decay blocks by the pid.
        n2_decay = self.slha[1000023]

        eq_(n2_decay.width, 1.95831641e-2)  # total width
        eq_(n2_decay.br(-2000011, 11), 3.38444885e-02)
        eq_(n2_decay.br(11, -2000011), 3.38444885e-02)  # order is irrelevant

        expected_partial_width = 1.95831641e-2 * 3.38444885e-2
        eq_(n2_decay.partial_width(11, -2000011), expected_partial_width)

    def test_iterator_read(self):
        # decay block as an iterator
        for _key in self.slha[1000023]:
            pass

        for i, key in enumerate(self.slha[999].keys()):
            if i == 0:
                eq_(sorted(key), [4, 123])
            elif i == 1:
                eq_(sorted(key), [5, 123])
            elif i == 2:
                eq_(sorted(key), [-123, 123])
            elif i == 3:
                eq_(sorted(key), [123, 123, 123])
            else:
                eq_(sorted(key), [1, 2, 3, 4])

        for i, key in enumerate(self.slha[999].keys(sort=True)):
            # the keys are sorted by the branding ratio descending.
            if i == 0:
                eq_(sorted(key), [123, 123, 123])
            elif i == 1:
                eq_(sorted(key), [-123, 123])
            elif i == 2:
                eq_(sorted(key), [5, 123])
            elif i == 3:
                eq_(sorted(key), [4, 123])
            else:
                eq_(sorted(key), [1, 2, 3, 4])

        # branching ratio iterator
        for key, value in self.slha[999].items_br():
            eq_(value, self.slha[999].br(*key))

        # partial width iterator
        for key, value in self.slha[999].items_partial_width():
            eq_(value, self.slha[999].partial_width(*key))

    def test_update_and_remove(self):
        # modification is made through partial width, not by BRs.
        decay = self.slha[999]
        decay.set_partial_width(123, 4, 0.005)

        eq_(decay.partial_width(123, 4), 0.005)
        eq_(decay.width, 0.014)
        eq_(decay.br(123, 4), 0.005 / 0.014)

        self.slha[999].set_partial_width(123, 123, 0.006)
        eq_(self.slha[999].width, 0.020)
        eq_(self.slha[999].br(123, 123), 0.006 / 0.020)
        eq_(decay.br(123, 4), 0.005 / 0.020)

        self.slha[999].remove(123, 123)
        decay.remove(4, 3, 2, 1)
        decay.remove(5, 123)
        eq_(self.slha[999].width, 0.012)
        eq_(decay.br(123, -123), 0.003 / 0.012)
        # cspell:ignore softsusy sdecay mssm drbar
