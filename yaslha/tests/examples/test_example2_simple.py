"""Sample codes of yaslha, serves also as test codes.

This example contains simple read/write of SLHA data.
"""

import logging
import unittest

from nose.tools import assert_raises, eq_, ok_, raises  # noqa: F401

from yaslha.parser import SLHAParser

logger = logging.getLogger("test_info")


class TestExampleSimple(unittest.TestCase):
    """Simple read/write of SLHA data."""

    slha_string = """
# SUSY Les Houches Accord 1.0 - example spectrum file
# Info from spectrum calculator
Block SPINFO         # Program information
     1   SOFTSUSY    # spectrum calculator
     2   1.8.4       # version number
     3   Error Message 1
     3   Error Message 2
# Input parameters
Block MODSEL  # Select model
     1    1   # sugra
Block MINPAR  # SUSY breaking input parameters
     1    1.00000000e+02   # m0(MGUT) MSSM drbar
     2    2.50000000e+02   # m12(MGUT) MSSM drbar
     3    1.00000000e+01   # tanb(MZ) MSSM drbar
     4    1.00000000e+00   # sign(mu(MGUT)) MSSM drbar
     5   -1.00000000e+02   # A0(MGUT) MSSM drbar
#
# mgut=2.551299875e+16 GeV
Block MASS  # Mass spectrum
# PDG code     mass               particle
   1000001     5.73103437e+02   # ~d_L
   1000002     5.67658152e+02   # ~u_L
   1000003     5.73029886e+02   # ~s_L
   1000004     5.67583798e+02   # ~c_L
   1000005     5.15617364e+02   # ~b_1
   1000006     3.96457239e+02   # ~t_1
# Higgs mixing
Block alpha   # Effective Higgs mixing parameter
          -1.13716828e-01   # alpha
Block stopmix  # stop mixing matrix
  1  1     5.37975095e-01   # O_{11}
  1  2     8.42960733e-01   # O_{12}
  2  1     8.42960733e-01   # O_{21}
  2  2    -5.37975095e-01   # O_{22}
Block gauge Q= 4.64649125e+02
     1     3.60872342e-01   # g'(Q)MSSM drbar
     2     6.46479280e-01   # g(Q)MSSM drbar
     3     1.09623002e+00   # g3(Q)MSSM drbar
Block hmix Q= 4.64649125e+02  # Higgs mixing parameters
     1     3.58660361e+02   # mu(Q)MSSM drbar
     2     9.75139550e+00   # tan beta(Q)MSSM drbar
     3     2.44923506e+02   # higgs vev(Q)MSSM drbar
     4     1.69697051e+04   # [m3^2/cosB sinB](Q)MSSM drbar
Block au Q= 4.64649125e+02
  3  3    -5.04995511e+02   # At(Q)MSSM drbar
Block ad Q= 4.64649125e+02
  3  3    -7.97992485e+02   # Ab(Q)MSSM drbar
"""

    def setUp(self):
        parser = SLHAParser()
        self.slha = parser.parse(self.slha_string)

    def test_read_1(self):
        # Reading data of multi-param blocks
        eq_(self.slha["STOPMIX", 1, 1], 5.37975095e-01)
        eq_(self.slha["AU"][3, 3], -5.04995511e02)

        # To read data of no-param block, a dummy parameter None must be used.
        #  (usually "Block ALPHA" is only the case)
        eq_(self.slha["ALPHA", None], -1.13716828e-01)
        eq_(self.slha["ALPHA"][None], -1.13716828e-01)  # this syntax also works

        # reading the "Q" value of a block
        eq_(self.slha["GAUGE"].q, 4.64649125e02)

    def test_update(self):
        self.slha["STOPMIX"][1, 1] = 0.5
        self.slha["AU", 1, 1] = 0.001
        self.slha["ALPHA", None] = 1.0

        eq_(self.slha["STOPMIX", 1, 1], 0.5)
        eq_(self.slha["AU"][1, 1], 0.001)
        eq_(self.slha["ALPHA"][None], 1.0)

        # create new block with multi params
        self.slha["lambda", 1, 2, 3] = 0.01
        eq_(self.slha["LAMBDA", 1, 2, 3], 0.01)

        # the "Q" value
        self.slha["GAUGE"].q = 400.0
        eq_(self.slha["GAUGE"].q, 400.0)

        # Q value can be set to any blocks (even if physically invalid).
        self.slha["MASS"].q = 123.45
        eq_(self.slha["mass"].q, 123.45)

    def test_delete(self):
        # multi-param or no-param
        del self.slha["STOPMIX", 1, 1]
        del self.slha["Alpha"][None]

        with assert_raises(KeyError):
            self.slha["stopmix", 1, 1]

        with assert_raises(KeyError):
            self.slha["Alpha", None]

        # removing Q-value
        self.slha["gauge"].q = None
        eq_(self.slha["gauge"].q, None)

    def test_info_block(self):
        # blocks with names ending with "INFO" is specially treated.
        eq_(self.slha["spinfo"][1], ("SOFTSUSY",))
        eq_(self.slha["spinfo"][2], ("1.8.4",))
        eq_(self.slha["spinfo"][3], ("Error Message 1", "Error Message 2"))

        # all the contents must be a list of string.
        self.slha["dcinfo", 1] = ["DecayProgramName"]

        with assert_raises(TypeError):
            self.slha["dcinfo", 2] = 1.0

        self.slha["dcinfo", 3] = ["Error message."]
        self.slha["dcinfo", 4] = ["Warning 1", "Warning 2"]

        eq_(self.slha["DCINFO"][3], ("Error message.",))
        ok_(self.slha["DCINFO"][4], ("Warning 1", "Warning 2"))

        # append a value
        self.slha["dcinfo"].append(4, "Warning 3")

        eq_(len(self.slha["dcinfo"][4]), 3)


# cspell:ignore softsusy modsel sminputs msbar drbar mgut mssm higgs hmix sugra tanb
