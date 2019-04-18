"""Sample codes of yaslha, serves also as test codes.

This example contains simple read/write of SLHA data.
"""

import logging
import unittest

from nose.tools import assert_raises, eq_, ok_, raises  # noqa: F401

from yaslha.parser import SLHAParser

logger = logging.getLogger("test_info")


class TestExampleAdvanced(unittest.TestCase):
    """Simple read/write of SLHA data."""

    slha_string = """
# SUSY Les Houches Accord 1.0 - example spectrum file
# Info from spectrum calculator
Block SPINFO         # Program information
     1   SOFTSUSY    # spectrum calculator
     2   1.8.4       # version number
# Input parameters
Block MODSEL  # Select model
     1    1   # sugra
Block MINPAR  # SUSY breaking input parameters
     3    1.00000000e+01   # tanb(MZ) MSSM drbar
     2    2.50000000e+02   # m12(MGUT) MSSM drbar
     4    1.00000000e+00   # sign(mu(MGUT)) MSSM drbar
     1    1.00000000e+02   # m0(MGUT) MSSM drbar
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

    def test_get(self):
        # default accessor raises KeyError if missing
        with assert_raises(KeyError):
            self.slha["Ad"][1, 1]
        with assert_raises(KeyError):
            self.slha["Ad", 1, 1]

        # get method allows to use default values
        eq_(self.slha["Ad"].get(3, 3, default=0), -7.97992485e02)
        eq_(self.slha["Ad"].get(2, 2, default=-123.456), -123.456)
        eq_(self.slha["Ad"].get(1, 1, default=None), None)

        eq_(self.slha.get("Au", 3, 3, default=0), -5.04995511e02)
        eq_(self.slha.get("Au", 2, 2, default=-1.0), -1.0)
        eq_(self.slha.get("Ad", 1, 1, default="NOTFOUND"), "NOTFOUND")

    def test_iterator_within_a_block(self):
        # block works as an iterator
        for key in self.slha["hmix"]:
            ok_(key in [1, 2, 3, 4])

        minpar_keys = list(self.slha["minpar"])
        eq_(minpar_keys, [3, 2, 4, 1, 5])  # order is saved

        alpha_keys = list(self.slha["alpha"])
        eq_(alpha_keys, [None])  # no-param line has None as a spurious key

        stopmix_keys = list(self.slha["stopmix"])
        eq_(stopmix_keys, [(1, 1), (1, 2), (2, 1), (2, 2)])  # multi-param as tuples

        # one can explicitly call Block.keys() method.
        eq_(list(self.slha["hmix"]), [1, 2, 3, 4])
        eq_(list(self.slha["hmix"].keys()), [1, 2, 3, 4])

        for k, v in self.slha["hmix"].items():
            eq_(v, self.slha["hmix", k])

        for k, v in self.slha["stopmix"].items():
            eq_(v, self.slha["stopmix"][k])
            eq_(v, self.slha["stopmix", k])  # you may notice this syntax is too tricky.

    def test_block_names(self):
        # SLHA.block_names() gives a generator for block names.
        expected_blocks = [
            "spinfo",
            "modsel",
            "minpar",
            "mass",
            "alpha",
            "stopmix",
            "gauge",
            "hmix",
            "au",
            "ad",
        ]
        for block_name in self.slha.blocks.keys():
            ok_(block_name.lower() in expected_blocks)
            expected_blocks.remove(block_name.lower())
        eq_(len(expected_blocks), 0)


# cspell:ignore softsusy modsel sminputs msbar drbar mgut mssm higgs hmix sugra tanb
