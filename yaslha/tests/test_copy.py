"""Test for copy.deepcopy applied to SLHA object."""

import copy
import logging
import unittest

from pytest import approx

from yaslha.parser import SLHAParser

logger = logging.getLogger("test_info")


class TestCopy(unittest.TestCase):
    """Copy operation of SLHA data."""

    slha_string = """
Block SPINFO         # Program information
     1   SOFTSUSY    # spectrum calculator
     2   1.8.4       # version number
Block MODSEL  # Select model
     1    1   # sugra
Block alpha   # Effective Higgs mixing parameter
          -1.13716828e-01   # alpha
Block gauge Q= 4.64649125e+02
     1     3.60872342e-01   # g'(Q)MSSM drbar
     2     6.46479280e-01   # g(Q)MSSM drbar
     3     1.09623002e+00   # g3(Q)MSSM drbar
Block au Q= 4.64649125e+02
  3  3    -5.04995511e+02   # At(Q)MSSM drbar

DECAY   1000023     1.95831641E-02   # chi_20
     5.00000000E-01    2    -2000011        11
     4.00000000E-01    2    -2000013        13
     1.00000000E-01    3     1000022         1        -1

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

    def test_copy(self):
        assert self.slha["au", 3, 3] == -5.04995511e02
        assert self.slha["spinfo", 2] == ("1.8.4",)
        assert self.slha[999].partial_width(123, 123, 123) == approx(0.40 * 0.01)

        c = copy.copy(self.slha)

        assert c["au", 3, 3] == -5.04995511e02
        assert c["spinfo", 2] == ("1.8.4",)
        assert c[999].br(123, 123, 123) == 0.40

        c["au", 3, 3] = 1
        c["spinfo"].append(2, "another line")
        c[999].set_partial_width(123, 123, 123, 0.0)

        assert c["au", 3, 3] == 1
        assert c["spinfo", 2] == ("1.8.4", "another line")
        assert c[999].partial_width(123, 123, 123) == 0
        assert c[999].width == 0.006

        assert self.slha["au", 3, 3] == 1
        assert self.slha["spinfo", 2] == ("1.8.4", "another line")
        assert self.slha[999].partial_width(123, 123, 123) == 0
        assert self.slha[999].width == 0.006

    def test_deepcopy(self):
        assert self.slha["au", 3, 3] == -5.04995511e02
        assert self.slha["spinfo", 2] == ("1.8.4",)
        assert self.slha[999].partial_width(123, 123, 123) == 0.40 * 0.01

        c = copy.deepcopy(self.slha)

        assert c["au", 3, 3] == -5.04995511e02
        assert c["spinfo", 2] == ("1.8.4",)
        assert c[999].br(123, 123, 123) == 0.40

        c["au", 3, 3] = 1
        c["spinfo"].append(2, "another line")
        c[999].set_partial_width(123, 123, 123, 0.0)

        assert c["au", 3, 3] == 1
        assert c["spinfo", 2] == ("1.8.4", "another line")
        assert c[999].partial_width(123, 123, 123) == 0
        assert c[999].width == 0.006

        assert self.slha["au", 3, 3] == -5.04995511e02
        assert self.slha["spinfo", 2] == ("1.8.4",)
        assert self.slha[999].partial_width(123, 123, 123) == 0.40 * 0.01


# cspell:ignore softsusy modsel sminputs msbar drbar mgut mssm higgs hmix sugra tanb
